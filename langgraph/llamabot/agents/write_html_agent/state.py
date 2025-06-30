from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain.schema import BaseMessage


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    initial_user_message: str
    existing_html_content: str
    final_html_content: str
    design_plan: str
