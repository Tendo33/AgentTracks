import json
import logging
import os
import time

from agents.react_agent.nodes import build_workflow
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import CheckpointTuple
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langsmith import Client
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from websocket.web_socket_connection_manager import WebSocketConnectionManager
from websocket.web_socket_handler import WebSocketHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("chat_app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
app.mount("/assets", StaticFiles(directory="../assets"), name="assets")
app.mount("/examples", StaticFiles(directory="../examples"), name="examples")

# Initialize the ChatOpenAI client
llm = ChatOpenAI(model="o4-mini-2025-04-16")

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))

# This is responsible for holding and managing all active websocket connections.
manager = WebSocketConnectionManager(app)


# Pydantic model for chat request
class ChatMessage(BaseModel):
    message: str
    thread_id: str = None  # Optional thread_id parameter
    agent: str = None  # Optional agent parameter


# Application state to hold persistent checkpointer, important for session-based persistence.
app.state.checkpointer = None
app.state.async_checkpointer = None


def get_or_create_checkpointer():
    """Get persistent checkpointer, creating once if needed"""
    if app.state.checkpointer is None:
        db_uri = os.getenv("DB_URI")
        if db_uri:
            try:
                # Create connection pool and PostgresSaver directly
                pool = ConnectionPool(db_uri)
                app.state.checkpointer = PostgresSaver(pool)
                app.state.checkpointer.setup()
                logger.info("Using PostgreSQL persistence.")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to PostgreSQL: {e}. Using MemorySaver."
                )
                app.state.checkpointer = MemorySaver()
        else:
            logger.info(
                "No DB_URI found. Using MemorySaver for session-based persistence."
            )
            app.state.checkpointer = MemorySaver()

    return app.state.checkpointer


@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve the home.html file
    with open("home.html") as f:
        return f.read()


@app.get("/hello", response_class=JSONResponse)
async def hello():
    return {"message": "Hello, World! 🦙💬"}


@app.post("/chat-message")
async def chat_message(chat_message: ChatMessage):
    request_id = f"req_{int(time.time())}_{hash(chat_message.message) % 1000}"
    logger.info(
        f"[{request_id}] New chat message received: {chat_message.message[:50]}..."
    )

    # Get the existing HTML content from page.html
    try:
        with open("../page.html", "r") as f:
            existing_html_content = f.read()
    except FileNotFoundError:
        existing_html_content = ""

    # Define a generator function to stream the response
    async def response_generator():
        # Track the final state to serialize at the end
        final_state = None

        try:
            logger.info(f"[{request_id}] Starting streaming response")

            # Initial response with request ID
            yield json.dumps({"type": "start", "request_id": request_id}) + "\n"

            # Use the provided thread_id or default to "5"
            thread_id = chat_message.thread_id or "5"
            logger.info(f"[{request_id}] Using thread_id: {thread_id}")

            checkpointer = get_or_create_checkpointer()
            graph = build_workflow(checkpointer=checkpointer)
            stream = graph.stream(
                {
                    "messages": [HumanMessage(content=chat_message.message)],
                    "initial_user_message": chat_message.message,
                    "existing_html_content": existing_html_content,
                },
                config={"configurable": {"thread_id": thread_id}},
                stream_mode=[
                    "updates",
                    "messages",
                ],  # "values" is the third option ( to return the entire state object )
            )

            # Stream each chunk
            for chunk in stream:
                if chunk is not None:
                    is_this_chunk_an_llm_message = (
                        isinstance(chunk, tuple)
                        and len(chunk) == 2
                        and chunk[0] == "messages"
                    )
                    is_this_chunk_an_update_stream_type = (
                        isinstance(chunk, tuple)
                        and len(chunk) == 2
                        and chunk[0] == "updates"
                    )

                    if is_this_chunk_an_llm_message:  ## If this is a message from the LLM. (Known as a 'Messages' Chunk streaming from LangGraph
                        # Get the langgraph_node_info.
                        langgraph_node_info = chunk[
                            1
                        ][
                            1
                        ]  # this is dict object with keys => dict_keys(['langgraph_step', 'langgraph_node', 'langgraph_triggers', 'langgraph_path', 'langgraph_checkpoint_ns', 'checkpoint_ns', 'ls_provider', 'ls_model_name', 'ls_model_type', 'ls_temperature'])

                        # Get the AI message from the LLM.
                        message_from_llm = chunk[
                            1
                        ][
                            0
                        ]  # AIMessageChunk object -> https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessageChunk.html

                        # Handle tuple format (node, value)
                        node, value = chunk
                        if value is not None:
                            # Log the streaming output
                            logger.info(
                                f"[{request_id}] Stream update from {langgraph_node_info['langgraph_node']}: {str(message_from_llm)[:100]}..."
                            )

                            # Send streaming update for React frontend
                            yield (
                                json.dumps(
                                    {
                                        "type": "update",
                                        "node": langgraph_node_info["langgraph_node"],
                                        "value": str(
                                            message_from_llm.content
                                        ),  # Convert value to string for safety
                                    }
                                )
                                + "\n"
                            )

                    elif is_this_chunk_an_update_stream_type:
                        updated_langgraph_state_object = chunk[1]  # Dict object

                        node_step_name = list(
                            chunk[1].keys()
                        )[
                            -1
                        ]  # will be one of the following:'route_initial_user_message', 'respond_naturally', 'design_and_plan', 'write_html_code'

                        node, value = chunk
                        if updated_langgraph_state_object is not None:
                            # Log the streaming output
                            logger.info(
                                f"[{request_id}] Stream update from {node}: {str(value)[:100]}..."
                            )

                            # Store final state for the final response
                            if "messages" in updated_langgraph_state_object:
                                final_state = updated_langgraph_state_object

                    else:
                        # Handle other formats or just log
                        logger.info(
                            f"[{request_id}] Received chunk in unknown format: {type(chunk)}"
                        )
        except Exception as e:
            logger.error(f"[{request_id}] Error in stream: {str(e)}", exc_info=True)
            yield (
                json.dumps({"type": "error", "error": str(e), "request_id": request_id})
                + "\n"
            )
        finally:
            logger.info(f"[{request_id}] Stream completed")
            # Send final update with complete messages
            yield (
                json.dumps(
                    {
                        "type": "final",
                        "node": "final",
                        "value": "final",
                        "messages": final_state.get("messages", [])
                        if final_state
                        else [],
                    }
                )
                + "\n"
            )

    # Return a streaming response
    return StreamingResponse(response_generator(), media_type="text/event-stream")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await WebSocketHandler(websocket, manager).handle_websocket()


@app.get("/chat", response_class=HTMLResponse)
async def chat():
    with open("chat.html") as f:
        return f.read()


@app.get("/page", response_class=HTMLResponse)
async def page():
    with open("page.html") as f:
        return f.read()


@app.get("/conversations", response_class=HTMLResponse)
async def conversations():
    with open("conversations.html") as f:
        return f.read()


@app.get("/threads", response_class=JSONResponse)
async def threads():
    checkpointer = get_or_create_checkpointer()
    config = {}
    checkpoint_generator = checkpointer.list(config=config)
    all_checkpoints: list[CheckpointTuple] = list(
        checkpoint_generator
    )  # convert to list

    # reduce only to the unique thread_ids
    unique_thread_ids = list(
        set(
            [
                checkpoint[0]["configurable"]["thread_id"]
                for checkpoint in all_checkpoints
            ]
        )
    )
    state_history = []
    for thread_id in unique_thread_ids:
        graph = build_workflow(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        state_history.append(
            {"thread_id": thread_id, "state": graph.get_state(config=config)}
        )
    return state_history


@app.get("/chat-history/{thread_id}")
async def chat_history(thread_id: str):
    checkpointer = get_or_create_checkpointer()
    graph = build_workflow(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    state_history = graph.get_state(config=config)
    print(state_history)
    return state_history


@app.get("/available-agents", response_class=JSONResponse)
async def available_agents():
    # map from langgraph.json to a list of agent names
    with open("../langgraph.json", "r") as f:
        langgraph_json = json.load(f)
    return {"agents": list(langgraph_json["graphs"].keys())}
