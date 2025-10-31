# -*- coding: utf-8 -*-
"""Main entry point for the Meta-planner agent example.

This module provides a conversational interface for the MetaPlanner agent,
which is designed to handle complex tasks through a planning-execution pattern.
The agent can break down complex requests into manageable steps and execute
them using various tools and MCP (Model Context Protocol) clients.

The key points in this script includes:
- Setting up MCP clients for external tool integration
    (Tavily search, filesystem)
- Configuring toolkits for both planner and worker agents
- Managing agent state persistence and recovery
- Providing an interactive chat interface

Example:
    Run the agent interactively:
        $ python main.py

    Load from a previous state:
        $ python main.py --load_state ./agent-states/run-xxxx/state-xxx.json

Required Environment Variables:
    ANTHROPIC_API_KEY: API key for Anthropic Claude model
    TAVILY_API_KEY: API key for Tavily search functionality

Optional Environment Variables:
    AGENT_OPERATION_DIR: Custom working directory for agent operations
"""

import argparse
import asyncio
import json
import os
from datetime import datetime

from _meta_planner import MetaPlanner  # pylint: disable=C0411
from config import config  # pylint: disable=C0411

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
from utils.logfire_utils import configure_logfire

# Configure logfire if enabled
if config.enable_logfire:
    configure_logfire()


def chunking_too_long_tool_response(
    tool_use: ToolUseBlock,  # pylint: disable=W0613
    tool_response: ToolResponse,
) -> ToolResponse:
    """Post-process tool responses to prevent content overflow.

    This function ensures that tool responses don't exceed a predefined budget
    to prevent overwhelming the model with too much information. It truncates
    text content while preserving the structure of the response.

    Args:
        tool_use: The tool use block that triggered the response (unused).
        tool_response: The tool response to potentially truncate.

    Note:
        The budget is configured via TOOL_RESPONSE_BUDGET environment variable
        to ensure responses remain manageable for the language model.
    """
    # Set budget to prevent overwhelming the model with too much content
    budget = config.tool_response_budget

    for i, block in enumerate(tool_response.content):
        if block["type"] == "text":
            text = block["text"]
            text_len = len(text)

            # If budget is exhausted, truncate remaining blocks
            if budget <= 0:
                tool_response.content = tool_response.content[:i]
                break

            # If this block exceeds remaining budget, truncate it
            if text_len > budget:
                # Calculate truncation threshold (80% of proportional budget)
                threshold = int(budget / text_len * len(text) * 0.8)
                tool_response.content[i]["text"] = text[:threshold]

            budget -= text_len

    return tool_response


def _add_tool_postprocessing_func(worker_toolkit: Toolkit) -> None:
    """Add postprocessing functions to specific tools in the worker toolkit.

    This function applies content truncation to tools that might return
    large amounts of data, specifically Tavily search tools, to prevent
    overwhelming the language model.

    Args:
        worker_toolkit: The toolkit containing worker tools to modify.
    """
    for tool_func, _ in worker_toolkit.tools.items():
        # Apply truncation to Tavily search tools
        if tool_func.startswith("tavily"):
            worker_toolkit.tools[
                tool_func
            ].postprocess_func = chunking_too_long_tool_response


async def main() -> None:
    """The main entry point for the Meta-planner agent example."""
    logger.setLevel(config.log_level)
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    planner_toolkit = Toolkit()
    worker_toolkit = Toolkit()
    worker_toolkit.register_tool_function(execute_shell_command)
    worker_toolkit.register_tool_function(view_text_file)
    mcp_clients = []

    # Setup Tavily MCP client for search functionality
    mcp_clients.append(
        StdIOStatefulClient(
            name="tavily_mcp",
            command=config.mcp_npx_command,
            args=["-y", config.mcp_tavily_package],
            env={"TAVILY_API_KEY": config.tavily_api_key},
        ),
    )

    # Note: You can add more MCP/tools for more diverse tasks

    # Setup working directory for agent operations
    agent_working_dir = config.get_agent_working_dir()
    os.makedirs(agent_working_dir, exist_ok=True)

    # Setup filesystem MCP client
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
        for mcp_client in mcp_clients:
            if isinstance(mcp_client, StatefulClientBase):
                await mcp_client.connect()
            await worker_toolkit.register_mcp_client(mcp_client)

        _add_tool_postprocessing_func(worker_toolkit)

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
        user = UserAgent("Simon")
        msg = None
        skip_user_input = False
        if args.load_state:
            state_file_path = args.load_state
            with open(state_file_path, "r", encoding="utf-8") as f:
                state_dict = json.load(f)
            agent.load_state_dict(state_dict)
            agent.resume_planner_tools()
            skip_user_input = True

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
        for mcp_client in mcp_clients:
            if isinstance(mcp_client, StatefulClientBase):
                await mcp_client.close()


def parse_args() -> argparse.Namespace:
    """parsing args from command line"""
    parser = argparse.ArgumentParser(
        description="Run the ReAct agent example with a specified state.",
    )
    parser.add_argument(
        "--load_state",
        type=str,
        help="The input file name to load the state from.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main())
