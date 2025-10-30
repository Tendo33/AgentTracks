import asyncio
import os

from dotenv import load_dotenv

from agents import (
    Agent,
    AsyncOpenAI,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from agents.run import RunConfig

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")


external_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)


set_default_openai_client(client=external_client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)


model = OpenAIChatCompletionsModel(
    model="Qwen2.5-72B-Instruct-AWQ", openai_client=external_client
)


config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)


async def main():
    agent = Agent(
        name="Assistant",
        instructions="You are helpful Assistent.",
        model=model,
        model_settings=ModelSettings(temperature=0.8),
    )

    result = await Runner.run(
        agent, "Tell me about recursion in programming.", run_config=config
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
