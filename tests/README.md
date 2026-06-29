# Tests

This directory contains unit and integration tests for the MCP MetaTrader 5 Server.

## Running Tests

### Install Test Dependencies

```bash
uv sync --extra dev
```

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test Files

```bash
# Test timeframe validation
uv run pytest tests/test_timeframes.py

# Test connection management
uv run pytest tests/test_connection.py

# Test account info
uv run pytest tests/test_account_info.py

# Test Pydantic models
uv run pytest tests/test_models.py
```

### Run Tests by Marker

```bash
# Run only unit tests (don't require MT5)
uv run pytest -m unit

# Run only integration tests (require MT5 connection)
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

### Run with Coverage

```bash
# Generate coverage report
uv run pytest --cov=mcp_mt5 --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Run with Verbose Output

```bash
uv run pytest -v
```

### Run Specific Test

```bash
uv run pytest tests/test_timeframes.py::TestTimeframeValidation::test_valid_timeframe_conversion
```

## Test Structure

### Unit Tests (`@pytest.mark.unit`)
- Don't require MT5 connection
- Use mocks for MT5 functions
- Fast execution
- Test individual functions in isolation

### Integration Tests (`@pytest.mark.integration`)
- Require actual MT5 connection
- Test real MT5 interactions
- Slower execution
- Require MT5 terminal to be running

### Test Files

- `conftest.py` - Shared fixtures and configuration
- `test_timeframes.py` - Timeframe validation and conversion
- `test_connection.py` - Connection management (initialize, login, shutdown)
- `test_account_info.py` - Account and terminal information
- `test_models.py` - Pydantic model validation

## Writing New Tests

### Example Unit Test

```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
def test_my_function():
    """Test description."""
    # Arrange
    expected = "result"
    
    # Act
    result = my_function()
    
    # Assert
    assert result == expected
```

### Example Integration Test

```python
import pytest

@pytest.mark.integration
def test_mt5_connection():
    """Test actual MT5 connection."""
    # This test requires MT5 to be running
    result = initialize(path="")
    assert result is True
```

## Continuous Integration

Tests are automatically run on GitHub Actions for:
- Pull requests
- Pushes to main branch
- Tagged releases

## Coverage Goals

- **Target**: 80%+ code coverage
- **Current**: Run `pytest --cov` to see current coverage
- Focus on critical paths and error handling

## Disclaimer

This software/model context protocol/author is not liable for any financial losses resulting from the use of the tools provided. Use at your own risk.
