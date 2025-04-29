import os
import random

import logfire
from dotenv import load_dotenv
from rich import print

from pydantic_ai import Agent, RunContext
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


"""方式一
使用 @agent.tool 装饰器 —— 适用于需要访问代理上下文的工具
使用 @agent.tool_plain 装饰器 —— 适用于不需要访问代理上下文的工具
"""

agent = Agent(
    model=model,
    deps_type=str,
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
    instrument=True,
)


# 不需要上下文
@agent.tool_plain
def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


# 需要上下文
@agent.tool
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps


dice_result = agent.run_sync("My guess is 4", deps="Anne")
print(dice_result.data)
print("=====================================================================")
print(dice_result.all_messages())
