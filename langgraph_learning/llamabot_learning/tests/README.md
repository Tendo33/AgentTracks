# Backend Tests for LlamaBot

This directory contains the test suite for the LlamaBot backend application.

## Test Structure

```
tests/
├── conftest.py          # Test fixtures and configuration
├── test_app.py          # Main FastAPI application tests
├── test_websocket.py    # WebSocket functionality tests
├── test_agents.py       # Agent functionality tests
├── test_integration.py  # Integration tests
└── README.md           # This file
```

## Test Categories

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution

### Integration Tests
- Test complete workflows and interactions
- Test multiple components working together
- May use real or mocked services

### WebSocket Tests
- Test WebSocket connection management
- Test message handling
- Test real-time communication

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

### Using the Test Runner Script

The `run_tests.py` script provides convenient options:

```bash
# Run all tests
python run_tests.py all

# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run only WebSocket tests
python run_tests.py websocket

# Run with coverage report
python run_tests.py coverage

# Run specific test file
python run_tests.py --file test_app.py

# Run with verbose output
python run_tests.py all --verbose
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.websocket` - WebSocket-related tests
- `@pytest.mark.slow` - Tests that take longer to run

Run specific test categories:
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports

Generate coverage reports:
```bash
pytest --cov=app --cov=agents --cov=websocket --cov-report=html
```

This creates an HTML coverage report in `htmlcov/index.html`.

Terminal coverage report:
```bash
pytest --cov=app --cov=agents --cov=websocket --cov-report=term-missing
```

## Test Configuration

### pytest.ini
The `pytest.ini` file contains default pytest configuration:
- Test discovery patterns
- Default options
- Warning filters
- Test markers

### conftest.py
Contains shared fixtures:
- `async_client` - HTTP client for testing FastAPI endpoints
- `mock_checkpointer` - Mock database checkpointer
- `mock_llm` - Mock LLM client
- `mock_websocket_manager` - Mock WebSocket manager
- Environment setup and teardown

## Writing New Tests

### Test File Naming
- Test files should start with `test_`
- Test functions should start with `test_`
- Test classes should start with `Test`

### Example Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock

class TestMyFeature:
    """Test my feature functionality."""
    
    @pytest.mark.asyncio
    async def test_my_async_function(self, async_client):
        """Test my async function."""
        response = await async_client.get("/my-endpoint")
        assert response.status_code == 200
    
    def test_my_sync_function(self):
        """Test my sync function."""
        result = my_sync_function("input")
        assert result == "expected_output"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_flow(self, async_client, mock_build_workflow):
        """Test complete integration flow."""
        # Integration test code here
        pass
```

### Testing Guidelines

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (APIs, databases, etc.)
3. **Assertions**: Use clear, descriptive assertions
4. **Documentation**: Document test purpose and expectations
5. **Edge Cases**: Test both happy path and error conditions

### Common Patterns

#### Testing FastAPI Endpoints
```python
@pytest.mark.asyncio
async def test_endpoint(self, async_client):
    response = await async_client.get("/endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_key" in data
```

#### Testing with Mocks
```python
@patch('module.external_function')
def test_with_mock(self, mock_external):
    mock_external.return_value = "mocked_result"
    result = my_function()
    assert result == "expected_result"
    mock_external.assert_called_once()
```

#### Testing WebSocket
```python
def test_websocket(self):
    from fastapi.testclient import TestClient
    from app import app
    
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("test message")
        response = websocket.receive_text()
        assert response is not None
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running tests from the backend directory
   - Check Python path in conftest.py

2. **Async Test Issues**
   - Use `@pytest.mark.asyncio` for async tests
   - Ensure `pytest-asyncio` is installed

3. **Mock Issues**
   - Check mock patch paths
   - Verify mock return values and side effects

4. **WebSocket Test Issues**
   - WebSocket tests may be flaky in CI environments
   - Consider using timeouts and error handling

### Debugging Tests

Run tests with more verbose output:
```bash
pytest -vvv --tb=long
```

Run a single test with debugging:
```bash
pytest tests/test_app.py::TestMainEndpoints::test_root_endpoint -vvv
```

Use `pytest.set_trace()` for debugging:
```python
def test_my_function():
    pytest.set_trace()  # Drops into debugger
    result = my_function()
    assert result == expected
```

## CI/CD Integration

The test suite is designed to work in CI/CD environments:

- All external dependencies are mocked
- Tests are isolated and deterministic
- Coverage reports can be generated
- Different test categories can be run separately

Example GitHub Actions workflow:
```yaml
- name: Run tests
  run: |
    cd backend
    pytest --cov=app --cov=agents --cov=websocket --cov-report=xml
``` 