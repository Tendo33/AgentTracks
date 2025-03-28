import os

import logfire
from dotenv import load_dotenv
from rich import print

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits


def setup_environment():
    """加载环境变量并配置日志"""
    load_dotenv()
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    # 'if-token-present' 表示如果没有配置 logfire，不会发送日志信息
    logfire.configure(token=logfire_token, send_to_logfire="if-token-present")

    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)


joke_selection_agent = Agent(
    model=model,
    system_prompt=(
        "Use the `joke_factory` to generate some jokes, then choose the best. "
        "You must return just a single joke."
    ),
)
joke_generation_agent = Agent(model=model, result_type=list[str])


@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f"Please generate {count} jokes.",
        usage=ctx.usage,
    )
    return r.data


result = joke_selection_agent.run_sync(
    "Tell me a joke.",
    usage_limits=UsageLimits(request_limit=10, total_tokens_limit=3000),
)
print(result.data)
print("============================================================")
print(result.usage())

print("============================================================")
print(result.all_messages())
