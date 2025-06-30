
from agents.write_html_agent.design_and_plan import design_and_plan_node
from agents.write_html_agent.respond_naturally import respond_naturally_node
from agents.write_html_agent.route_initial_user_message import (
    route_initial_user_message_node,
)
from agents.write_html_agent.state import State
from agents.write_html_agent.write_html_code import write_html_code_node
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph

load_dotenv()


def build_workflow():
    graph_builder = StateGraph(State)

    llm = ChatOpenAI(model="o4-mini")

    # The first argument is the unique node name
    # The second argument is the function or object that will be called whenever
    # the node is used.
    graph_builder.add_node(
        "route_initial_user_message", route_initial_user_message_node
    )
    graph_builder.add_node("respond_naturally", respond_naturally_node)
    graph_builder.add_node("design_and_plan", design_and_plan_node)
    graph_builder.add_node("write_html_code", write_html_code_node)

    graph_builder.add_edge(START, "route_initial_user_message")

    graph_builder.add_conditional_edges(
        "route_initial_user_message",
        lambda x: x["next"],
        {
            "respond_naturally": "respond_naturally",
            "design_and_plan": "design_and_plan",
        },
    )

    graph_builder.add_edge("design_and_plan", "write_html_code")

    graph = graph_builder.compile()

    return graph


# Only run this code when the file is executed directly
if __name__ == "__main__":
    graph = build_workflow()
    output = graph.invoke(
        {"messages": [HumanMessage(content="Please change this background to white")]}
    )
    print(output)
