import os
from datetime import date

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

"""
一般来说，系统提示可以分为两大类：

静态系统提示：这些在编写代码时已知，可以通过 Agent 构造函数的 system_prompt 参数来定义。

动态系统提示：这些在运行时才知道其上下文，因此需要通过带有 @agent.system_prompt 装饰器的函数来定义。
"""


def setup_environment():
    """加载环境变量并配置日志"""
    # 'if-token-present' 表示如果没有配置 logfire，不会发送日志信息
    logfire.configure(send_to_logfire="if-token-present")
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)


agent = Agent(
    model=model,
    deps_type=str,
    system_prompt="Use the customer's name while replying to them.",
)


@agent.system_prompt
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:
    return f"The date is {date.today()}."


result = agent.run_sync("What is the date?", deps="Frank")
print(result.data)
print(result.all_messages())
