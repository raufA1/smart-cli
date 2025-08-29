"""Basic tests for Smart CLI functionality."""

import pytest
import tempfile
import os
from pathlib import Path


def test_project_structure():
    """Test that essential project files exist."""
    project_root = Path(__file__).parent.parent
    
    # Essential files should exist
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "README.md").exists()
    assert (project_root / "src").exists()
    assert (project_root / "src" / "smart_cli.py").exists()
    assert (project_root / "src" / "cli.py").exists()


def test_imports():
    """Test that core modules can be imported."""
    try:
        from src.utils.config import ConfigManager
        from src.utils.simple_ai_client import SimpleOpenRouterClient
        from src.templates import TemplateManager
        from src.agents.orchestrator import SmartCLIOrchestrator
        from src.smart_cli import SmartCLI
        print("✅ All imports successful")
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_config_manager_basic():
    """Basic test for ConfigManager."""
    from src.utils.config import ConfigManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ConfigManager(Path(temp_dir))
        
        # Test basic functionality
        config.set_config("test_key", "test_value")
        assert config.get_config("test_key") == "test_value"
        
        # Test default values
        assert config.get_config("nonexistent", "default") == "default"


def test_template_manager_basic():
    """Basic test for TemplateManager."""
    from src.templates import TemplateManager
    
    template_manager = TemplateManager()
    
    # Test basic functionality
    templates = template_manager.list_templates()
    assert len(templates) > 0
    
    # Test specific template exists
    python_template = template_manager.get_template("python_basic")
    assert python_template is not None
    assert python_template.name == "python_basic"


def test_ai_client_initialization():
    """Test AI client can be initialized."""
    from src.utils.simple_ai_client import SimpleOpenRouterClient
    from src.utils.config import ConfigManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ConfigManager(Path(temp_dir))
        
        # Should be able to create client (even without API key)
        client = SimpleOpenRouterClient(config)
        assert client is not None
        assert client.config_manager is config


def test_smart_cli_initialization():
    """Test Smart CLI can be initialized.""" 
    from src.smart_cli import SmartCLI
    
    # Should be able to create SmartCLI instance
    smart_cli = SmartCLI(debug=True)
    assert smart_cli is not None
    assert smart_cli.debug is True


@pytest.mark.asyncio
async def test_smart_cli_async_init():
    """Test Smart CLI async initialization."""
    from src.smart_cli import SmartCLI
    
    smart_cli = SmartCLI(debug=True)
    
    # Should be able to initialize (even if some components fail)
    result = await smart_cli.initialize()
    assert isinstance(result, bool)


def test_agent_creation():
    """Test that agents can be created."""
    from src.agents.analyzer_agent import AnalyzerAgent
    from src.agents.modifier_agent import ModifierAgent
    from src.agents.orchestrator import SmartCLIOrchestrator
    from src.utils.config import ConfigManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ConfigManager(Path(temp_dir))
        
        # Should be able to create agents
        analyzer = AnalyzerAgent(config_manager=config)
        modifier = ModifierAgent(config_manager=config) 
        orchestrator = SmartCLIOrchestrator(config_manager=config)
        
        assert analyzer is not None
        assert modifier is not None  
        assert orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])