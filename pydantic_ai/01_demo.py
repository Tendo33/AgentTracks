import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

model = OpenAIModel(
    "Hs-Deepseek-v3",
    provider=OpenAIProvider(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE),
)

agent = Agent(
    model=model,
    system_prompt="Be concise, reply with one sentence.",
)
setting = OpenAIModelSettings(temperature=0.8, top_p=0.95)
result = agent.run_sync(
    user_prompt='Where does "hello world" come from?', model_settings=setting
)
print(result.data)
