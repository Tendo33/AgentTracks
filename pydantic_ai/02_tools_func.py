import os
import random

import logfire
from dotenv import load_dotenv
from rich import print

from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
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

"""方式二
使用 Agent 的 tools 关键字参数，可以接受普通函数或 Tool 的实例
"""


def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps


agent_a = Agent(
    model=model,
    deps_type=str,
    tools=[roll_die, get_player_name], # 自动判断要不要使用上下文
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
    instrument=True,
)
agent_b = Agent(
    model=model,
    deps_type=str,
    tools=[
        Tool(roll_die, takes_ctx=False),
        Tool(get_player_name, takes_ctx=True),  # 显示制定要使用上下文
    ],
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
    instrument=True,
)
dice_result = agent_a.run_sync("My guess is 4", deps="Anne")
print(dice_result.data)
print("=====================================================================")
print(dice_result.all_messages())