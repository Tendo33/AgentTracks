from dataclasses import dataclass
from typing import Callable, Awaitable, Dict, Any, Optional
from starlette.websockets import WebSocket
from langgraph.checkpoint.base import BaseCheckpointSaver


@dataclass
class WebSocketRequestContext:
    websocket: WebSocket
    langgraph_checkpointer: Optional[BaseCheckpointSaver] = None
