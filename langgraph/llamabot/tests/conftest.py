"""
Test configuration and fixtures for the FastAPI application.
"""

import pytest
import pytest_asyncio
import asyncio
import os
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# Add the backend directory to the Python path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app, manager
from langgraph.checkpoint.memory import MemorySaver


@pytest_asyncio.fixture
async def async_client():
    """Create an async HTTP client for testing."""
    async with AsyncClient(base_url="http://test") as client:
        # We need to patch the client to work with our FastAPI app
        from fastapi.testclient import TestClient

        sync_client = TestClient(app)

        # Create a wrapper that mimics AsyncClient but uses TestClient under the hood
        class AsyncClientWrapper:
            def __init__(self, sync_client):
                self._sync_client = sync_client

            async def get(self, url, **kwargs):
                return self._sync_client.get(url, **kwargs)

            async def post(self, url, **kwargs):
                return self._sync_client.post(url, **kwargs)

            async def put(self, url, **kwargs):
                return self._sync_client.put(url, **kwargs)

            async def delete(self, url, **kwargs):
                return self._sync_client.delete(url, **kwargs)

            async def patch(self, url, **kwargs):
                return self._sync_client.patch(url, **kwargs)

        yield AsyncClientWrapper(sync_client)


@pytest.fixture
def mock_checkpointer():
    """Mock checkpointer for testing."""
    return MemorySaver()


@pytest.fixture
def mock_llm():
    """Mock LLM client for testing."""
    mock = AsyncMock()
    mock.stream = AsyncMock()
    return mock


@pytest.fixture
def mock_langsmith_client():
    """Mock LangSmith client for testing."""
    return MagicMock()


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket connection manager."""
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.send_personal_message = AsyncMock()
    mock_manager.broadcast = AsyncMock()
    return mock_manager


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "Hello, this is a test message",
        "thread_id": "test_thread_123",
        "agent": "test_agent",
    }


@pytest.fixture
def mock_html_content():
    """Mock HTML content for testing."""
    return "<html><body><h1>Test Page</h1></body></html>"


@pytest.fixture
def mock_workflow():
    """Mock LangGraph workflow for testing."""
    mock = MagicMock()
    mock.stream = MagicMock()
    mock.get_state = MagicMock()
    return mock


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables and mocks."""
    # Set test environment variables
    os.environ["LANGSMITH_API_KEY"] = "test_api_key"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"

    # Mock the checkpointer to avoid database connections during tests
    with patch("app.get_or_create_checkpointer") as mock_checkpointer:
        mock_checkpointer.return_value = MemorySaver()
        yield


@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.fetchall = AsyncMock(return_value=[])
    mock_db.fetchone = AsyncMock(return_value=None)
    return mock_db


@pytest.fixture
def mock_build_workflow():
    """Mock build_workflow function for testing."""
    with patch("app.build_workflow") as mock:
        workflow = MagicMock()
        workflow.stream = MagicMock(return_value=iter([]))
        workflow.get_state = MagicMock(return_value={"messages": []})
        mock.return_value = workflow
        yield mock
