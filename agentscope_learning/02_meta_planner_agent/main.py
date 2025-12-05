# -*- coding: utf-8 -*-
"""Meta-planner agent 示例的主入口程序

本模块为 MetaPlanner agent 提供会话式交互界面。
MetaPlanner 设计用于通过规划-执行模式处理复杂任务。
该 agent 可以将复杂请求分解为可管理的步骤，并使用各种工具和 MCP（Model Context Protocol）客户端执行。

本脚本的关键功能包括：
- 设置 MCP 客户端以进行外部工具集成（Tavily 搜索、文件系统）
- 为规划器和工作器 agent 配置工具集
- 管理 agent 状态持久化和恢复
- 提供交互式聊天界面

示例：
    交互式运行 agent：
        $ python main.py

    从之前的状态加载：
        $ python main.py --load_state ./agent-states/run-xxxx/state-xxx.json

必需的环境变量：
    ANTHROPIC_API_KEY: Anthropic Claude 模型的 API 密钥
    TAVILY_API_KEY: Tavily 搜索功能的 API 密钥

可选的环境变量：
    AGENT_OPERATION_DIR: agent 操作的自定义工作目录
"""

import argparse
import asyncio
import json
import os
from datetime import datetime

from agentscope import logger
from agentscope.agent import UserAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.mcp import StatefulClientBase, StdIOStatefulClient
from agentscope.memory import InMemoryMemory
from agentscope.message import ToolUseBlock
from agentscope.model import OpenAIChatModel
from agentscope.tool import (
    Toolkit,
    ToolResponse,
    execute_shell_command,
    view_text_file,
)
from config import config
from meta_planner import MetaPlanner
from planning_tools.logfire_utils import configure_logfire

# 如果启用了 logfire，则进行配置
if config.enable_logfire:
    configure_logfire()


def chunking_too_long_tool_response(
    tool_use: ToolUseBlock,  # pylint: disable=W0613
    tool_response: ToolResponse,
) -> ToolResponse:
    """对工具响应进行后处理，防止内容溢出

    此函数确保工具响应不会超过预定义的预算，
    以防止过多的信息淹没模型。它会截断文本内容，同时保留响应的结构。

    参数：
        tool_use: 触发响应的工具使用块（未使用）
        tool_response: 可能需要截断的工具响应

    注意：
        预算通过 TOOL_RESPONSE_BUDGET 环境变量配置，
        以确保响应对语言模型保持可管理的大小。
    """
    # 设置预算以防止用过多内容淹没模型
    budget = config.tool_response_budget

    for i, block in enumerate(tool_response.content):
        if block["type"] == "text":
            text = block["text"]
            text_len = len(text)

            # 如果预算已耗尽，截断剩余的块
            if budget <= 0:
                tool_response.content = tool_response.content[:i]
                break

            # 如果此块超过剩余预算，则截断它
            if text_len > budget:
                # 计算截断阈值（比例预算的 80%）
                threshold = int(budget / text_len * len(text) * 0.8)
                tool_response.content[i]["text"] = text[:threshold]

            budget -= text_len

    return tool_response


def _add_tool_postprocessing_func(worker_toolkit: Toolkit) -> None:
    """为工作器工具集中的特定工具添加后处理函数

    此函数对可能返回大量数据的工具应用内容截断，
    特别是 Tavily 搜索工具，以防止淹没语言模型。

    参数：
        worker_toolkit: 包含要修改的工作器工具的工具集
    """
    for tool_func, _ in worker_toolkit.tools.items():
        # 对 Tavily 搜索工具应用截断
        if tool_func.startswith("tavily"):
            worker_toolkit.tools[
                tool_func
            ].postprocess_func = chunking_too_long_tool_response


async def main() -> None:
    """Meta-planner agent 示例的主入口函数"""
    logger.setLevel(config.log_level)
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # 初始化工具集
    planner_toolkit = Toolkit()  # 规划器工具集
    worker_toolkit = Toolkit()  # 工作器工具集
    worker_toolkit.register_tool_function(
        execute_shell_command
    )  # 注册 shell 命令执行工具
    worker_toolkit.register_tool_function(view_text_file)  # 注册文本文件查看工具
    mcp_clients = []  # MCP 客户端列表

    # 设置 Tavily MCP 客户端用于搜索功能
    mcp_clients.append(
        StdIOStatefulClient(
            name="tavily_mcp",
            command=config.mcp_npx_command,
            args=["-y", config.mcp_tavily_package],
            env={"TAVILY_API_KEY": config.tavily_api_key},
        ),
    )

    # 注意：你可以添加更多 MCP/工具来支持更多样化的任务

    # 设置 agent 操作的工作目录
    agent_working_dir = config.get_agent_working_dir()
    os.makedirs(agent_working_dir, exist_ok=True)

    # 设置文件系统 MCP 客户端
    mcp_clients.append(
        StdIOStatefulClient(
            name="file_system_mcp",
            command=config.mcp_npx_command,
            args=[
                "-y",
                config.mcp_filesystem_package,
                agent_working_dir,
            ],
        ),
    )

    try:
        # 单独连接并注册每个 MCP 客户端，带有错误处理
        connected_clients = []
        for mcp_client in mcp_clients:
            try:
                if isinstance(mcp_client, StatefulClientBase):
                    logger.info(f"正在连接 MCP 客户端：{mcp_client.name}")
                    await mcp_client.connect()
                    logger.info(f"成功连接 MCP 客户端：{mcp_client.name}")

                logger.info(f"正在从 MCP 客户端注册工具：{mcp_client.name}")
                await worker_toolkit.register_mcp_client(mcp_client)
                logger.info(f"成功从以下客户端注册工具：{mcp_client.name}")

                connected_clients.append(mcp_client)

            except Exception as e:
                logger.error(
                    f"初始化 MCP 客户端 '{mcp_client.name}' 失败：{e}", exc_info=True
                )
                # 尝试关闭失败的客户端
                try:
                    if isinstance(mcp_client, StatefulClientBase):
                        await mcp_client.close()
                except Exception as close_error:
                    logger.warning(
                        f"关闭失败的 MCP 客户端 '{mcp_client.name}' 时出错：{close_error}"
                    )
                # 继续处理其他客户端，而不是完全失败
                continue

        # 更新 mcp_clients 为仅包含成功连接的客户端
        mcp_clients = connected_clients

        if not mcp_clients:
            logger.warning(
                "没有成功初始化任何 MCP 客户端。Agent 将以有限的工具能力运行。"
            )

        # 为工作器工具集添加后处理函数
        _add_tool_postprocessing_func(worker_toolkit)

        # 创建 MetaPlanner agent
        agent = MetaPlanner(
            name=config.agent_name,
            model=OpenAIChatModel(
                api_key=config.openai_api_key,
                model_name=config.chat_model,
                stream=config.model_stream,
                client_args={"base_url": config.openai_base_url},
                generate_kwargs={
                    "temperature": config.model_temperature,
                    "max_tokens": config.model_max_tokens,
                },
            ),
            formatter=OpenAIChatFormatter(),
            toolkit=planner_toolkit,
            worker_full_toolkit=worker_toolkit,
            agent_working_dir=agent_working_dir,
            memory=InMemoryMemory(),
            state_saving_dir=config.get_state_saving_dir(time_str),
            max_iters=config.agent_max_iters,
            planner_mode=config.planner_mode,
        )
        # 创建用户 agent
        user = UserAgent("Simon")
        msg = None
        skip_user_input = False

        # 如果指定了加载状态，则从状态文件恢复
        if args.load_state:
            state_file_path = args.load_state
            with open(state_file_path, "r", encoding="utf-8") as f:
                state_dict = json.load(f)
            agent.load_state_dict(state_dict)
            agent.resume_planner_tools()
            skip_user_input = True

        # 打印工具集的 JSON schemas（用于调试）
        print(
            json.dumps(planner_toolkit.get_json_schemas(), indent=4, ensure_ascii=False)
        )
        print("====================================================")
        print(
            json.dumps(worker_toolkit.get_json_schemas(), indent=4, ensure_ascii=False)
        )
        print("====================================================")

        # 主交互循环
        while True:
            if skip_user_input:
                skip_user_input = False
            else:
                msg = await user(msg)
                if msg.get_text_content() == "exit":
                    break
            msg = await agent(msg)

    except Exception as e:
        logger.exception(e)
    finally:
        # 单独清理每个 MCP 客户端
        for mcp_client in mcp_clients:
            if isinstance(mcp_client, StatefulClientBase):
                try:
                    logger.info(f"正在关闭 MCP 客户端：{mcp_client.name}")
                    await mcp_client.close()
                    logger.info(f"成功关闭 MCP 客户端：{mcp_client.name}")
                except Exception as cleanup_error:
                    logger.warning(
                        f"清理 MCP 客户端 '{mcp_client.name}' 时出错：{cleanup_error}"
                    )


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="使用指定状态运行 ReAct agent 示例。",
    )
    parser.add_argument(
        "--load_state",
        type=str,
        help="用于加载状态的输入文件名。",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main())
