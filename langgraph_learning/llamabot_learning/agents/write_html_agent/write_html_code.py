from agents.base_agent import BaseAgent
from agents.write_html_agent.state import State
from langchain import hub
from langchain.schema import HumanMessage


class WriteHtmlCode(BaseAgent):
    def __init__(self):
        super().__init__("Write Html Code Agent", "A agent that writes html code.")

    def run(
        self, user_message: str, existing_html_content: str, design_plan: str
    ) -> str:
        prompt = hub.pull("llamabot/after_planning_generate_html")
        prompt_value = prompt.invoke(
            {
                "user_message": user_message,
                "existing_html_content": existing_html_content,
                "design_plan": design_plan,
            }
        )
        intent_response = self.invoke(prompt_value)
        return intent_response.content


def write_html_code_node(state: State) -> State:
    agent = WriteHtmlCode()
    return_response = agent.run(
        state.get("initial_user_message"),
        state.get("existing_html_content"),
        state.get("design_plan"),
    )

    try:
        with open("page.html", "w") as f:
            f.write(return_response)
    except Exception as write_error:
        raise write_error

    return {
        "final_html_content": return_response,
        "messages": state.get("messages", []) + [HumanMessage(content=return_response)],
    }


if __name__ == "__main__":
    agent = WriteHtmlCode()
    print(agent.run("Hello, world!", "", ""))
