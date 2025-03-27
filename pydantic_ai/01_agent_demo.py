import os

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from rich import print


def setup_environment():
    """加载环境变量并配置日志"""
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire="if-token-present")
    load_dotenv()
    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


def run_agent_with_simple_prompt(
    agent: Agent, prompt: str, temperature: float = 0.8, top_p: float = 0.95
):
    """运行 Agent 并返回结果"""
    settings = OpenAIModelSettings(temperature=temperature, top_p=top_p)
    result = agent.run_sync(user_prompt=prompt, model_settings=settings)
    print(result.data)


def run_agent_with_structured_output(agent: Agent, prompt: str):
    """运行 Agent 并返回结构化结果"""
    result = agent.run_sync(prompt)
    print(result.data)
    print(result.usage())


class MyModel(BaseModel):
    """定义结构化数据模型"""

    city: str
    country: str


def main():
    # 1. 设置环境
    api_key, base_url = setup_environment()

    # 2. 创建 OpenAI 模型
    model = create_openai_model(api_key, base_url)

    # 3. 创建第一个 Agent（简单回答）
    simple_agent = Agent(model, system_prompt="Be concise, reply with one sentence.")
    run_agent_with_simple_prompt(simple_agent, 'Where does "hello world" come from?')

    # 4. 创建第二个 Agent（结构化输出）
    structured_agent = Agent(model, result_type=MyModel, instrument=True)
    run_agent_with_structured_output(structured_agent, "The windy city in the US of A.")


if __name__ == "__main__":
    main()
