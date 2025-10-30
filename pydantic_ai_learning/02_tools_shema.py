import os

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel
from rich import print

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.openai import OpenAIProvider


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


agent = Agent()


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def foobar(a: int, b: str, c: dict[str, list[float]]) -> str:
    """Get me foobar.

    Args:
        a: apple pie
        b: banana cake
        c: carrot smoothie
    """
    return f"{a} {b} {c}"


def print_schema(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tool = info.function_tools[0]
    print(messages)
    print("====================================================")
    print(tool.description)
    print("====================================================")
    print(tool.parameters_json_schema)
    print("====================================================")
    """
    {
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'apple pie', 'type': 'integer'},
            'b': {'description': 'banana cake', 'type': 'string'},
            'c': {
                'additionalProperties': {'items': {'type': 'number'}, 'type': 'array'},
                'description': 'carrot smoothie',
                'type': 'object',
            },
        },
        'required': ['a', 'b', 'c'],
        'type': 'object',
    }
    """
    return ModelResponse(parts=[TextPart("foobar")])


agent.run_sync("hello", model=FunctionModel(print_schema))


agent2 = Agent()


class Foobar(BaseModel):
    """This is a Foobar"""

    x: int
    y: str
    z: float = 3.14


@agent2.tool_plain
def foobar2(f: Foobar) -> str:
    return str(f)


test_model = TestModel()
result = agent2.run_sync("hello", model=test_model)
print(result.data)
print("====================================================")

print(test_model.last_model_request_parameters.function_tools)
