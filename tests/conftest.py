"""Test configuration and fixtures for Smart CLI."""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import shutil
from typer.testing import CliRunner

from src.cli import app
from src.utils.config import ConfigManager


@pytest.fixture
def cli_runner():
    """Provide CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_config_dir():
    """Provide temporary config directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config_manager(temp_config_dir):
    """Provide mock configuration manager."""
    config_manager = ConfigManager(config_dir=temp_config_dir)
    
    # Set some default test configuration
    test_config = {
        'default_model': 'test-model',
        'temperature': 0.7,
        'max_tokens': 1000,
        'cache_enabled': False,
        'log_level': 'DEBUG'
    }
    
    for key, value in test_config.items():
        config_manager.set_config(key, value)
    
    return config_manager


@pytest.fixture
def mock_ai_client():
    """Provide mock AI client."""
    client = Mock()
    client.generate_response = AsyncMock(return_value={
        "choices": [{"message": {"content": "Mock AI response"}}],
        "usage": {"total_tokens": 100}
    })
    return client


@pytest.fixture
def sample_python_code():
    """Provide sample Python code for testing."""
    return '''
def fibonacci(n):
    """Calculate fibonacci sequence up to n."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result


if __name__ == "__main__":
    result = fibonacci(10)
    calc = Calculator()
    sum_result = calc.add(5, 3)
    print(f"Fibonacci(10): {result}")
    print(f"5 + 3 = {sum_result}")
'''


@pytest.fixture
def sample_javascript_code():
    """Provide sample JavaScript code for testing."""
    return '''
function fibonacci(n) {
    /**
     * Calculate fibonacci sequence up to n.
     */
    if (n <= 1) {
        return n;
    }
    return fibonacci(n-1) + fibonacci(n-2);
}

class Calculator {
    /**
     * Simple calculator class.
     */
    
    constructor() {
        this.history = [];
    }
    
    add(a, b) {
        /**
         * Add two numbers.
         */
        const result = a + b;
        this.history.push(`${a} + ${b} = ${result}`);
        return result;
    }
}

// Usage example
const result = fibonacci(10);
const calc = new Calculator();
const sumResult = calc.add(5, 3);
console.log(`Fibonacci(10): ${result}`);
console.log(`5 + 3 = ${sumResult}`);
'''


@pytest.fixture
def sample_project_structure(temp_dir):
    """Create a sample project structure for testing."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()
    
    # Create directory structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()
    
    # Create files
    (project_dir / "README.md").write_text("# Test Project")
    (project_dir / ".gitignore").write_text("*.pyc\n__pycache__/")
    (project_dir / "requirements.txt").write_text("pytest>=7.0.0")
    
    # Create Python files
    (project_dir / "src" / "main.py").write_text('''
def main():
    """Main function."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')
    
    (project_dir / "tests" / "test_main.py").write_text('''
import pytest
from src.main import main

def test_main():
    """Test main function."""
    # This would normally capture output
    main()
''')
    
    return project_dir


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for tests."""
    # Clear any existing environment variables that might affect tests
    env_vars_to_clear = [
        'OPENROUTER_API_KEY',
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'REDIS_URL',
        'DATABASE_URL',
        'LOG_LEVEL',
    ]
    
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    
    # Set test-specific environment variables
    monkeypatch.setenv('SMART_CLI_TEST_MODE', 'true')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, status=200, json_data=None, text_data=""):
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data
    
    async def json(self):
        return self._json_data
    
    async def text(self):
        return self._text_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_aiohttp_session():
    """Provide mock aiohttp session."""
    session = Mock()
    session.post = Mock(return_value=MockResponse())
    session.get = Mock(return_value=MockResponse())
    
    # Mock context manager behavior
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    return session


# Async test utilities
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test markers for different test categories
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-focused tests"
    )
    config.addinivalue_line(
        "markers", "ai: marks tests that require AI API calls"
    )