import asyncio
import os
from dataclasses import dataclass
from datetime import date

import logfire
from dotenv import load_dotenv
from rich import print

from pydantic_ai import Agent
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.tools import RunContext


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


@dataclass
class WeatherService:
    async def get_forecast(self, location: str, forecast_date: date) -> str:
        # In real code: call weather API, DB queries, etc.
        return f"The forecast in {location} on {forecast_date} is 24°C and sunny."

    async def get_historic_weather(self, location: str, forecast_date: date) -> str:
        # In real code: call a historical weather API or DB
        return (
            f"The weather in {location} on {forecast_date} was 18°C and partly cloudy."
        )


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)

# 这个泛型是怎么泛的？
weather_agent = Agent[WeatherService, str](
    model=model,
    deps_type=WeatherService,
    result_type=str,  # We'll produce a final answer as plain text
    system_prompt="Providing a weather forecast at the locations the user provides.",
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext[WeatherService],
    location: str,
    forecast_date: date,
) -> str:
    if forecast_date >= date.today():
        return await ctx.deps.get_forecast(location, forecast_date)
    else:
        return await ctx.deps.get_historic_weather(location, forecast_date)


output_messages: list[str] = []


async def main():
    user_prompt = "What will the weather be like in Paris on Tuesday?"

    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(user_prompt, deps=WeatherService()) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                # A user prompt node => The user has provided input
                output_messages.append(f"=== UserPromptNode: {node.user_prompt} ===")
            elif Agent.is_model_request_node(node):
                # A model request node => We can stream tokens from the model's request
                output_messages.append(
                    "=== ModelRequestNode: streaming partial request tokens ==="
                )
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent):
                            output_messages.append(
                                f"[Request] Starting part {event.index}: {event.part!r}"
                            )
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, TextPartDelta):
                                output_messages.append(
                                    f"[Request] Part {event.index} text delta: {event.delta.content_delta!r}"
                                )
                            elif isinstance(event.delta, ToolCallPartDelta):
                                output_messages.append(
                                    f"[Request] Part {event.index} args_delta={event.delta.args_delta}"
                                )
                        elif isinstance(event, FinalResultEvent):
                            output_messages.append(
                                f"[Result] The model produced a final result (tool_name={event.tool_name})"
                            )
            elif Agent.is_call_tools_node(node):
                # A handle-response node => The model returned some data, potentially calls a tool
                output_messages.append(
                    "=== CallToolsNode: streaming partial response & tool usage ==="
                )
                async with node.stream(run.ctx) as handle_stream:
                    async for event in handle_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            output_messages.append(
                                f"[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})"
                            )
                        elif isinstance(event, FunctionToolResultEvent):
                            output_messages.append(
                                f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}"
                            )
            elif Agent.is_end_node(node):
                assert run.result.data == node.data.data
                # Once an End node is reached, the agent run is complete
                output_messages.append(f"=== Final Agent Output: {run.result.data} ===")


async def main2():
    user_prompt = "What will the weather be like in Paris on Tuesday?"

    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(user_prompt, deps=WeatherService()) as run:
        async for node in run:
            print(node)
            print("==============================================")
            if Agent.is_end_node(node):
                pass



agent = Agent(model=model,result_type=str)

# stream = True 的流式返回
async def main3():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        # delta=True 是传统的流式，如果为False，那每一次都会输出前面的句子
        async for message in result.stream_text(delta=True):
            print(message,end="")

if __name__ == "__main__":
    asyncio.run(main3())

    # print(output_messages)
    a = [
        "=== ModelRequestNode: streaming partial request tokens ===",
        "[Request] Starting part 0: TextPart(content='', part_kind='text')",
        "[Result] The model produced a final result (tool_name=None)",
        "[Request] Starting part 1: ToolCallPart(tool_name='weather_forecast', args='', tool_call_id='call_l0h71e24lg4zf2ty92de9kjo', part_kind='tool-call')",
        "[Request] Part 0 text delta: ''",
        '[Request] Part 1 args_delta={"',
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=location",
        "[Request] Part 0 text delta: ''",
        '[Request] Part 1 args_delta=":"',
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=Paris",
        "[Request] Part 0 text delta: ''",
        '[Request] Part 1 args_delta=","',
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=fore",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=cast",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=_date",
        "[Request] Part 0 text delta: ''",
        '[Request] Part 1 args_delta=":"',
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=202",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=3",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=-",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=10",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=-",
        "[Request] Part 0 text delta: ''",
        "[Request] Part 1 args_delta=17",
        "[Request] Part 0 text delta: ''",
        '[Request] Part 1 args_delta="}',
        "[Request] Part 0 text delta: ''",
        "=== CallToolsNode: streaming partial response & tool usage ===",
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2023-10-17"} (tool_call_id=\'call_l0h71e24lg4zf2ty92de9kjo\')',
        "[Tools] Tool call 'call_l0h71e24lg4zf2ty92de9kjo' returned => The weather in Paris on 2023-10-17 was 18°C and partly cloudy.",
        "=== ModelRequestNode: streaming partial request tokens ===",
        "[Request] Starting part 0: TextPart(content='On', part_kind='text')",
        "[Result] The model produced a final result (tool_name=None)",
        "[Request] Part 0 text delta: ' Tuesday'",
        "[Request] Part 0 text delta: ','",
        "[Request] Part 0 text delta: ' October'",
        "[Request] Part 0 text delta: ' '",
        "[Request] Part 0 text delta: '17'",
        "[Request] Part 0 text delta: ','",
        "[Request] Part 0 text delta: ' '",
        "[Request] Part 0 text delta: '202'",
        "[Request] Part 0 text delta: '3'",
        "[Request] Part 0 text delta: ','",
        "[Request] Part 0 text delta: ' the'",
        "[Request] Part 0 text delta: ' weather'",
        "[Request] Part 0 text delta: ' in'",
        "[Request] Part 0 text delta: ' Paris'",
        "[Request] Part 0 text delta: ' is'",
        "[Request] Part 0 text delta: ' expected'",
        "[Request] Part 0 text delta: ' to'",
        "[Request] Part 0 text delta: ' be'",
        "[Request] Part 0 text delta: ' **'",
        "[Request] Part 0 text delta: '18'",
        "[Request] Part 0 text delta: '°'",
        "[Request] Part 0 text delta: 'C'",
        "[Request] Part 0 text delta: '**'",
        "[Request] Part 0 text delta: ' and'",
        "[Request] Part 0 text delta: ' **'",
        "[Request] Part 0 text delta: 'part'",
        "[Request] Part 0 text delta: 'ly'",
        "[Request] Part 0 text delta: ' cloudy'",
        "[Request] Part 0 text delta: '**.'",
        "[Request] Part 0 text delta: ' Make'",
        "[Request] Part 0 text delta: ' sure'",
        "[Request] Part 0 text delta: ' to'",
        "[Request] Part 0 text delta: ' dress'",
        "[Request] Part 0 text delta: ' comfortably'",
        "[Request] Part 0 text delta: ' and'",
        "[Request] Part 0 text delta: ' enjoy'",
        "[Request] Part 0 text delta: ' your'",
        "[Request] Part 0 text delta: ' day'",
        "[Request] Part 0 text delta: '!'",
        "[Request] Part 0 text delta: ''",
        "=== CallToolsNode: streaming partial response & tool usage ===",
        "=== Final Agent Output: On Tuesday, October 17, 2023, the weather in Paris is expected to be **18°C** and **partly cloudy**. Make sure to dress comfortably and enjoy your day! ===",
    ]
