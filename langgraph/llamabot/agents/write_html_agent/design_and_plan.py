from agents.base_agent import BaseAgent
from agents.write_html_agent.state import State
from langchain import hub


class DesignAndPlan(BaseAgent):
    def __init__(self):
        super().__init__(
            "Design and Plan Agent",
            "A design and plan agent that designs and plans a project.",
        )

    def run(self, user_message: str, existing_html_content: str) -> str:
        prompt = hub.pull("llamabot/design_planning_prompt")
        prompt_value = prompt.invoke(
            {
                "user_message": user_message,
                "existing_html_content": existing_html_content,
            }
        )
        intent_response = self.invoke(prompt_value)
        return intent_response.content


def design_and_plan_node(state: State) -> State:
    agent = DesignAndPlan()
    design_plan = agent.run(
        state.get("initial_user_message"), state.get("existing_html_content")
    )

    return {"design_plan": design_plan}


if __name__ == "__main__":
    agent = DesignAndPlan()
    print(agent.run("Hello, world!", ""))
