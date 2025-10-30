import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

# os.environ["OPENAI_API_KEY"] = "sk-uG93vRV5V2Dog95J15FfCdE5DaAe438fBb17C642F2E1Ae57"
# os.environ["OPENAI_API_BASE"] = "http://ai-api.e-tudou.com:9000/v1"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

external_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

set_default_openai_client(client=external_client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)


class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str


guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
    model=OpenAIChatCompletionsModel(
        model="Qwen2.5-72B-Instruct-AWQ",
        openai_client=external_client,
    ),
    model_settings=ModelSettings(temperature=0.8),
)

math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)

history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
)


async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=homework_guardrail),
    ],
)


async def main():
    result = await Runner.run(
        triage_agent, "who was the first president of the united states?"
    )
    print(result.final_output)

    result = await Runner.run(triage_agent, "what is life")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
