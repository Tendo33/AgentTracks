from agents.base_agent import BaseAgent
from agents.write_html_agent.state import State
from langchain import hub


class RouteInitialUserMessage(BaseAgent):
    def __init__(self):
        super().__init__(
            "Route Initial User Message Agent",
            "A agent that routes the initial user message to the appropriate agent.",
        )

    def run(self, user_message: str, existing_html_content: str) -> str:
        prompt = hub.pull("llamabot/determine_user_intent")
        prompt_value = prompt.invoke(
            {
                "user_message": user_message,
                "existing_html_content": existing_html_content,
            }
        )
        intent_response = self.invoke(prompt_value)
        return intent_response.content


def route_initial_user_message_node(state: State) -> State:
    agent = RouteInitialUserMessage()
    user_intent = agent.run(
        state.get("initial_user_message"), state.get("existing_html_content")
    )

    if user_intent == "WRITE_CODE":
        return {"next": "design_and_plan"}
    else:
        return {"next": "respond_naturally"}


if __name__ == "__main__":
    agent = RouteInitialUserMessage()
    print(agent.run("Hello, world!", ""))
