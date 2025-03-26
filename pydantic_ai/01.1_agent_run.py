import asyncio
import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


def setup_environment():
    """加载环境变量并配置日志"""
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire="if-token-present")
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "Hs-Deepseek-v3"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url = setup_environment()

model = create_openai_model(api_key, base_url)


agent = Agent(model=model, instrument=True)

result_sync = agent.run_sync("What is the capital of Italy?")
print(result_sync.data)
# > Rome


async def main():
    result = await agent.run("What is the capital of France?")
    print(result.data)
    # > Paris

    async with agent.run_stream("What is the capital of the UK?") as response:
        print(await response.get_data())
        # > London


async def agent_iter_async_for():
    nodes = []
    # Begin an AgentRun, which is an async-iterable over the nodes of the agent's graph
    async with agent.iter("What is the capital of France?") as agent_run:
        async for node in agent_run:
            # Each node represents a step in the agent's execution
            nodes.append(node)
    print(nodes)
    print("========================================================")
    print(agent_run.result.data)
    # > Paris


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(agent_iter_async_for())
