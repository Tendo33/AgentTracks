from dataclasses import dataclass
from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from starlette.websockets import WebSocket


@dataclass
class WebSocketRequestContext:
    websocket: WebSocket
    langgraph_checkpointer: Optional[BaseCheckpointSaver] = None
