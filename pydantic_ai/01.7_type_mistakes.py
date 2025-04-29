import dataclasses
import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
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


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)


@dataclasses.dataclass
class User:
    name: str


agent = Agent(
    model,
    deps_type=User,
    result_type=bool,
)


@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


def foobar(x: bytes) -> None:
    pass


result = agent.run_sync('Does their name start with "A"?', deps=User("Anne"))
foobar(result.data)
print(result.data)
print("==============================================")
print(result.all_messages())
"""
a = [
    ModelRequest(
        parts=[
            SystemPromptPart(
                content="The user's name is User(name='Anne').",
                timestamp=datetime.datetime(
                    2025, 3, 27, 6, 33, 59, 139430, tzinfo=datetime.timezone.utc
                ),
                dynamic_ref=None,
                part_kind="system-prompt",
            ),
            UserPromptPart(
                content='Does their name start with "A"?',
                timestamp=datetime.datetime(
                    2025, 3, 27, 6, 33, 59, 139434, tzinfo=datetime.timezone.utc
                ),
                part_kind="user-prompt",
            ),
        ],
        kind="request",
    ),
    ModelResponse(
        parts=[
            TextPart(content="", part_kind="text"),
            ToolCallPart(
                tool_name="final_result",
                args='{"response":true}',
                tool_call_id="call_nf3i7v6xs8747idhhkvqraj5",
                part_kind="tool-call",
            ),
        ],
        model_name="deepseek-v3-250324",
        timestamp=datetime.datetime(
            2025, 3, 27, 6, 33, 59, tzinfo=datetime.timezone.utc
        ),
        kind="response",
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name="final_result",
                content="Final result processed.",
                tool_call_id="call_nf3i7v6xs8747idhhkvqraj5",
                timestamp=datetime.datetime(
                    2025, 3, 27, 6, 33, 59, 831888, tzinfo=datetime.timezone.utc
                ),
                part_kind="tool-return",
            )
        ],
        kind="request",
    ),
]
"""
