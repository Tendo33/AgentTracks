import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
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


agent = Agent(model=model)

# First run
result1 = agent.run_sync("Who was Albert Einstein?")
print(result1.data)
print("=========================================================================")

print(result1.all_messages())
"""
a = [
    ModelRequest(
        parts=[
            UserPromptPart(
                content="Who was Albert Einstein?",
                timestamp=datetime.datetime(
                    2025, 3, 27, 3, 12, 50, 609847, tzinfo=datetime.timezone.utc
                ),
                part_kind="user-prompt",
            )
        ],
        kind="request",
    ),
    ModelResponse(
        parts=[
            TextPart(
                content="Albert Einstein (1879–1955) was a German-born theoretical physicist who revolutionized modern physics with his groundbreaking contributions, most notably the **theory of relativity**. He is widely regarded as one of the greatest scientists of all time.\n\n### **Key Contributions:**\n1. **Special Theory of Relativity (1905)** – Introduced the famous equation **E=mc²**, showing the relationship between mass and energy.\n2. **General Theory of Relativity (1915)** – Described gravity as the curvature of spacetime caused by mass and energy.\n3. **Photoelectric Effect (1905)** – Explained how light can eject electrons from metals (this work earned him the **Nobel Prize in Physics in 1921**).\n4. **Brownian Motion (1905)** – Provided evidence for the existence of atoms.\n5. **Quantum Theory** – Though skeptical of quantum mechanics, his debates with Niels Bohr helped shape the field.\n\n### **Legacy:**\n- Einstein’s work laid the foundation for technologies like GPS, nuclear energy, and advanced cosmology.\n- He became a global icon of genius and advocated for **peace, civil rights, and scientific freedom**.\n- Fled Nazi Germany in 1933 and settled in the U.S., where he worked at Princeton University.\n\nEinstein’s name is synonymous with intelligence, and his discoveries continue to shape our understanding of the universe. 🌌🔭",
                part_kind="text",
            )
        ],
        model_name="deepseek-v3-250324",
        timestamp=datetime.datetime(
            2025, 3, 27, 3, 13, 1, tzinfo=datetime.timezone.utc
        ),
        kind="response",
    ),
]
"""

print("=========================================================================")

result2 = agent.run_sync(
    "What was his most famous equation?",
    message_history=result1.all_messages(),
)
print(result2.data)
print("=========================================================================")
print(result2.all_messages())
print("=========================================================================")
result3 = agent.run_sync(
    "Who is his wife?",
    message_history=result2.all_messages(),
)
print(result3.data)
