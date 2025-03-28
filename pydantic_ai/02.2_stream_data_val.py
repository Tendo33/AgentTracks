import asyncio
import os
from datetime import date

import logfire
from dotenv import load_dotenv
from pydantic import ValidationError
from rich import print
from typing_extensions import TypedDict

from pydantic_ai import Agent
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




class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str


agent = Agent(model=model, result_type=UserProfile)


async def main():
    user_input = "My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid."
    async with agent.run_stream(user_input) as result:
        async for message, last in result.stream_structured(debounce_by=0.01):
            try:
                profile = await result.validate_structured_result(
                    message,
                    allow_partial=not last,
                )
            except ValidationError:
                continue
            print(profile)

asyncio.run(main())