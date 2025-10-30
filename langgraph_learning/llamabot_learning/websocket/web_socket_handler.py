import asyncio
import logging

from agents.llamapress_legacy.state import LlamaPressMessage
from fastapi import WebSocket, WebSocketDisconnect

from websocket.request_handler import RequestHandler
from websocket.web_socket_connection_manager import WebSocketConnectionManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    def __init__(self, websocket: WebSocket, manager: WebSocketConnectionManager):
        self.websocket = websocket
        self.manager = manager
        self.request_handler = RequestHandler(manager.app)

    async def handle_websocket(self):
        logger.info(f"New WebSocket connection attempt from {self.websocket.client}")
        await self.manager.connect(self.websocket)
        current_task = None
        try:
            while True:
                try:
                    start_time = asyncio.get_event_loop().time()

                    logger.info("Waiting for message from LlamaPress")
                    json_data = await self.websocket.receive_json()

                    receive_time = asyncio.get_event_loop().time()

                    ### Warning: If LangGraph does await LLM calls appropriately, then this main thread can get blocked and will stop responding to pings from LlamaPress, ultimately killing the websocket connection.
                    logger.info(
                        f"Message received after {receive_time - start_time:.2f}s"
                    )
                    logger.info("Received message from LlamaPress!")

                    if isinstance(json_data, dict) and json_data.get("type") == "ping":
                        logger.info("PING RECV, SENDING PONG")
                        # prevent batch queue
                        await asyncio.shield(
                            self.manager.send_personal_message(
                                {"type": "pong"}, self.websocket
                            )
                        )
                        continue

                    if (
                        isinstance(json_data, dict)
                        and json_data.get("type") == "cancel"
                    ):
                        logger.info("CANCEL RECV")
                        if current_task and not current_task.done():
                            current_task.cancel()
                            await self.manager.send_personal_message(
                                {
                                    "type": "system_message",
                                    "content": "Previous task has been cancelled",
                                },
                                self.websocket,
                            )
                        continue

                    # Cancel previous task if it exists and create new one
                    if current_task and not current_task.done():
                        logger.info("Cancelling previous task")
                        current_task.cancel()
                        try:
                            await current_task
                        except asyncio.CancelledError:
                            logger.info("Previous task was cancelled successfully")

                    message = LlamaPressMessage(**json_data)

                    logger.info(f"Received message: {message}")
                    current_task = asyncio.create_task(
                        self.request_handler.handle_request(message, self.websocket)
                    )
                except WebSocketDisconnect as e:
                    logger.info(f"WebSocket disconnected! Error: {e}")
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {str(e)}")
                    await self.manager.send_personal_message(
                        {"type": "error", "content": f"Error 80: {str(e)}"},
                        self.websocket,
                    )
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await self.manager.send_personal_message(
                {"type": "error", "content": f"Error 253: {str(e)}"}, self.websocket
            )
        finally:
            if current_task and not current_task.done():
                current_task.cancel()
                try:
                    logger.info("Cancelling current task")
                    await current_task
                except asyncio.CancelledError:
                    logger.info("Current task was cancelled successfully")
                    pass
            self.manager.disconnect(self.websocket)
            self.request_handler.cleanup_connection(self.websocket)
