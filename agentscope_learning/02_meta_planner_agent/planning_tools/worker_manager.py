# -*- coding: utf-8 -*-
"""
元规划器的协调处理模块
"""

import json
import os
from typing import List, Literal, Optional

from agentscope import logger
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter, FormatterBase
from agentscope.memory import InMemoryMemory, MemoryBase
from agentscope.message import Msg, TextBlock, ToolResultBlock, ToolUseBlock
from agentscope.model import ChatModelBase
from agentscope.module import StateModule
from agentscope.tool import Toolkit, ToolResponse

from .planning_notebook import (
    PlannerNoteBook,
    WorkerInfo,
    WorkerResponse,
)
from .prompt import get_tool_usage_rules, get_worker_additional_sys_prompt


def rebuild_reactworker(
    worker_info: WorkerInfo,
    old_toolkit: Toolkit,
    new_toolkit: Toolkit,
    memory: Optional[MemoryBase] = None,
    model: Optional[ChatModelBase] = None,
    formatter: Optional[FormatterBase] = None,
    exclude_tools: Optional[list[str]] = None,
) -> ReActAgent:
    """
    使用指定的配置和工具重建 ReActAgent 工作器。

    使用工作器信息和工具集配置创建新的 ReActAgent。
    工具从旧工具集共享到新工具集，排除任何指定的工具。

    参数：
        worker_info (WorkerInfo): 有关工作器的信息，包括名称、系统提示和工具列表。
        old_toolkit (Toolkit): 包含可用工具的源工具集。
        new_toolkit (Toolkit): 接收共享工具的目标工具集。
        memory (Optional[MemoryBase], optional): agent 的内存实例。
            如果为 None，则默认为 InMemoryMemory()。
        model (Optional[ChatModelBase], optional): 聊天模型实例。
            如果为 None，则默认为使用 gpt-4o-mini 的 OpenAIChatModel。
        formatter (Optional[FormatterBase], optional): 消息格式化器。
            如果为 None，则默认为 OpenAIChatFormatter()。
        exclude_tools (Optional[list[str]], optional): 要从共享中排除的工具名称列表。
            如果为 None，则默认为空列表。

    返回：
        ReActAgent: 配置好的 ReActAgent 实例，可以使用。

    注意：
        - 默认模型使用 OPENAI_API_KEY 环境变量
        - 工具基于 worker_info.tool_lists 减去排除的工具进行共享
        - agent 配置为启用思考和流式支持
    """
    if exclude_tools is None:
        exclude_tools = []
    # 构建工具列表，排除指定的工具
    tool_list = [
        tool_name
        for tool_name in worker_info.tool_lists
        if tool_name not in exclude_tools
    ]
    # 将工具从旧工具集共享到新工具集
    share_tools(old_toolkit, new_toolkit, tool_list)
    # 尝试从配置中获取最大迭代次数
    try:
        from config import config as agent_config

        max_iters = agent_config.agent_worker_max_iters
    except ImportError:
        max_iters = int(os.environ.get("AGENT_WORKER_MAX_ITERS", "20"))

    # 创建并返回 ReActAgent
    return ReActAgent(
        name=worker_info.worker_name,
        sys_prompt=worker_info.sys_prompt,
        model=model,
        formatter=formatter if formatter else DashScopeChatFormatter(),
        toolkit=new_toolkit,
        memory=InMemoryMemory() if memory is None else memory,
        max_iters=max_iters,
    )


async def check_file_existence(file_path: str, toolkit: Toolkit) -> bool:
    """
    使用提供的工具集中的 read_file 工具检查文件是否存在。

    此函数尝试通过调用 read_file 工具并检查响应中的错误指示符来验证文件是否存在。
    它要求工具集具有可用的 'read_file' 工具。

    参数：
        file_path (str): 要检查是否存在的文件路径。
        toolkit (Toolkit): 包含 read_file 工具的工具集。

    返回：
        bool: 如果文件存在且可读，则为 True，否则为 False。

    注意：
        - 如果工具集中没有 'read_file' 工具，则返回 False
        - 如果在文件读取尝试期间发生任何异常，则返回 False
        - 使用错误消息检测（"no such file or directory"）来确定是否存在
    """
    if "read_file" in toolkit.tools:
        params = {
            "path": file_path,
        }
        read_file_block = ToolUseBlock(
            type="tool_use",
            id="manual_check_file_existence",
            name="read_file",
            input=params,
        )
        try:
            tool_res = await toolkit.call_tool_function(read_file_block)
            tool_res_msg = Msg(
                "system",
                [
                    ToolResultBlock(
                        type="tool_result",
                        id="",
                        name="read_file",
                        output=[],
                    ),
                ],
                "system",
            )
            async for chunk in tool_res:
                # Turn into a tool result block
                tool_res_msg.content[0][  # type: ignore[index]
                    "output"
                ] = chunk.content
            if "no such file or directory" in str(tool_res_msg.content):
                return False
            else:
                return True
        except Exception as _:  # noqa: F841
            return False

    else:
        return False


def share_tools(
    old_toolkit: Toolkit,
    new_toolkit: Toolkit,
    tool_list: list[str],
) -> None:
    """
    将指定的工具从旧工具集共享到新工具集。

    此函数根据提供的工具列表将工具从一个工具集复制到另一个工具集。
    如果工具在旧工具集中不存在，则记录警告。

    参数：
        old_toolkit (Toolkit):
            包含要共享的工具的源工具集。
        new_toolkit (Toolkit):
            接收工具的目标工具集。
        tool_list (list[str]):
            要从旧工具集复制到新工具集的工具名称列表。

    返回：
        None

    注意：
        此函数就地修改 new_toolkit。
        如果在 old_toolkit 中找不到 tool_list 中的工具，
        则记录警告但继续执行。
    """
    for tool in tool_list:
        if tool in old_toolkit.tools and tool not in new_toolkit.tools:
            new_toolkit.tools[tool] = old_toolkit.tools[tool]
        else:
            logger.warning(
                "提供的 worker_tool_toolkit 中没有工具 %s",
                tool,
            )


class WorkerManager(StateModule):
    """
    处理元规划器和工作器 agent 之间的协调。

    此类管理工作器 agent 的创建、选择和执行，以完成路线图中的子任务。
    它提供动态工作器创建、基于任务需求的工作器选择以及
    处理工作器响应以更新整体任务进度的功能。
    """

    def __init__(
        self,
        worker_model: ChatModelBase,
        worker_formatter: FormatterBase,
        planner_notebook: PlannerNoteBook,
        worker_full_toolkit: Toolkit,
        agent_working_dir: str,
        worker_pool: Optional[dict[str, tuple[WorkerInfo, ReActAgent]]] = None,
    ):
        """初始化 CoordinationHandler。
        参数：
            worker_model (ChatModelBase):
                用于协调决策的主要语言模型
            worker_formatter (FormatterBase):
                用于模型通信的消息格式化器
            planner_notebook (PlannerNoteBook):
                包含路线图和文件信息的笔记本
            worker_full_toolkit (Toolkit):
                工作器可用的完整工具集
            agent_working_dir (str):
                agent 操作的工作目录
            worker_pool: dict[str, tuple[WorkerInfo, ReActAgent]]:
                已创建的工作器
        """
        super().__init__()
        self.planner_notebook = planner_notebook
        self.worker_model = worker_model
        self.worker_formatter = worker_formatter
        self.worker_pool: dict[str, tuple[WorkerInfo, ReActAgent]] = (
            worker_pool if worker_pool else {}
        )
        self.agent_working_dir = agent_working_dir
        self.worker_full_toolkit = worker_full_toolkit

        def reconstruct_workerpool(worker_pool_dict: dict) -> dict:
            """重建工作器池的辅助函数"""
            rebuild_worker_pool = {}
            for k, v in worker_pool_dict.items():
                worker_info = WorkerInfo(**v)
                rebuild_worker_pool[k] = (
                    worker_info,
                    rebuild_reactworker(
                        worker_info=worker_info,
                        old_toolkit=self.worker_full_toolkit,
                        new_toolkit=Toolkit(),
                        model=self.worker_model,
                        formatter=self.worker_formatter,
                        exclude_tools=["generate_response"],
                    ),
                )
            return rebuild_worker_pool

        # 注册工作器池状态
        self.register_state(
            "worker_pool",
            lambda x: {k: v[0].model_dump() for k, v in x.items()},
            custom_from_json=reconstruct_workerpool,
        )

    def _register_worker(
        self,
        agent: ReActAgent,
        description: Optional[str] = None,
        worker_type: Literal["built-in", "dynamic-built"] = "dynamic",
    ) -> None:
        """
        在工作器池中注册工作器 agent。

        将工作器 agent 添加到可用池中，并带有适当的元数据。
        必要时通过附加版本号来处理名称冲突。

        参数：
            agent (ReActAgent):
                要注册的工作器 agent
            description (Optional[str]):
                工作器能力的描述
            worker_type (Literal["built-in", "dynamic-built"]):
                工作器 agent 的类型
        """
        worker_info = WorkerInfo(
            worker_name=agent.name,
            description=description,
            worker_type=worker_type,
            status="ready-to-work",
        )
        if worker_type == "dynamic-built":
            worker_info.sys_prompt = agent.sys_prompt
            worker_info.tool_lists = list(agent.toolkit.tools.keys())

        # 处理名称冲突
        if agent.name in self.worker_pool:
            name = agent.name
            version = 1
            while name in self.worker_pool:
                name = agent.name + f"_v{version}"
                version += 1
            agent.name, worker_info.worker_name = name, name
            self.worker_pool[name] = (worker_info, agent)
        else:
            self.worker_pool[agent.name] = (worker_info, agent)

    @staticmethod
    def _no_more_subtask_return() -> ToolResponse:
        """
        当不存在更多未完成的子任务时返回响应。

        返回：
            ToolResponse: 指示没有更多可用子任务的响应
        """
        return ToolResponse(
            metadata={"success": False},
            content=[
                TextBlock(
                    type="text",
                    text="No more subtask exists. "
                    "Check whether the task is "
                    "completed solved.",
                ),
            ],
        )

    async def create_worker(
        self,
        worker_name: str,
        worker_system_prompt: str,
        tool_names: Optional[List[str]] = None,
        agent_description: str = "",
    ) -> ToolResponse:
        """
        Create a worker agent for the next unfinished subtask.

        Dynamically creates a specialized worker agent based on the
        requirements of the next unfinished subtask in the roadmap.
        The worker is configured with appropriate tools and system prompts
        based on the task needs.

        Args:
            worker_name (str): The name of the worker agent.
            worker_system_prompt (str): The system prompt for the worker agent.
            tool_names (Optional[List[str]], optional):
                List of tools that should be assigned to the worker agent so
                that it can finish the subtask. MUST be from the
                `Available Tools for workers`
            agent_description (str, optional):
                A brief description of the worker's capabilities.

        Returns:
            ToolResponse: Response containing the creation result and worker
                details
        """
        if tool_names is None:
            tool_names = []
        worker_toolkit = Toolkit()
        share_tools(
            self.worker_full_toolkit,
            worker_toolkit,
            tool_names
            + [
                "read_file",
                "write_file",
                "edit_file",
                "search_files",
                "list_directory",
            ],
        )

        additional_worker_prompt = get_worker_additional_sys_prompt()

        tool_usage_rules = get_tool_usage_rules(self.agent_working_dir)

        worker = ReActAgent(
            name=worker_name,
            sys_prompt=(
                worker_system_prompt + additional_worker_prompt + tool_usage_rules
            ),
            model=self.worker_model,
            formatter=self.worker_formatter,
            memory=InMemoryMemory(),
            toolkit=worker_toolkit,
        )

        self._register_worker(
            worker,
            description=agent_description,
            worker_type="dynamic-built",
        )

        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Successfully created a worker agent:\n"
                        f"Worker name: {worker_name}"
                        f"Worker tools: {tool_names}"
                        f"Worker system prompt: {worker.sys_prompt}"
                    ),
                ),
            ],
        )

    async def show_current_worker_pool(self) -> ToolResponse:
        """
        List all currently available worker agents with
        their system prompts and tools.
        """
        worker_info: dict[str, dict] = {
            name: info.model_dump() for name, (info, _) in self.worker_pool.items()
        }
        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(worker_info, ensure_ascii=False, indent=2),
                ),
            ],
        )

    async def execute_worker(
        self,
        subtask_idx: int,
        selected_worker_name: str,
        detailed_instruction: str,
    ) -> ToolResponse:
        """
        Execute a worker agent for the next unfinished subtask.

        Args:
            subtask_idx (int):
                Index of the subtask to execute.
            selected_worker_name (str):
                Select a worker agent to execute by its name. If you are unsure
                what are the available agents, call `show_current_worker_pool`
                before using this function.
            detailed_instruction (str):
                Generate detailed instruction for the worker based on the
                next unfinished subtask in the roadmap. If you are unsure
                what is the next unavailable subtask, check with
                `get_next_unfinished_subtask_from_roadmap` to get more info.
        """
        if selected_worker_name not in self.worker_pool:
            worker_info: dict[str, WorkerInfo] = {
                name: info for name, (info, _) in self.worker_pool.items()
            }
            current_agent_pool = json.dumps(
                worker_info,
                ensure_ascii=False,
                indent=2,
            )
            return ToolResponse(
                metadata={"success": False},
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"There is no {selected_worker_name} in current"
                            "agent pool."
                            "Current agent pool:\n```json"
                            f"{current_agent_pool}\n"
                            "```"
                        ),
                    ),
                ],
            )

        worker = self.worker_pool[selected_worker_name][1]
        question_msg = Msg(
            role="user",
            name="user",
            content=detailed_instruction,
        )
        worker_response_msg = await worker(
            question_msg,
            structured_model=WorkerResponse,
        )
        if worker_response_msg.metadata is not None:
            worker_response = WorkerResponse(
                **worker_response_msg.metadata,
            )
            self.planner_notebook.roadmap.decomposed_tasks[subtask_idx].workers.append(
                self.worker_pool[selected_worker_name][0],
            )
            # double-check to ensure the generated files exists
            for filepath, desc in worker_response.generated_files.items():
                if await check_file_existence(
                    filepath,
                    self.worker_full_toolkit,
                ):
                    self.planner_notebook.files[filepath] = desc
                else:
                    worker_response.generated_files.pop(filepath)

            return ToolResponse(
                metadata={
                    "success": True,
                    "worker_response": worker_response.model_dump_json(),
                },
                content=[
                    TextBlock(
                        type="text",
                        text=worker_response.model_dump_json(),
                    ),
                ],
            )
        else:
            return ToolResponse(
                metadata={
                    "success": False,
                    "worker_response": worker_response_msg.content,
                },
                content=[
                    TextBlock(
                        type="text",
                        text=str(worker_response_msg.content),
                    ),
                ],
            )
