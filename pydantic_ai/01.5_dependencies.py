import asyncio
import os
from dataclasses import dataclass

import httpx
import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


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


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    model=model,
    deps_type=MyDeps,
)


@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get(
        "https://example.com",
        headers={"Authorization": f"Bearer {ctx.deps.api_key}"},
    )
    response.raise_for_status()
    return f"Prompt: {response.text}"


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps("foobar", client)
        result = await agent.run(
            "Tell me a joke.",
            deps=deps,
        )
        print(result.data)
# 在 weather agent 例子中重新看

if __name__ == "__main__":
    asyncio.run(main())
