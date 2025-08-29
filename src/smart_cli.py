"""Smart CLI Main Application - Clean, Modular Architecture."""

import asyncio
import os

from rich.console import Console
from rich.panel import Panel

# Core modules
try:
    # Agents
    from .agents.orchestrator import SmartCLIOrchestrator
    from .core.command_handler import CommandHandler
    from .core.file_manager import FileManager
    from .core.identity import SmartIdentity
    from .core.session_manager import SessionManager

    # UIManager deprecated - using terminal_ui instead
    from .core.simple_git import SimpleGitManager
    from .core.simple_project_generator import SimpleProjectGenerator
    from .core.simple_terminal import SimpleTerminalManager

    # Handlers
    from .handlers import (
        CostHandler,
        FileHandler,
        GitHandler,
        GitHubHandler,
        ImplementationHandler,
        ProjectHandler,
        TerminalHandler,
    )

    # Integrations
    from .integrations.github_manager import GitHubManager

    # Essential utilities only
    from .utils import ConfigManager, OpenRouterClient
except ImportError:
    # Agents
    from agents.orchestrator import SmartCLIOrchestrator
    from core.command_handler import CommandHandler
    from core.file_manager import FileManager
    from core.identity import SmartIdentity
    from core.session_manager import SessionManager

    # UIManager deprecated - using terminal_ui instead
    from core.simple_git import SimpleGitManager
    from core.simple_project_generator import SimpleProjectGenerator
    from core.simple_terminal import SimpleTerminalManager

    # Handlers
    from handlers import (
        CostHandler,
        FileHandler,
        GitHandler,
        GitHubHandler,
        ImplementationHandler,
        ProjectHandler,
        TerminalHandler,
    )

    # Integrations
    from integrations.github_manager import GitHubManager

    # Essential utilities only
    from utils import ConfigManager, OpenRouterClient

console = Console()


class SmartCLI:
    """Main Smart CLI application with clean modular architecture."""

    def __init__(self, debug: bool = False):
        # Core components
        self.config = ConfigManager()
        self.session_manager = SessionManager(debug)
        self.file_manager = FileManager()
        self.command_handler = CommandHandler(self.config)
        self.identity = SmartIdentity()
        # Simple managers without deprecated UI
        self.git_manager = SimpleGitManager()
        self.terminal_manager = SimpleTerminalManager()
        self.project_generator = SimpleProjectGenerator()

        # AI components
        self.ai_client = None
        self.orchestrator = None

        # Integrations
        self.github_manager = None

        # Handlers - initialized after AI components
        self.handlers = []

        self.debug = debug

    async def initialize(self):
        """Initialize Smart CLI components with robust error handling."""
        initialization_steps = [
            ("config", self._initialize_config),
            ("ai_client", self._initialize_ai_client),
            ("orchestrator", self._initialize_orchestrator),
            ("components", self._initialize_components),
            ("handlers", self._initialize_handlers),
        ]

        for step_name, step_func in initialization_steps:
            try:
                success = (
                    await step_func()
                    if asyncio.iscoroutinefunction(step_func)
                    else step_func()
                )
                if not success:
                    if self.debug:
                        console.print(
                            f"⚠️ [dim yellow]{step_name} initialization failed[/dim yellow]"
                        )
                else:
                    if self.debug:
                        console.print(
                            f"✅ [dim green]{step_name} initialized[/dim green]"
                        )
            except Exception as e:
                if self.debug:
                    console.print(
                        f"❌ [red]{step_name} initialization error: {str(e)}[/red]"
                    )
                    console.print_exception()
                # Continue with other components

        console.print("✅ [green]Smart CLI initialized successfully![/green]")
        return True

    def _initialize_config(self):
        """Initialize configuration with validation."""
        try:
            # Validate essential config silently - check for any API key
            has_openrouter = self.config.get_config("openrouter_api_key")
            has_anthropic = self.config.get_config("anthropic_api_key")
            
            if not (has_openrouter or has_anthropic):
                return False
            return True
        except Exception:
            return False

    async def _initialize_ai_client(self):
        """Initialize AI client with config manager integration."""
        try:
            from .utils.simple_ai_client import SimpleOpenRouterClient
            self.ai_client = SimpleOpenRouterClient(self.config)
            
            # Initialize the AI client session
            await self.ai_client.initialize()
            return True
        except Exception as e:
            if self.debug:
                console.print(
                    f"⚠️ [dim yellow]AI client unavailable: {str(e)}[/dim yellow]"
                )
            self.ai_client = None
            return False

    async def _test_ai_connection(self):
        """Test AI connection with timeout."""
        if not self.ai_client:
            return False
        try:
            # Quick test request with timeout
            response = await asyncio.wait_for(
                self.ai_client.generate_response("Test connection"), timeout=5.0
            )
            return response is not None
        except asyncio.TimeoutError:
            if self.debug:
                console.print("⚠️ [dim yellow]AI connection timeout[/dim yellow]")
            return False
        except Exception:
            return False

    def _initialize_orchestrator(self):
        """Initialize orchestrator with config manager integration."""
        try:
            if self.ai_client:
                self.orchestrator = SmartCLIOrchestrator(self.ai_client, self.config)
                return True
            else:
                if self.debug:
                    console.print(
                        "⚠️ [dim yellow]Orchestrator disabled (no AI client)[/dim yellow]"
                    )
                self.orchestrator = None
                return False
        except Exception:
            self.orchestrator = None
            return False

    def _initialize_components(self):
        """Initialize core components."""
        try:
            # Initialize GitHub manager
            github_token = self.config.get_config("github_token")
            if github_token:
                self.github_manager = GitHubManager()  # Removed deprecated ui_manager
                if self.debug:
                    console.print(
                        "✅ [dim green]GitHub integration initialized[/dim green]"
                    )
            else:
                if self.debug:
                    console.print(
                        "⚠️ [dim yellow]GitHub integration disabled (no token)[/dim yellow]"
                    )

            return True
        except Exception as e:
            if self.debug:
                console.print(f"❌ [red]GitHub integration error: {e}[/red]")
            return False

    def _initialize_handlers(self):
        """Initialize command handlers."""
        try:
            self.handlers = [
                FileHandler(self),
                ImplementationHandler(self),
                GitHubHandler(self),
                GitHandler(self),
                TerminalHandler(self),
                ProjectHandler(self),
                CostHandler(self),
            ]

            if self.debug:
                console.print(
                    f"✅ [dim green]Initialized {len(self.handlers)} handlers[/dim green]"
                )

            return True
        except Exception as e:
            if self.debug:
                console.print(f"❌ [red]Handler initialization error: {e}[/red]")
            return False

    async def start(self):
        """Start Smart CLI interactive session."""
        if not await self.initialize():
            return

        await self.session_manager.start_session()

        # Welcome message handled by session_manager
        await self.interactive_loop()

    async def interactive_loop(self):
        """Main interactive loop with fundamental request routing."""
        from core.request_router import RequestRouter

        # Initialize request router
        request_router = RequestRouter(self)

        while self.session_manager.session_active:
            try:
                # Get user input
                user_input = await self._get_user_input()
                if user_input is None:  # EOF or exit
                    break

                # Route request to appropriate processor
                should_continue = await request_router.process_request(user_input)
                if not should_continue:
                    break

            except Exception as e:
                console.print(f"❌ [red]Session error: {str(e)}[/red]")
                if self.debug:
                    console.print_exception()
                continue

        # Cleanup when loop ends
        await self.session_manager.end_session()
        if self.ai_client:
            try:
                await self.ai_client.close_session()
            except Exception:
                pass

    # LEGACY METHODS - kept for compatibility, but replaced by RequestRouter

    async def _get_user_input(self):
        """Get user input with error handling."""
        try:
            # Contextual prompt with caching
            prompt_text = await self._get_contextual_prompt()
            console.print(prompt_text, end="")
            return input().strip()
        except EOFError:
            console.print("\n👋 EOF detected. Goodbye!", style="yellow")
            return None
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="yellow")
            return None
        except Exception as e:
            console.print(f"⚠️ [yellow]Input error: {str(e)}[/yellow]")
            return ""

    # Legacy fallback method - replaced by RequestRouter
    async def _handle_ai_fallback(self, user_input: str):
        """Legacy method - now handled by RequestRouter._process_conversation"""
        return await self._process_ai_request(user_input)

    # Legacy orchestrator methods - now handled by RequestRouter
    # Kept for backward compatibility if needed

    async def _process_ai_request(self, user_input: str):
        """Process AI request with proper error handling."""
        if not self.ai_client:
            console.print("❌ [red]AI client not available[/red]")
            return

        try:
            response = await self.ai_client.generate_response(user_input)

            # Simple AI response display
            console.print(f"🤖 {response.content}")

            # Add to conversation history
            self.session_manager.add_to_history("user", user_input)
            self.session_manager.add_to_history("assistant", response.content)

        except Exception as e:
            console.print(f"❌ [red]AI request failed: {str(e)}[/red]")

    def handle_identity_questions(self, user_input: str) -> bool:
        """Handle Smart CLI identity and self-awareness questions."""
        identity_keywords = [
            "kim sənsən",
            "who are you",
            "özünü tanıt",
            "introduce yourself",
            "nə bacarırsan",
            "what can you do",
            "capabilities",
            "bacarıqların",
            "status",
            "vəziyyət",
            "version",
            "versiya",
        ]

        lower_input = user_input.lower()

        if any(keyword in lower_input for keyword in identity_keywords):
            response = self.identity.handle_identity_questions(user_input)
            console.print(f"🤖 {response}")
            return True

        return False

    async def _get_contextual_prompt(self):
        """Get contextual prompt with git branch."""
        git_status = await self.git_manager.check_git_status()

        if git_status:
            branch = git_status["branch"]
            changes = (
                len(git_status["modified"])
                + len(git_status["staged"])
                + len(git_status["untracked"])
            )

            if changes > 0:
                return f"[{branch}] ⚠️({changes}) > "
            else:
                return f"[{branch}] > "
        else:
            return f"smart > "
