import json
from typing import Annotated

import requests
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import InjectedState, ToolNode, tools_condition

load_dotenv()


class LlamaBotState(MessagesState):
    api_token: str
    agent_instructions: str


# Tools
@tool
def run_rails_console_command(
    rails_console_command: str,
    message_to_user: str,
    internal_thoughts: str,
    state: Annotated[LlamaBotState, InjectedState],
) -> str:
    """
    Run a Rails console command.
    Message to user is a string to tell the user what you're doing.
    Internal thoughts are your thoughts about the command.
    State is the state of the agent.
    """
    print(
        "API TOKEN", state.get("api_token")
    )  # empty. only messages is getting passed through.

    # Configuration
    RAILS_SERVER_URL = "http://localhost:3000"
    API_ENDPOINT = f"{RAILS_SERVER_URL}/llama_bot/agent/command"

    try:
        # Make HTTP request to Rails AP
        response = requests.post(
            API_ENDPOINT,
            json={"command": rails_console_command},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {state.get('api_token')}",
            },
            timeout=30,  # 30 second timeout
        )

        # Parse the response
        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            result_type = data.get("type")

            # Format the output nicely
            if isinstance(result, (list, dict)):
                formatted_result = json.dumps(result, indent=2, default=str)
            else:
                formatted_result = str(result)

            # Create a JSON-serializable dictionary
            result_data = {
                "command": rails_console_command,
                "result": formatted_result,
                "type": result_type,
            }

            # Serialize to JSON string for safe transmission
            return json.dumps(result_data, ensure_ascii=False, indent=2)
        elif response.status_code == 403:
            error_data = response.json()
            return f"Error: {error_data.get('error', 'Command not allowed')}"

        elif response.status_code == 500:
            error_data = response.json()
            return f"Rails Error: {error_data.get('error', 'Unknown error')}\nType: {error_data.get('type', 'Unknown')}"

        else:
            return f"HTTP Error {response.status_code}: {response.text}"

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Rails server. Make sure your Rails app is running on http://localhost:3000"

    except requests.exceptions.Timeout:
        return "Error: Request timed out. The Rails command may be taking too long to execute."

    except requests.exceptions.RequestException as e:
        return f"Request Error: {str(e)}"

    except json.JSONDecodeError:
        return (
            f"Error: Invalid JSON response from server. Raw response: {response.text}"
        )

    except Exception as e:
        return f"Unexpected Error: {str(e)}"


# Global tools list
tools = [run_rails_console_command]


# Node
def llamabot(state: LlamaBotState):
    additional_instructions = state.get("agent_instructions")

    # System message
    sys_msg = SystemMessage(
        content=f"""You are LlamaBot, a helpful AI assistant.
                        In normal chat conversations, feel free to implement markdown formatting to make your responses more readable, if it's appropriate.
                        Here are additional instructions provided by the user: <USER_INSTRUCTIONS> {additional_instructions} </USER_INSTRUCTIONS>"""
    )

    llm = ChatOpenAI(model="o4-mini")
    llm_with_tools = llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


def build_workflow(checkpointer=None):
    # Graph
    builder = StateGraph(LlamaBotState)

    # Define nodes: these do the work
    builder.add_node("llamabot", llamabot)
    builder.add_node("tools", ToolNode(tools))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "llamabot")
    builder.add_conditional_edges(
        "llamabot",
        # If the latest message (result) from llamabot is a tool call -> tools_condition routes to tools
        # If the latest message (result) from llamabot is a not a tool call -> tools_condition routes to END
        tools_condition,
    )
    builder.add_edge("tools", "llamabot")

    react_graph = builder.compile(checkpointer=checkpointer)

    return react_graph
