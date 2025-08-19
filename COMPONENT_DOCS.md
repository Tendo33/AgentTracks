# AgentTracks Component Documentation

## Table of Contents
- [WebSocket Communication System](#websocket-communication-system)
- [LangGraph Workflow Architecture](#langgraph-workflow-architecture)
- [Agent Implementation Patterns](#agent-implementation-patterns)
- [Testing Infrastructure](#testing-infrastructure)
- [Base Agent Framework](#base-agent-framework)

## WebSocket Communication System

### Location: `langgraph/llamabot/app.py`

The WebSocket system provides real-time streaming responses for agent interactions.

#### Key Components:

```python
# Connection Manager
class ConnectionManager:
    async def connect(self, websocket: WebSocket, request_id: str)
    async def disconnect(self, request_id: str)
    async def send_personal_message(self, message: str, request_id: str)
    async def broadcast(self, message: str)

# Streaming Response Generator
async def response_generator():
    final_state = None
    try:
        logger.info(f"[{request_id}] Starting streaming response")
        yield json.dumps({"type": "start", "request_id": request_id}) + "\n"
        
        # Process through LangGraph workflow
        for event in workflow.stream(input_data, config):
            if event["event"] == "on_chain_start":
                yield json.dumps({
                    "type": "agent_start",
                    "agent": event["data"]["input"]["agent"],
                    "request_id": request_id
                }) + "\n"
            
            if event["event"] == "on_chain_end":
                yield json.dumps({
                    "type": "agent_end", 
                    "agent": event["data"]["output"]["agent"],
                    "request_id": request_id
                }) + "\n"
                
        yield json.dumps({
            "type": "final_response",
            "response": final_state,
            "request_id": request_id
        }) + "\n"
        
    except Exception as e:
        logger.error(f"[{request_id}] Error in stream: {str(e)}", exc_info=True)
        yield json.dumps({
            "type": "error",
            "error": str(e),
            "request_id": request_id
        }) + "\n"
```

#### WebSocket Events:
- `start`: Connection established
- `agent_start`: Agent begins processing
- `agent_end`: Agent completes processing
- `final_response`: Complete workflow result
- `error`: Processing error

## LangGraph Workflow Architecture

### Core Pattern: StateGraph with Conditional Routing

#### Basic Workflow Structure:
```python
def build_workflow():
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("agent_node", agent_function)
    graph_builder.add_node("tool_node", ToolNode(tools))
    
    # Define flow
    graph_builder.add_edge(START, "agent_node")
    graph_builder.add_conditional_edges(
        "agent_node",
        lambda x: x["next"],
        {
            "continue": "tool_node",
            "end": END
        }
    )
    graph_builder.add_edge("tool_node", "agent_node")
    
    return graph_builder.compile()
```

### State Management:
```python
class State(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], add_messages]
    next: str
    context: Dict[str, Any]
```

## Agent Implementation Patterns

### 1. React Agent Pattern (`react_agent/nodes.py`)

**Purpose**: Tool-using agent with conditional routing

**Key Features**:
- Dynamic tool binding
- Conditional routing based on tool calls
- Persistent conversation state

```python
def software_developer_assistant(state: MessagesState):
    llm = ChatOpenAI(model="o4-mini")
    llm_with_tools = llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

def build_workflow(checkpointer=None):
    builder = StateGraph(MessagesState)
    builder.add_node("software_developer_assistant", software_developer_assistant)
    builder.add_node("tools", ToolNode(tools))
    
    builder.add_edge(START, "software_developer_assistant")
    builder.add_conditional_edges(
        "software_developer_assistant",
        tools_condition,
    )
    builder.add_edge("tools", "software_developer_assistant")
    
    return builder.compile(checkpointer=checkpointer)
```

### 2. Write HTML Agent Pattern (`write_html_agent/nodes.py`)

**Purpose**: Sequential workflow for HTML generation tasks

**Key Features**:
- Sequential node execution
- State-based routing
- Multi-step processing

```python
def build_workflow():
    graph_builder = StateGraph(State)
    
    # Add nodes in sequence
    graph_builder.add_node("route_initial_user_message", route_initial_user_message_node)
    graph_builder.add_node("respond_naturally", respond_naturally_node)
    graph_builder.add_node("design_and_plan", design_and_plan_node)
    graph_builder.add_node("write_html_code", write_html_code_node)
    
    # Define flow
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
    
    return graph_builder.compile()
```

## Testing Infrastructure

### Test Runner (`run_tests.py`)

**Purpose**: Comprehensive test execution with different test types

**Features**:
- Multiple test categories (unit, integration, websocket, coverage)
- Command-line interface
- Coverage reporting

```python
def run_with_coverage():
    return run_command([
        "pytest",
        "tests/",
        "--cov=app",
        "--cov=agents", 
        "--cov=websocket",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
```

### Test Categories:
- **Unit Tests**: Individual component testing
- **Integration Tests**: Full workflow testing
- **WebSocket Tests**: Real-time communication testing
- **Coverage**: Code coverage analysis

### Usage:
```bash
# Run all tests
python run_tests.py all

# Run specific test type
python run_tests.py unit
python run_tests.py integration
python run_tests.py websocket

# Run with coverage
python run_tests.py coverage

# Run specific file
python run_tests.py --file test_app.py
```

## Base Agent Framework

### Base Agent Class (`base_agent.py`)

**Purpose**: Abstract base class for all agent implementations

**Features**:
- Common LLM initialization
- Abstract method enforcement
- Standardized interface

```python
class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
        load_dotenv()
        self.llm = ChatOpenAI(model="o4-mini")
    
    @abstractmethod
    def run(self, input: str) -> str:
        pass
    
    def invoke(self, input: str) -> str:
        return self.llm.invoke(input)
```

### Usage Pattern:
```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="my_agent",
            description="Custom agent implementation"
        )
    
    def run(self, input: str) -> str:
        # Custom implementation
        return self.invoke(input)
```

## Tool Integration

### Tool Definition Pattern:
```python
@tool
def write_html(html_code: str) -> str:
    """Write HTML code to a file."""
    with open("page.html", "w") as f:
        f.write(html_code)
    return "HTML code written to page.html"
```

### Tool Registration:
```python
tools = [
    write_html,
    write_css,
    write_javascript,
    get_screenshot_and_html_content_using_playwright,
]
```

## Configuration and Setup

### Environment Variables:
- `OPENAI_API_KEY`: OpenAI API authentication
- `DATABASE_URL`: PostgreSQL connection (for persistence)
- `LOG_LEVEL`: Logging verbosity

### Dependencies:
- `langgraph`: Workflow orchestration
- `langchain-openai`: LLM integration
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pytest`: Testing framework

## Best Practices

1. **State Management**: Use TypedDict for clear state definitions
2. **Error Handling**: Implement comprehensive error handling in workflows
3. **Testing**: Write tests for all components and workflows
4. **Logging**: Use structured logging with request IDs
5. **Modularity**: Keep agents modular and reusable
6. **Documentation**: Document all tools and workflows

## Common Patterns

### 1. Streaming Response Pattern
```python
async def response_generator():
    try:
        yield json.dumps({"type": "start"}) + "\n"
        # Process workflow
        for event in workflow.stream(input_data):
            yield json.dumps({"type": "event", "data": event}) + "\n"
        yield json.dumps({"type": "final"}) + "\n"
    except Exception as e:
        yield json.dumps({"type": "error", "error": str(e)}) + "\n"
```

### 2. Tool Integration Pattern
```python
@tool
def my_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    return result

# Register with agent
llm_with_tools = llm.bind_tools([my_tool])
```

### 3. Workflow Builder Pattern
```python
def build_workflow():
    builder = StateGraph(State)
    builder.add_node("node1", node1_function)
    builder.add_node("node2", node2_function)
    
    builder.add_edge(START, "node1")
    builder.add_conditional_edges("node1", routing_function)
    builder.add_edge("node2", END)
    
    return builder.compile()
```