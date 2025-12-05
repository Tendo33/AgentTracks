# -*- coding: utf-8 -*-
"""
Meta Planner agent 类，能够使用规划-执行模式处理复杂任务。
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from agentscope.agent import ReActAgent
from agentscope.formatter import FormatterBase
from agentscope.memory import MemoryBase
from agentscope.message import Msg, TextBlock, ToolResultBlock, ToolUseBlock
from agentscope.model import ChatModelBase
from agentscope.tool import Toolkit, ToolResponse
from planning_tools import (
    PlannerNoteBook,
    RoadmapManager,
    WorkerManager,
    share_tools,
)
from planning_tools.prompt import get_meta_planner_sys_prompt

PlannerStage = Literal["post_reasoning", "post_action", "pre_reasoning"]


class MetaPlanner(ReActAgent):
    """
    元规划 agent，扩展 ReActAgent 并增强规划能力。

    MetaPlanner 设计用于通过结合推理和行动能力来处理复杂的多步骤规划任务。
    子任务将通过动态创建 ReAct 工作器 agent 并为其提供必要的工具来解决。
    """

    def __init__(
        self,
        name: str,
        model: ChatModelBase,
        worker_full_toolkit: Toolkit,
        formatter: FormatterBase,
        memory: MemoryBase,
        toolkit: Toolkit,
        agent_working_dir: str,
        sys_prompt: Optional[str] = None,
        max_iters: int = 10,
        state_saving_dir: Optional[str] = None,
        planner_mode: Literal["disable", "dynamic", "enforced"] = "dynamic",
    ) -> None:
        """
        使用给定参数初始化 MetaPlanner。

        参数：
            name (str):
                此 agent 实例的名称标识符。
            model (ChatModelBase):
                用于推理和响应生成的主要聊天模型。
            worker_full_toolkit (Toolkit):
                工作器 agent 可用的完整工具集。
            formatter (FormatterBase):
                用于将消息格式化为模型 API 提供商格式的格式化器。
            memory (MemoryBase):
                用于存储对话历史和上下文的内存系统。
            toolkit (Toolkit):
                用于管理 agent 可用工具的工具集。
            agent_working_dir (str):
                agent 文件操作的目录。
            sys_prompt (str, optional):
                元规划器的系统提示
            max_iters (int, optional):
                规划迭代的最大次数。默认为 10。
            state_saving_dir (Optional[str], optional):
                保存 agent 状态的目录。默认为 None。
            planner_mode (bool, optional):
                启用规划器模式以解决任务。默认为 True。
        """
        name = "Task-Meta-Planner" if name is None else name
        if sys_prompt is None:
            sys_prompt = (
                "You are a helpful assistant named Task-Meta-Planner."
                "If a given task can not be done easily, then you may need "
                "to use the tool `enter_solving_complicated_task_mode` to "
                "change yourself to a more long-term planning mode."
            )

        # 提前调用 super().__init__() 以初始化 StateModule 属性
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters,
        )

        self.agent_working_dir_root = agent_working_dir  # agent 工作目录根路径
        self.task_dir = self.agent_working_dir_root  # 任务目录
        self.worker_full_toolkit = worker_full_toolkit  # 工作器完整工具集
        self.state_saving_dir = state_saving_dir  # 状态保存目录

        # 如果我们加载了一个轨迹且最后一步是推理，
        # 那么我们需要一个缓冲区来存储推理消息，并在推理后替换此消息
        self.state_loading_reasoning_msg: Optional[Msg] = None

        # 为了调试和状态恢复，我们需要一个标志来指示
        self.planner_mode = planner_mode  # 规划器模式
        self.in_planner_mode = False  # 是否处于规划器模式
        self.register_state("planner_mode")
        self.register_state("in_planner_mode")

        self.planner_notebook = None
        self.roadmap_manager, self.worker_manager = None, None
        if planner_mode in ["dynamic", "enforced"]:
            self.planner_notebook = PlannerNoteBook()  # 创建规划器笔记本
            self.prepare_planner_tools(planner_mode)  # 准备规划器工具
            # 注册规划器笔记本状态
            self.register_state(
                "planner_notebook",
                lambda x: x.model_dump(),
                lambda x: PlannerNoteBook(**x),
            )

        # pre-reply hook（回复前钩子）
        self.register_instance_hook(
            "pre_reply",
            "update_user_input_to_notebook_pre_reply_hook",
            update_user_input_pre_reply_hook,
        )
        # pre-reasoning hook（推理前钩子）
        self.register_instance_hook(
            "pre_reasoning",
            "planner_load_state_pre_reasoning_hook",
            planner_load_state_pre_reasoning_hook,
        )
        self.register_instance_hook(
            "pre_reasoning",
            "planner_compose_reasoning_msg_pre_reasoning_hook",
            planner_compose_reasoning_msg_pre_reasoning_hook,
        )
        # post_reasoning hook（推理后钩子）
        self.register_instance_hook(
            "post_reasoning",
            "planner_load_state_post_reasoning_hook",
            planner_load_state_post_reasoning_hook,
        )
        self.register_instance_hook(
            "post_reasoning",
            "planner_remove_reasoning_msg_post_reasoning_hook",
            planner_remove_reasoning_msg_post_reasoning_hook,
        )
        self.register_instance_hook(
            "post_reasoning",
            "save_state_post_reasoning_hook",
            planner_save_post_reasoning_state,
        )
        # post_action_hook（行动后钩子）
        self.register_instance_hook(
            "post_acting",
            "save_state_post_action_hook",
            planner_save_post_action_state,
        )

    def prepare_planner_tools(
        self,
        planner_mode: Literal["disable", "enforced", "dynamic"],
    ) -> None:
        """
        根据选定的模式准备规划工具。
        """
        # 创建路线图管理器
        self.roadmap_manager = RoadmapManager(
            planner_notebook=self.planner_notebook,
        )

        # 创建工作器管理器
        self.worker_manager = WorkerManager(
            worker_model=self.model,
            worker_formatter=self.formatter,
            planner_notebook=self.planner_notebook,
            agent_working_dir=self.task_dir,
            worker_full_toolkit=self.worker_full_toolkit,
        )
        # 清理现有的规划工具组
        self.toolkit.remove_tool_groups("planning")
        # 创建新的规划工具组
        self.toolkit.create_tool_group(
            "planning",
            "Tool group for planning capability",
        )
        # 重新注册规划工具以启用加载正确的信息
        self.toolkit.register_tool_function(
            self.roadmap_manager.decompose_task_and_build_roadmap,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.roadmap_manager.revise_roadmap,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.roadmap_manager.get_next_unfinished_subtask_from_roadmap,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.worker_manager.show_current_worker_pool,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.worker_manager.create_worker,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.worker_manager.execute_worker,
            group_name="planning",
        )

        if planner_mode == "dynamic":
            # 如果还没有注册，注册进入复杂任务解决模式的工具
            if "enter_solving_complicated_task_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_solving_complicated_task_mode,
                )
            # 仅在 agent 决定进入规划-执行模式后才激活
            self.toolkit.update_tool_groups(["planning"], False)
        elif planner_mode == "enforced":
            # 强制模式：直接激活规划工具组
            self.toolkit.update_tool_groups(["planning"], True)
            # 使用 self.agent_working_dir 作为工作目录
            self._update_toolkit_and_sys_prompt()

    def _ensure_file_system_functions(self) -> None:
        """确保文件系统功能可用"""
        required_tool_list = [
            "read_file",
            "write_file",
            "edit_file",
            "create_directory",
            "list_directory",
            "directory_tree",
            "list_allowed_directories",
        ]
        # 检查所有必需的工具是否都在工作器工具集中
        for tool_name in required_tool_list:
            if tool_name not in self.worker_full_toolkit.tools:
                raise ValueError(
                    f"{tool_name} must be in the worker toolkit and "
                    "its tool group must be active for complicated.",
                )
        # 将必需的工具共享给规划器工具集
        share_tools(self.worker_full_toolkit, self.toolkit, required_tool_list)

    async def enter_solving_complicated_task_mode(
        self,
        task_name: str,
    ) -> ToolResponse:
        """
        When the user task meets any of the following conditions, enter the
        solving complicated task mode by using this tool.
        1. the task cannot be done within 5 reasoning-acting iterations;
        2. the task cannot be done by the current tools you can see;
        3. the task is related to comprehensive research or information
            gathering

        Args:
            task_name (`str`):
                Given a name to the current task as an indicator. Because
                this name will be used to create a directory, so try to
                use "_" instead of space between words, e.g. "A_NEW_TASK".
        """
        # 为任务构建目录
        self._ensure_file_system_functions()
        self.task_dir = os.path.join(
            self.agent_working_dir_root,
            task_name,
        )
        self.worker_manager.agent_working_dir = self.task_dir

        # 创建任务目录的工具使用块
        create_task_dir = ToolUseBlock(
            type="tool_use",
            id=str(uuid.uuid4()),
            name="create_directory",
            input={
                "path": self.task_dir,
            },
        )
        # 调用工具函数创建目录
        tool_res = await self.toolkit.call_tool_function(create_task_dir)
        # 构造工具结果消息
        tool_res_msg = Msg(
            "system",
            content=[
                ToolResultBlock(
                    type="tool_result",
                    output=[],
                    name="create_directory",
                    id=create_task_dir["id"],
                ),
            ],
            role="system",
        )
        # 将流式结果转换为工具结果块
        async for chunk in tool_res:
            tool_res_msg.content[0]["output"] = chunk.content
        await self.print(tool_res_msg)

        # 更新工具集和系统提示
        self._update_toolkit_and_sys_prompt()
        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Successfully enter the planning-execution mode to "
                        "solve complicated task. "
                        "All the file operations, including"
                        "read/write/modification, should be done in directory "
                        f"{self.task_dir}"
                    ),
                ),
            ],
        )

    def _update_toolkit_and_sys_prompt(self) -> None:
        """更新工具集和系统提示以解决复杂任务"""
        # 获取工作器完整工具列表
        full_worker_tool_list = [
            {
                "tool_name": func_dict.get("function", {}).get("name", ""),
                "description": func_dict.get("function", {}).get(
                    "description",
                    "",
                ),
            }
            for func_dict in self.worker_full_toolkit.get_json_schemas()
        ]
        self.planner_notebook.full_tool_list = full_worker_tool_list

        # 准备工具列表用于系统提示
        tool_list = {
            "tool_list": json.dumps(
                full_worker_tool_list,
                ensure_ascii=False,
            ),
        }
        # 获取元规划器系统提示
        sys_prompt = get_meta_planner_sys_prompt(tool_list)

        self._sys_prompt = sys_prompt  # pylint: disable=W0201
        # 激活规划工具组
        self.toolkit.update_tool_groups(["planning"], True)
        self.in_planner_mode = True

    def resume_planner_tools(self) -> None:
        """恢复规划器笔记本的工具"""
        self.prepare_planner_tools(self.planner_mode)
        if self.in_planner_mode:
            self._update_toolkit_and_sys_prompt()


def _infer_planner_stage_with_msg(
    cur_msg: Msg,
) -> tuple[PlannerStage, list[str]]:
    """
    从消息中推断规划器阶段并提取工具名称。

    分析消息以确定规划器工作流的当前阶段，
    如果消息中存在工具调用，则提取任何工具名称。

    参数：
        cur_msg (Msg): 要分析以进行阶段推断的消息。

    返回：
        tuple[PlannerStage, list[str]]: 包含以下内容的元组：
            - PlannerStage: "pre_reasoning"、"post_reasoning" 或 "post_action" 之一
            - list[str]: 在 tool_use 或 tool_result 块中找到的工具名称列表

    注意：
        - "pre_reasoning": 带有字符串内容的系统角色消息
        - "post_reasoning": 带有 tool_use 块或纯文本内容的消息
        - "post_action": 带有 tool_result 块的消息
        - 工具名称从 tool_use 和 tool_result 块中提取
    """
    blocks = cur_msg.content
    if isinstance(blocks, str) and cur_msg.role in ["system", "user"]:
        return "pre_reasoning", []

    # 提取工具名称
    cur_tool_names = [
        str(b.get("name", "no_name_tool"))
        for b in blocks
        if b["type"] in ["tool_use", "tool_result"]
    ]
    # 根据内容块类型确定阶段
    if cur_msg.has_content_blocks("tool_result"):
        return "post_action", cur_tool_names
    elif cur_msg.has_content_blocks("tool_use"):
        return "post_reasoning", cur_tool_names
    else:
        return "post_reasoning", cur_tool_names


def update_user_input_pre_reply_hook(
    self: "MetaPlanner",
    kwargs: dict[str, Any],
) -> None:
    """将用户输入加载到规划器笔记本的钩子"""
    msg = kwargs.get("msg", None)
    if isinstance(msg, Msg):
        msg = [msg]
    if isinstance(msg, list):
        for m in msg:
            self.planner_notebook.user_input.append(m.content)


def planner_save_post_reasoning_state(
    self: "MetaPlanner",
    reasoning_input: dict[str, Any],  # pylint: disable=W0613
    reasoning_output: Msg,
) -> None:
    """推理步骤后保存状态的钩子函数"""
    if self.state_saving_dir:
        os.makedirs(self.state_saving_dir, exist_ok=True)
        cur_stage, _ = _infer_planner_stage_with_msg(reasoning_output)
        time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(
            self.state_saving_dir,
            f"state-{cur_stage}-{time_str}.json",
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.state_dict(), f, ensure_ascii=False, indent=4)


async def planner_load_state_pre_reasoning_hook(
    self: "MetaPlanner",  # pylint: disable=W0613
    *args: Any,
    **kwargs: Any,
) -> None:
    """推理步骤前加载已保存状态的钩子函数"""
    mem_msgs = await self.memory.get_memory()
    if len(mem_msgs) > 0:
        stage, _ = _infer_planner_stage_with_msg(mem_msgs[-1])
        if stage == "post_reasoning":
            self.state_loading_reasoning_msg = mem_msgs[-1]
            # 删除最后一条推理消息，以避免在推理步骤中调用模型时出错
            await self.memory.delete(len(mem_msgs) - 1)


async def planner_load_state_post_reasoning_hook(
    self: "MetaPlanner",  # pylint: disable=W0613
    *args: Any,
    **kwargs: Any,
) -> Msg:
    """推理步骤后加载已保存状态的钩子函数"""
    if self.state_loading_reasoning_msg is not None:
        num_msgs = await self.memory.size()
        # 用加载的消息替换新生成的推理消息
        await self.memory.delete(num_msgs - 1)
        old_reasoning_msg = self.state_loading_reasoning_msg
        await self.memory.add(old_reasoning_msg)
        self.state_loading_reasoning_msg = None
        return old_reasoning_msg


async def planner_compose_reasoning_msg_pre_reasoning_hook(
    self: "MetaPlanner",  # pylint: disable=W0613
    *args: Any,
    **kwargs: Any,
) -> None:
    """为推理步骤组合消息的钩子函数"""
    reasoning_info = (
        "## All User Input\n{all_user_input}\n\n"
        "## Session Context\n"
        "```json\n{notebook_string}\n```\n\n"
    ).format_map(
        {
            "notebook_string": self.planner_notebook.model_dump_json(
                exclude={"user_input", "full_tool_list"},
                indent=2,
            ),
            "all_user_input": self.planner_notebook.user_input,
        },
    )
    reasoning_msg = Msg(
        "user",
        content=reasoning_info,
        role="user",
    )
    await self.memory.add(reasoning_msg)


async def planner_remove_reasoning_msg_post_reasoning_hook(
    self: "MetaPlanner",  # pylint: disable=W0613
    *args: Any,
    **kwargs: Any,
) -> None:
    """推理步骤后移除消息的钩子函数"""
    num_msgs = await self.memory.size()
    if num_msgs > 1:
        # 移除由 planner_compose_reasoning_pre_reasoning_hook 添加的消息
        await self.memory.delete(num_msgs - 2)


def planner_save_post_action_state(
    self: "MetaPlanner",
    action_input: dict[str, Any],
    tool_output: Optional[Msg],  # pylint: disable=W0613
) -> None:
    """行动步骤后保存状态的钩子函数"""
    if self.state_saving_dir:
        os.makedirs(self.state_saving_dir, exist_ok=True)
        time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(
            self.state_saving_dir,
            "state-post-action-"
            f"{action_input.get('tool_call').get('name')}-{time_str}.json",
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.state_dict(), f, ensure_ascii=False, indent=4)
