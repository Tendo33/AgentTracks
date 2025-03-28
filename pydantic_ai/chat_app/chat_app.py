from __future__ import annotations as _annotations

import asyncio
import json
import os
import sqlite3
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, TypeVar

import fastapi
import logfire
from dotenv import load_dotenv
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from rich import print
from typing_extensions import LiteralString, ParamSpec, TypedDict

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


def setup_environment():
    """加载环境变量并配置日志
    该函数从 `.env` 文件中加载环境变量，并配置日志系统。
    如果配置了 `LOGFIRE_TOKEN`，则启用日志发送功能。
    返回 OpenAI 的 API Key 和 API Base URL。
    """
    load_dotenv()
    logfire_token = os.getenv("LOGFIRE_TOKEN")
    # 'if-token-present' 表示如果没有配置 logfire，不会发送日志信息
    logfire.configure(token=logfire_token, send_to_logfire="if-token-present")

    return os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE")


def create_openai_model(
    api_key: str, base_url: str, model_name: str = "deepseek-v3-250324"
) -> OpenAIModel:
    """创建 OpenAI 模型实例
    该函数根据提供的 API Key 和 Base URL 创建一个 OpenAI 模型实例。
    使用 `OpenAIProvider` 作为模型提供者，并返回 `OpenAIModel` 实例。
    """
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    return OpenAIModel(model_name, provider=provider)


api_key, base_url = setup_environment()
model = create_openai_model(api_key, base_url)
agent = Agent(model=model, instrument=True)
THIS_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    """FastAPI 应用的生命周期管理
    该函数用于管理 FastAPI 应用的生命周期。
    在应用启动时，连接到数据库，并在应用关闭时释放资源。
    """
    async with Database.connect() as db:
        yield {"db": db}


app = fastapi.FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app)


@app.get("/")
async def index() -> FileResponse:
    """返回聊天应用的 HTML 页面
    该函数返回聊天应用的前端 HTML 页面，用于渲染用户界面。
    """
    return FileResponse((THIS_DIR / "chat_app.html"), media_type="text/html")


@app.get("/chat_app.ts")
async def main_ts() -> FileResponse:
    """返回聊天应用的 TypeScript 代码
    该函数返回聊天应用的前端 TypeScript 代码，供浏览器动态编译和执行。
    """
    return FileResponse((THIS_DIR / "chat_app.ts"), media_type="text/plain")


async def get_db(request: Request) -> Database:
    """获取数据库实例
    该函数从 FastAPI 的请求上下文中获取数据库实例，供其他函数使用。
    """
    return request.state.db


@app.get("/chat/")
async def get_chat(database: Database = Depends(get_db)) -> Response:
    """获取聊天记录
    该函数从数据库中获取所有聊天记录，并将其以 JSON 格式返回给客户端。
    """
    msgs = await database.get_messages()
    return Response(
        b"\n".join(json.dumps(to_chat_message(m)).encode("utf-8") for m in msgs),
        media_type="text/plain",
    )


class ChatMessage(TypedDict):
    """Format of messages sent to the browser."""

    role: Literal["user", "model"]
    timestamp: str
    content: str


def to_chat_message(m: ModelMessage) -> ChatMessage:
    """将 ModelMessage 转换为 ChatMessage 格式
    该函数将 `ModelMessage` 实例转换为前端所需的 `ChatMessage` 格式。
    根据消息类型（用户输入或模型响应）提取内容并格式化。
    """
    first_part = m.parts[0]
    if isinstance(m, ModelRequest):
        if isinstance(first_part, UserPromptPart):
            assert isinstance(first_part.content, str)
            return {
                "role": "user",
                "timestamp": first_part.timestamp.isoformat(),
                "content": first_part.content,
            }
    elif isinstance(m, ModelResponse):
        if isinstance(first_part, TextPart):
            return {
                "role": "model",
                "timestamp": m.timestamp.isoformat(),
                "content": first_part.content,
            }
    raise UnexpectedModelBehavior(f"Unexpected message type for chat app: {m}")


@app.post("/chat/")
async def post_chat(
    prompt: Annotated[str, fastapi.Form()], database: Database = Depends(get_db)
) -> StreamingResponse:
    """处理用户输入的聊天消息
    该函数处理用户输入的聊天消息，并流式返回模型的响应。
    具体步骤包括：
    1. 立即返回用户输入的消息。
    2. 从数据库中获取历史消息作为上下文。
    3. 调用模型生成响应并流式返回。
    4. 将新消息保存到数据库中。
    """

    async def stream_messages():
        """Streams new line delimited JSON `Message`s to the client."""
        # 1. 首先，将用户输入的 prompt 立即流式传输给客户端
        yield (
            json.dumps(
                {
                    "role": "user",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "content": prompt,
                }
            ).encode("utf-8")
            + b"\n"
        )
        # 2. 从数据库中获取历史消息，作为上下文传递给 agent
        messages = await database.get_messages()
        # 3. 使用用户输入的 prompt 和历史消息运行 agent
        async with agent.run_stream(prompt, message_history=messages) as result:
            async for text in result.stream(debounce_by=0.01):
                # 4. 将 agent 生成的文本转换为 ModelResponse 格式并流式传输给客户端
                m = ModelResponse(parts=[TextPart(text)], timestamp=result.timestamp())
                print(m)
                yield json.dumps(to_chat_message(m)).encode("utf-8") + b"\n"

        # 5. 将新消息（用户输入和 agent 的响应）添加到数据库中
        await database.add_messages(result.new_messages_json())

    return StreamingResponse(stream_messages(), media_type="text/plain")


P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class Database:
    """简单的 SQLite 数据库管理类
    该类用于管理聊天消息的存储和检索。
    由于 SQLite 标准库是同步的，使用线程池执行器来异步执行数据库操作。
    """

    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = THIS_DIR / ".chat_app_messages.sqlite"
    ) -> AsyncIterator[Database]:
        """连接到数据库
        该函数用于异步连接到 SQLite 数据库，并返回数据库实例。
        在连接成功后，会创建一个消息表（如果不存在）。
        """
        with logfire.span("connect to DB"):
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            con = await loop.run_in_executor(executor, cls._connect, file)
            slf = cls(con, loop, executor)
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        """同步连接数据库
        该函数用于同步连接到 SQLite 数据库，并初始化消息表。
        """
        con = sqlite3.connect(str(file))
        con = logfire.instrument_sqlite3(con)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, message_list TEXT);"
        )
        con.commit()
        return con

    async def add_messages(self, messages: bytes):
        """添加消息到数据库
        该函数将新消息（用户输入和模型响应）插入到数据库中。
        """
        await self._asyncify(
            self._execute,
            "INSERT INTO messages (message_list) VALUES (?);",
            messages,
            commit=True,
        )
        await self._asyncify(self.con.commit)

    async def get_messages(self) -> list[ModelMessage]:
        """从数据库中获取消息
        该函数从数据库中检索所有消息，并将其转换为 `ModelMessage` 列表。
        """
        c = await self._asyncify(
            self._execute, "SELECT message_list FROM messages order by id"
        )
        rows = await self._asyncify(c.fetchall)
        messages: list[ModelMessage] = []
        for row in rows:
            messages.extend(ModelMessagesTypeAdapter.validate_json(row[0]))
        return messages

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        """执行 SQL 查询
        该函数用于执行 SQL 查询，并返回结果游标。
        如果 `commit` 为 True，则提交事务。
        """
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        """将同步函数异步化
        该函数将同步的数据库操作异步化，以便在异步上下文中执行。
        """
        return await self._loop.run_in_executor(  # type: ignore
            self._executor,
            partial(func, **kwargs),
            *args,  # type: ignore
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "chat_app:app",
        reload=True,
        reload_dirs=[str(THIS_DIR)],
        port=7541,
        host="10.0.34.60",
    )
