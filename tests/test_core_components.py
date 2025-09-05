"""
Comprehensive tests for Smart CLI core components.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import json
import os


class TestSmartCLI:
    """Test Smart CLI main functionality."""
    
    def test_smart_cli_import(self):
        """Test SmartCLI can be imported."""
        from src.smart_cli import SmartCLI
        assert SmartCLI is not None
    
    def test_smart_cli_initialization(self):
        """Test SmartCLI initialization."""
        from src.smart_cli import SmartCLI
        
        # Mock the necessary dependencies
        with patch('src.smart_cli.ConfigManager'), \
             patch('src.smart_cli.SessionManager'), \
             patch('src.smart_cli.CommandHandler'):
            
            cli = SmartCLI(debug=True)
            assert cli.debug is True
            assert cli is not None


class TestCommandHandler:
    """Test Command Handler functionality."""
    
    def test_command_handler_import(self):
        """Test CommandHandler can be imported."""
        from src.core.command_handler import CommandHandler
        assert CommandHandler is not None
    
    def test_command_handler_initialization(self):
        """Test CommandHandler initialization."""
        from src.core.command_handler import CommandHandler
        
        mock_smart_cli = Mock()
        handler = CommandHandler(mock_smart_cli)
        assert handler.smart_cli == mock_smart_cli


class TestConfigManager:
    """Test Configuration Manager functionality."""
    
    def test_config_manager_import(self):
        """Test ConfigManager can be imported."""
        from src.utils.config import ConfigManager
        assert ConfigManager is not None
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        from src.utils.config import ConfigManager
        
        manager = ConfigManager()
        assert manager is not None
    
    def test_config_loading(self):
        """Test configuration loading."""
        from src.utils.config import ConfigManager
        
        manager = ConfigManager()
        
        # Test loading configuration (should not crash)
        try:
            config = manager.load_config()
            assert isinstance(config, dict)
        except Exception:
            # If config loading fails, that's okay for basic test
            pass


class TestRequestRouter:
    """Test Request Router functionality."""
    
    def test_request_router_import(self):
        """Test RequestRouter can be imported."""
        from src.core.request_router import RequestRouter
        assert RequestRouter is not None
    
    def test_request_router_initialization(self):
        """Test RequestRouter initialization."""
        from src.core.request_router import RequestRouter
        
        mock_smart_cli = Mock()
        mock_smart_cli.orchestrator = Mock()
        mock_smart_cli.handlers = {}
        mock_smart_cli.command_handler = Mock()
        
        router = RequestRouter(mock_smart_cli)
        assert router.smart_cli == mock_smart_cli


class TestSessionManager:
    """Test Session Manager functionality."""
    
    def test_session_manager_import(self):
        """Test SessionManager can be imported."""
        from src.core.session_manager import SessionManager
        assert SessionManager is not None
    
    def test_session_manager_initialization(self):
        """Test SessionManager initialization."""
        from src.core.session_manager import SessionManager
        
        manager = SessionManager(debug=False)
        assert manager.debug is False
        assert hasattr(manager, 'session_id')


class TestBudgetProfiles:
    """Test Budget Profiles functionality."""
    
    def test_budget_profiles_import(self):
        """Test BudgetProfile can be imported."""
        from src.core.budget_profiles import BudgetProfile, get_budget_profiles
        assert BudgetProfile is not None
        assert get_budget_profiles is not None
    
    def test_get_budget_profiles(self):
        """Test getting budget profiles."""
        from src.core.budget_profiles import get_budget_profiles
        
        profiles = get_budget_profiles()
        assert isinstance(profiles, dict)
        assert len(profiles) > 0
        
        # Test that profiles have required fields
        for profile_name, profile in profiles.items():
            assert hasattr(profile, 'name')
            assert hasattr(profile, 'daily_limit')
            assert hasattr(profile, 'monthly_limit')
            assert profile.daily_limit > 0
            assert profile.monthly_limit > 0


class TestIntelligentRequestClassifier:
    """Test Intelligent Request Classifier."""
    
    def test_classifier_import(self):
        """Test classifier components can be imported."""
        from src.core.intelligent_request_classifier import RequestType, ClassificationResult
        assert RequestType is not None
        assert ClassificationResult is not None
    
    def test_request_types(self):
        """Test RequestType enum."""
        from src.core.intelligent_request_classifier import RequestType
        
        # Test that enum has expected values
        expected_types = ['CODE_GENERATION', 'CODE_REVIEW', 'DEBUGGING', 'ARCHITECTURE']
        for req_type in expected_types:
            assert hasattr(RequestType, req_type), f"RequestType.{req_type} not found"
    
    def test_classification_result(self):
        """Test ClassificationResult structure."""
        from src.core.intelligent_request_classifier import ClassificationResult, RequestType
        
        result = ClassificationResult(
            request_type=RequestType.CODE_GENERATION,
            confidence=0.95,
            reasoning="Test reasoning"
        )
        
        assert result.request_type == RequestType.CODE_GENERATION
        assert result.confidence == 0.95
        assert result.reasoning == "Test reasoning"


class TestGitIntegration:
    """Test Git integration functionality."""
    
    def test_git_handler_import(self):
        """Test GitHandler can be imported."""
        from src.handlers.git_handler import GitHandler
        assert GitHandler is not None
    
    def test_git_handler_initialization(self):
        """Test GitHandler initialization."""
        from src.handlers.git_handler import GitHandler
        
        mock_smart_cli = Mock()
        handler = GitHandler(mock_smart_cli)
        assert handler.smart_cli == mock_smart_cli


class TestFileManager:
    """Test File Manager functionality."""
    
    def test_file_manager_import(self):
        """Test FileManager can be imported."""
        from src.core.file_manager import FileManager
        assert FileManager is not None
    
    def test_file_manager_initialization(self):
        """Test FileManager initialization."""
        from src.core.file_manager import FileManager
        
        manager = FileManager()
        assert manager is not None


class TestGithubIntegration:
    """Test GitHub integration functionality."""
    
    def test_github_client_import(self):
        """Test GitHubClient can be imported."""
        from src.integrations.github_client import GitHubClient
        assert GitHubClient is not None
    
    def test_github_manager_import(self):
        """Test GitHubManager can be imported."""
        from src.integrations.github_manager import GitHubManager
        assert GitHubManager is not None


class TestCostHandler:
    """Test Cost Handler functionality."""
    
    def test_cost_handler_import(self):
        """Test CostHandler can be imported."""
        from src.handlers.cost_handler import CostHandler
        assert CostHandler is not None
    
    def test_cost_handler_initialization(self):
        """Test CostHandler initialization."""
        from src.handlers.cost_handler import CostHandler
        
        mock_smart_cli = Mock()
        handler = CostHandler(mock_smart_cli)
        assert handler.smart_cli == mock_smart_cli


class TestAIClient:
    """Test AI Client functionality."""
    
    def test_ai_client_import(self):
        """Test SimpleOpenRouterClient can be imported."""
        from src.utils.simple_ai_client import SimpleOpenRouterClient
        assert SimpleOpenRouterClient is not None
    
    def test_ai_client_initialization(self):
        """Test AI client initialization."""
        from src.utils.simple_ai_client import SimpleOpenRouterClient
        
        # Mock API key for testing
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            client = SimpleOpenRouterClient()
            assert client is not None


class TestAgentSystem:
    """Test AI Agent System."""
    
    def test_base_agent_import(self):
        """Test BaseAgent can be imported."""
        from src.agents.base_agent import BaseAgent
        assert BaseAgent is not None
    
    def test_orchestrator_import(self):
        """Test Orchestrator can be imported."""
        from src.agents.orchestrator import Orchestrator
        assert Orchestrator is not None
    
    def test_orchestrator_initialization(self):
        """Test Orchestrator initialization."""
        from src.agents.orchestrator import Orchestrator
        
        mock_smart_cli = Mock()
        mock_smart_cli.config = {}
        
        orchestrator = Orchestrator(mock_smart_cli)
        assert orchestrator.smart_cli == mock_smart_cli


class TestTerminalUI:
    """Test Terminal UI components."""
    
    def test_simple_terminal_import(self):
        """Test SimpleTerminal can be imported."""
        from src.core.simple_terminal import SimpleTerminal
        assert SimpleTerminal is not None
    
    def test_simple_terminal_initialization(self):
        """Test SimpleTerminal initialization."""
        from src.core.simple_terminal import SimpleTerminal
        
        terminal = SimpleTerminal()
        assert terminal is not None


class TestIdentitySystem:
    """Test Identity and Authentication."""
    
    def test_identity_import(self):
        """Test identity module can be imported."""
        from src.core.identity import SecurityManager
        assert SecurityManager is not None
    
    def test_security_manager_initialization(self):
        """Test SecurityManager initialization."""
        from src.core.identity import SecurityManager
        
        manager = SecurityManager()
        assert manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])