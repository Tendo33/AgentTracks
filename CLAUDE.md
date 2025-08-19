# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentTracks is an educational learning project for understanding and comparing AI agent frameworks. This project helps developers learn different approaches to building intelligent agents using various libraries and frameworks including LangGraph, Pydantic AI, Agno, OpenAI Agents SDK, and PocketFlow through hands-on examples and comparisons.

## Development Environment

### Setup Commands
```bash
# Install uv package manager
pip install uv

# Clone and setup
git clone https://github.com/Tendo33/AgentTracks.git
cd AgentTracks
uv sync

# Create .env file with OpenAI credentials
OPENAI_API_KEY="xxx"
OPENAI_API_BASE="xxx"
```

### Running the Application
```bash
# Main application (LangGraph-based)
cd langgraph/llamabot
python app.py

# Run individual agent examples
cd agno && python 0.1_research_agent.py
cd pydantic_ai && python 01_agent_demo.py
cd openai_agents_sdk && python 02_first_agent.py
cd pocketflow && python main.py
```

### Testing
```bash
# From langgraph/llamabot directory
python run_tests.py all                    # Run all tests
python run_tests.py unit                  # Run unit tests only
python run_tests.py integration           # Run integration tests only
python run_tests.py websocket             # Run WebSocket tests only
python run_tests.py coverage              # Run with coverage report
python run_tests.py --file test_app.py   # Run specific test file

# Direct pytest usage
pytest tests/
pytest -m unit                           # Run only unit tests
pytest -m integration                   # Run only integration tests
pytest --cov=app --cov=agents --cov=websocket --cov-report=html
```

## Architecture Overview

### Core Components

1. **LangGraph Implementation** (`langgraph/llamabot/`)
   - Complete learning example with FastAPI and WebSocket support
   - Multiple agent patterns: React Agent, Write HTML Agent, Sequential workflows
   - State management and persistence examples
   - Real-time streaming response handling
   - Comprehensive test suite for learning testing patterns

2. **Agent Framework Learning Examples**
   - **Agno**: Multi-agent collaboration and research patterns
   - **Pydantic AI**: Type-safe agents and tool integration examples
   - **OpenAI Agents SDK**: Official framework basics and quick start
   - **PocketFlow**: Lightweight workflow and RAG implementation examples

3. **Learning Infrastructure**
   - **Chainlit**: UI interface examples for agent interactions
   - **WebSocket System**: Real-time communication patterns
   - **Testing Framework**: Comprehensive testing examples and patterns

### Learning Patterns and Concepts

#### LangGraph Workflow Patterns
- StateGraph orchestration and state management
- Different checkpointer strategies for persistence
- Conversation thread management
- Streaming response patterns for real-time updates

#### Agent Design Patterns
- Base agent abstractions and common patterns
- Specialized agent implementations for different use cases
- Tool integration and external system interactions
- Conditional routing and decision-making patterns

#### Communication Patterns
- Real-time update mechanisms
- Bidirectional communication designs
- Cross-framework integration approaches
- Context management strategies

### Learning Project Structure

```
AgentTracks/
├── langgraph/llamabot/          # Complete LangGraph learning project
│   ├── agents/                  # Agent pattern examples
│   │   ├── base_agent.py        # Base agent abstraction pattern
│   │   ├── react_agent/         # ReAct pattern implementation
│   │   ├── write_html_agent/    # Sequential workflow pattern
│   │   └── utils/               # Shared utility patterns
│   ├── websocket/               # Real-time communication patterns
│   ├── tests/                   # Testing patterns and examples
│   ├── app.py                   # Complete application example
│   └── run_tests.py             # Test runner pattern
├── agno/                        # Multi-agent collaboration examples
├── pydantic_ai/                 # Type-safe agent examples
├── openai_agents_sdk/           # Official framework basics
├── pocketflow/                  # Lightweight workflow examples
└── chainlit/                    # UI interface examples
```

## Learning and Development Guidelines

### Agent Learning Patterns
- Study `BaseAgent` class to understand common abstractions
- Examine LangGraph StateGraph for workflow orchestration
- Learn error handling and logging patterns from examples
- Compare different agent implementations to understand trade-offs

### Testing for Learning
- Study the comprehensive test suite to understand testing patterns
- Learn pytest markers for test organization (`@pytest.mark.unit`, `@pytest.mark.integration`)
- Understand mocking strategies for external dependencies
- Examine WebSocket testing patterns for real-time features
- Use the test examples as learning resources for your own projects

### API Pattern Learning
- Study FastAPI implementation patterns from the examples
- Learn CORS configuration for frontend integration
- Examine Pydantic model usage for request/response validation
- Understand logging and error handling patterns
- Compare REST vs WebSocket communication approaches

### Configuration Management Patterns
- Learn environment variable usage for configuration
- Study fallback mechanisms for optional dependencies
- Understand development vs production configuration strategies
- Examine `.env` file patterns for local development

## Learning Project Notes

- The main application uses `o4-mini` OpenAI model by default for cost-effective learning
- PostgreSQL connection is optional - falls back to MemorySaver for easier setup
- WebSocket system demonstrates real-time communication patterns
- All agent implementations showcase different approaches to common problems
- The project is designed primarily for learning, with working examples as educational resources
- Focus is on understanding concepts and patterns rather than production deployment