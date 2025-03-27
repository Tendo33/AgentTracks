import asyncio
import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_graph import End
from rich import print


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


def initialize_agent():
    """初始化环境、创建 OpenAI 模型和 Agent 实例"""
    api_key, base_url = setup_environment()
    # 创建 OpenAI 模型实例
    model = create_openai_model(api_key, base_url)
    # 创建 Agent 实例，并启用 instrument（用于监控和调试）
    agent = Agent(model=model, instrument=True)
    return agent


agent = initialize_agent()


# 同步方式运行 Agent
result_sync = agent.run_sync("What is the capital of Italy?")
print(result_sync.data)
print("========================================================")
print(result_sync.usage())


async def main():
    #异步方式运行 Agent
    result = await agent.run("What is the capital of France?")
    print(result.data)

    # 使用流式方式运行 Agent
    async with agent.run_stream("What is the capital of the UK?") as response:
        print(await response.get_data())


async def agent_iter_async_for():
    """使用 async for 迭代 Agent 的执行节点"""
    nodes = []
    # 开始一个 AgentRun，它是一个异步可迭代对象，用于遍历 Agent 的执行节点
    async with agent.iter("What is the capital of France?") as agent_run:
        async for node in agent_run:
            # 每个节点代表 Agent 执行的一个步骤
            nodes.append(node)
    print(nodes)
    print("========================================================")
    print(agent_run.result.data)  # 输出: Paris

async def agent_iter_next():
    """使用 next 方法手动驱动 Agent 的迭代"""
    async with agent.iter("What is the capital of France?") as agent_run:
        node = agent_run.next_node

        all_nodes = [node]

        # 手动驱动迭代
        while not isinstance(node, End):
            node = await agent_run.next(node)
            all_nodes.append(node)

        print(all_nodes)


if __name__ == "__main__":
    # 异步运行 main 函数
    # asyncio.run(main())

    # 异步运行 agent_iter_async_for 函数
    # asyncio.run(agent_iter_async_for())

    # 异步运行 agent_iter_next 函数
    asyncio.run(agent_iter_next())
