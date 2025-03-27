import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich import print


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


api_key, base_url,tavily_api_key = setup_environment()
model = create_openai_model(api_key, base_url)

agent_tavily = Agent(
    model=model,
    tools=[tavily_search_tool(tavily_api_key)],
    system_prompt="Search tavily for the given query and return the results.",
)
agent_duck = Agent(
    model=model,
    tools=[duckduckgo_search_tool()],
    system_prompt="Search tavily for the given query and return the results.",
)

result = agent_tavily.run_sync(
    "Can you list the top five highest-grossing animated films of 2025?"
)
print(result.data)
print("===========================================================================")
print(result.all_messages())