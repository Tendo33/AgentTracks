"""Example of PydanticAI with multiple tools which the LLM needs to call in turn to answer a question.

In this case the idea is a "weather" agent — the user can ask for the weather in multiple cities,
the agent will use the `get_lat_lng` tool to get the latitude and longitude of the locations, then use
the `get_weather` tool to get the weather.

Run with:

    uv run -m pydantic_ai_examples.weather_agent
"""

from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import logfire
from devtools import debug
from dotenv import load_dotenv
from httpx import AsyncClient
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich import print


def setup_environment():
    """加载环境变量并配置日志"""
    load_dotenv()
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    # 'if-token-present' 表示如果没有配置 logfire，不会发送日志信息
    logfire.configure(token=logfire_token, send_to_logfire="if-token-present")

    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)


@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None


weather_agent = Agent(
    model=model,
    # 'Be concise, reply with one sentence.' is enough for some models (like openai) to use
    # the below tools appropriately, but others like anthropic and gemini require a bit more direction.
    system_prompt=(
        "Be concise, reply with one sentence."
        "Use the `get_lat_lng` tool to get the latitude and longitude of the locations, "
        "then use the `get_weather` tool to get the weather."
    ),
    deps_type=Deps,
    retries=2,
    instrument=True,
)


@weather_agent.tool
async def get_lat_lng(
    ctx: RunContext[Deps], location_description: str
) -> dict[str, float]:
    """Get the latitude and longitude of a location.

    Args:
        ctx: The context.
        location_description: A description of a location.
    """
    if ctx.deps.geo_api_key is None:
        # if no API key is provided, return a dummy response (London)
        return {"lat": 51.1, "lng": -0.1}

    params = {
        "q": location_description,
        "api_key": ctx.deps.geo_api_key,
    }
    with logfire.span("calling geocode API", params=params) as span:
        r = await ctx.deps.client.get("https://geocode.maps.co/search", params=params)
        r.raise_for_status()
        data = r.json()
        span.set_attribute("response", data)

    if data:
        return {"lat": data[0]["lat"], "lng": data[0]["lon"]}
    else:
        raise ModelRetry("Could not find the location")


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    if ctx.deps.weather_api_key is None:
        # if no API key is provided, return a dummy response
        return {"temperature": "21 °C", "description": "Sunny"}

    params = {
        "apikey": ctx.deps.weather_api_key,
        "location": f"{lat},{lng}",
        "units": "metric",
    }
    with logfire.span("calling weather API", params=params) as span:
        r = await ctx.deps.client.get(
            "https://api.tomorrow.io/v4/weather/realtime", params=params
        )
        r.raise_for_status()
        data = r.json()
        span.set_attribute("response", data)

    values = data["data"]["values"]
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: "Clear, Sunny",
        1100: "Mostly Clear",
        1101: "Partly Cloudy",
        1102: "Mostly Cloudy",
        1001: "Cloudy",
        2000: "Fog",
        2100: "Light Fog",
        4000: "Drizzle",
        4001: "Rain",
        4200: "Light Rain",
        4201: "Heavy Rain",
        5000: "Snow",
        5001: "Flurries",
        5100: "Light Snow",
        5101: "Heavy Snow",
        6000: "Freezing Drizzle",
        6001: "Freezing Rain",
        6200: "Light Freezing Rain",
        6201: "Heavy Freezing Rain",
        7000: "Ice Pellets",
        7101: "Heavy Ice Pellets",
        7102: "Light Ice Pellets",
        8000: "Thunderstorm",
    }
    return {
        "temperature": f"{values['temperatureApparent']:0.0f}°C",
        "description": code_lookup.get(values["weatherCode"], "Unknown"),
    }


async def main():
    async with AsyncClient() as client:
        # create a free API key at https://www.tomorrow.io/weather-api/
        weather_api_key = os.getenv("WEATHER_API_KEY")
        # create a free API key at https://geocode.maps.co/
        geo_api_key = os.getenv("GEO_API_KEY")
        deps = Deps(
            client=client, weather_api_key=weather_api_key, geo_api_key=geo_api_key
        )
        result = await weather_agent.run(
            "What is the weather like in Beijing and in Qingdao?", deps=deps
        )
        debug(result)
        print("=====================================================================")
        print("Response:", result.data)
        print("=====================================================================")
        print(result.all_messages())


if __name__ == "__main__":
    asyncio.run(main())
