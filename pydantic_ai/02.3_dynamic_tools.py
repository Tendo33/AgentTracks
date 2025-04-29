from __future__ import annotations

import os
from typing import Literal

import logfire
from dotenv import load_dotenv
from rich import print

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.tools import Tool, ToolDefinition


def setup_environment():
    """加载环境变量并配置日志"""
    # 'if-token-present' 表示如果没有配置 logfire，不会发送日志信息
    logfire.configure(send_to_logfire="if-token-present")
    load_dotenv()
    return (
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_API_BASE"),
        os.getenv("TAVILY_API_KEY"),
    )


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url, tavily_api_key = setup_environment()
model = create_openai_model(api_key, base_url)


def greet(name: str) -> str:
    return f"hello {name}"


# prepare 函数必须有这两个值
async def prepare_greet(
    ctx: RunContext[Literal["human", "machine"]], tool_def: ToolDefinition
) -> ToolDefinition | None:
    d = f"Name of the {ctx.deps} to greet."
    tool_def.parameters_json_schema["properties"]["name"]["description"] = d
    print(tool_def)
    print("tool def====================================================")
    return tool_def


greet_tool = Tool(greet, prepare=prepare_greet)
test_model = TestModel()

agent = Agent(test_model, tools=[greet_tool], deps_type=Literal["human", "machine"])

result = agent.run_sync("testing", deps="simon")
print(result.data)
print("====================================================")
print(result.all_messages())
print("====================================================")
print(test_model.last_model_request_parameters.function_tools)
