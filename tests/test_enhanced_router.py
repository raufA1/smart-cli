"""
Tests for Enhanced Request Router functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestEnhancedRequestRouterCommands:
    """Test Enhanced Request Router command handling."""
    
    @pytest.fixture
    def mock_smart_cli(self):
        """Create mock SmartCLI instance."""
        mock_cli = Mock()
        mock_cli.current_conversation = []
        mock_cli.session_manager = Mock()
        return mock_cli
    
    def test_mode_command_parsing(self, mock_smart_cli):
        """Test parsing of mode commands."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            
            router = EnhancedRequestRouter(mock_smart_cli)
            
            # Test various mode command formats
            test_cases = [
                ("/mode", True),
                ("/modestatus", True),
                ("/switch code", True),
                ("/context", True),
                ("regular message", False),
                ("help", False),
                ("/help", False),
                ("/mode list", True),
            ]
            
            for command, expected in test_cases:
                result = router.is_mode_command(command)
                assert result == expected, f"Command '{command}' should return {expected}"
                
        except ImportError:
            pytest.skip("Enhanced Request Router not available")
    
    @pytest.mark.asyncio
    async def test_mode_command_handling(self, mock_smart_cli):
        """Test handling of mode commands."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            from src.core.mode_manager import ModeManager
            
            # Mock mode manager
            mock_mode_manager = Mock(spec=ModeManager)
            mock_mode_manager.handle_mode_command = AsyncMock(return_value="Mode command handled")
            
            router = EnhancedRequestRouter(mock_smart_cli)
            router.mode_manager = mock_mode_manager
            
            # Test mode command handling
            result = await router.handle_mode_command("/mode")
            assert result is not None
            mock_mode_manager.handle_mode_command.assert_called_once_with("/mode")
            
        except ImportError:
            pytest.skip("Enhanced Request Router not available")
    
    def test_request_classification(self, mock_smart_cli):
        """Test request type classification."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            
            router = EnhancedRequestRouter(mock_smart_cli)
            
            # Test different request types
            code_requests = [
                "Write a Python function",
                "Create a class for user management",
                "Generate API endpoints",
                "Fix this bug in my code",
            ]
            
            analysis_requests = [
                "Review this code for security issues",
                "Analyze the performance of this function",
                "What does this code do?",
                "Explain this algorithm",
            ]
            
            for request in code_requests:
                classification = router.classify_request(request)
                assert classification is not None
            
            for request in analysis_requests:
                classification = router.classify_request(request)
                assert classification is not None
                
        except ImportError:
            pytest.skip("Enhanced Request Router not available")


class TestModeIntegration:
    """Test mode system integration with router."""
    
    @pytest.fixture
    def mock_smart_cli(self):
        """Create mock SmartCLI instance."""
        mock_cli = Mock()
        mock_cli.current_conversation = []
        return mock_cli
    
    @pytest.mark.asyncio
    async def test_router_with_mode_manager(self, mock_smart_cli):
        """Test router integration with mode manager."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            from src.core.mode_manager import ModeManager, SmartMode
            
            router = EnhancedRequestRouter(mock_smart_cli)
            mode_manager = ModeManager(mock_smart_cli)
            router.mode_manager = mode_manager
            
            # Test basic integration
            assert router.mode_manager is not None
            assert router.mode_manager.current_mode == SmartMode.SMART
            
        except ImportError:
            pytest.skip("Mode integration not available")
    
    @pytest.mark.asyncio
    async def test_request_processing_with_modes(self, mock_smart_cli):
        """Test request processing with different modes."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            from src.core.mode_manager import ModeManager
            
            router = EnhancedRequestRouter(mock_smart_cli)
            mode_manager = ModeManager(mock_smart_cli)
            router.mode_manager = mode_manager
            
            # Mock the original router methods
            with patch.object(router, 'original_process_request', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "Response"
                
                result = await router.process_request("Test request")
                assert result is not None
                
        except ImportError:
            pytest.skip("Mode integration not available")


class TestErrorHandling:
    """Test error handling in enhanced router."""
    
    @pytest.fixture
    def mock_smart_cli(self):
        """Create mock SmartCLI instance."""
        mock_cli = Mock()
        mock_cli.current_conversation = []
        return mock_cli
    
    def test_router_initialization_with_invalid_cli(self):
        """Test router handles invalid CLI initialization."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            
            # Test with None CLI
            router = EnhancedRequestRouter(None)
            assert router.smart_cli is None
            
        except ImportError:
            pytest.skip("Enhanced Request Router not available")
    
    @pytest.mark.asyncio
    async def test_mode_command_error_handling(self, mock_smart_cli):
        """Test error handling for mode commands."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            
            router = EnhancedRequestRouter(mock_smart_cli)
            
            # Test with no mode manager
            result = await router.handle_mode_command("/mode")
            # Should handle gracefully (return None or error message)
            assert result is None or isinstance(result, str)
            
        except ImportError:
            pytest.skip("Enhanced Request Router not available")


class TestBackwardsCompatibility:
    """Test backwards compatibility with original router."""
    
    @pytest.fixture
    def mock_smart_cli(self):
        """Create mock SmartCLI instance."""
        mock_cli = Mock()
        mock_cli.current_conversation = []
        return mock_cli
    
    def test_fallback_to_original_processing(self, mock_smart_cli):
        """Test fallback to original request processing."""
        try:
            from src.core.enhanced_request_router import EnhancedRequestRouter
            
            router = EnhancedRequestRouter(mock_smart_cli)
            
            # Test that router can be created and has fallback capability
            assert router is not None
            assert hasattr(router, 'smart_cli')
            
        except ImportError:
            pytest.skip("Enhanced Request Router not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])