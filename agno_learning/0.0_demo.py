import os

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from dotenv import load_dotenv
from rich import print


def setup_environment():
    """加载环境变量并配置日志"""
    load_dotenv()
    print("加载成功")
    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


api_key, base_url = setup_environment()

agent = Agent(
    model=OpenAILike(
        id="deepseek-v3-250324",
        api_key=api_key,
        base_url=base_url,
    ),
    stream=True,
)

# Print the response in the terminal
agent.print_response("Share a 2 sentence horror story.")
