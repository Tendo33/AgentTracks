from agents.base_agent import BaseAgent
from langsmith import Client
import os
from langchain import hub
from agents.write_html_agent.state import State
from langchain.schema import HumanMessage


class RespondNaturally(BaseAgent):
    def __init__(self):
        super().__init__(
            "Respond Naturally Agent",
            "A agent that responds naturally to a user's message.",
        )

    def run(self, user_message: str, existing_html_content: str) -> str:
        prompt = hub.pull("llamabot/respond_to_user")
        prompt_value = prompt.invoke(
            {
                "user_message": user_message,
                "existing_html_content": existing_html_content,
            }
        )
        intent_response = self.invoke(prompt_value)
        return intent_response.content


def respond_naturally_node(state: State) -> State:
    agent = RespondNaturally()
    return_response = agent.run(
        state.get("initial_user_message"), state.get("existing_html_content")
    )

    # Get existing messages or empty list if none
    existing_messages = state.get("messages", [])

    return {"messages": existing_messages + [HumanMessage(content=return_response)]}


if __name__ == "__main__":
    agent = RespondNaturally()
    print(agent.run("Hello, world!", ""))
