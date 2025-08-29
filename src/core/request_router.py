"""Smart CLI Request Router - Advanced request processing with intelligent classification."""

import asyncio
import os
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()

try:
    from .intelligent_request_classifier import (
        ClassificationResult,
        RequestType,
        get_intelligent_classifier,
    )
except ImportError:
    from intelligent_request_classifier import (
        ClassificationResult,
        RequestType,
        get_intelligent_classifier,
    )


class RequestRouter:
    """Advanced request router with intelligent classification and context awareness."""

    def __init__(self, smart_cli_instance):
        """Initialize router with Smart CLI instance and intelligent classifier."""
        self.smart_cli = smart_cli_instance
        self.orchestrator = smart_cli_instance.orchestrator
        self.handlers = smart_cli_instance.handlers
        self.command_handler = smart_cli_instance.command_handler
        self.debug = smart_cli_instance.debug

        # Initialize intelligent classifier
        self.classifier = get_intelligent_classifier()

    async def process_request(self, user_input: str) -> bool:
        """Process user request using intelligent classification and routing.

        Returns:
            bool: True if request was handled, False if should exit
        """
        if not user_input.strip():
            return True

        # Get current context
        context = self._get_current_context()

        # Intelligent request classification
        classification = self.classifier.classify_request(user_input, context)

        if self.debug:
            console.print(
                f"🔍 [dim]Request: {classification.request_type.value} (confidence: {classification.confidence:.2f})[/dim]"
            )
            console.print(
                f"💭 [dim]Reasoning: {', '.join(classification.reasoning)}[/dim]"
            )

        # Route to appropriate processor
        try:
            return await self._route_to_processor(classification, user_input)
        except Exception as e:
            console.print(f"❌ [red]Request processing error: {str(e)}[/red]")
            if self.debug:
                console.print_exception()
            return True

    def _get_current_context(self) -> Dict[str, any]:
        """Get current environment context for better classification."""
        context = {}

        # Check if in git repository
        try:
            context["is_git_repo"] = os.path.exists(".git") or os.path.exists("../.git")
        except:
            context["is_git_repo"] = False

        # Check for code files in current directory
        try:
            code_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]
            files = os.listdir(".")
            context["has_code_files"] = any(
                f.endswith(tuple(code_extensions)) for f in files
            )
        except:
            context["has_code_files"] = False

        # Check current directory name (project context)
        context["current_dir"] = os.path.basename(os.getcwd())

        return context

    async def _route_to_processor(
        self, classification: ClassificationResult, user_input: str
    ) -> bool:
        """Route request to appropriate processor based on intelligent classification."""

        request_type = classification.request_type

        # Route based on intelligent classification
        if request_type == RequestType.COMMAND:
            return await self._process_command(user_input)

        elif request_type == RequestType.DEVELOPMENT:
            return await self._process_development(user_input, classification)

        elif request_type == RequestType.UTILITY:
            return await self._process_utility(user_input, classification)

        elif request_type == RequestType.ANALYSIS:
            return await self._process_analysis(user_input, classification)

        elif request_type == RequestType.LEARNING:
            return await self._process_learning(user_input, classification)

        else:  # RequestType.CONVERSATION
            return await self._process_conversation(user_input)

        return True

    async def _process_command(self, user_input: str) -> bool:
        """Process special commands."""
        return await self.command_handler.handle_command(user_input)

    async def _process_development(
        self, user_input: str, classification: ClassificationResult
    ) -> bool:
        """Process development tasks using orchestrator with intelligent insights."""
        if not self.orchestrator:
            console.print(
                "⚠️ [yellow]Orchestrator not available for development tasks[/yellow]"
            )
            return await self._process_conversation(user_input)

        # Enhanced development processing with context
        tech_stack = classification.context_hints.get("tech_stack", "general")
        urgency = classification.context_hints.get("urgency", "normal")

        console.print(
            f"🎭 [bold blue]Development Task → Smart CLI Orchestrator[/bold blue]"
        )
        console.print(f"🔧 [dim]Context: {tech_stack} | Priority: {urgency}[/dim]")

        try:
            # Create and execute plan with enhanced context
            plan = await self.orchestrator.create_detailed_plan(user_input)

            # Add classification insights to plan
            if "context_hints" not in plan:
                plan["context_hints"] = classification.context_hints
            plan["confidence"] = classification.confidence
            plan["reasoning"] = classification.reasoning

            success = await self.orchestrator.execute_task_plan(plan, user_input)

            if not success:
                console.print(
                    "⚠️ [yellow]Orchestrator task failed, falling back to AI conversation[/yellow]"
                )
                return await self._process_conversation(user_input)

            return True

        except Exception as e:
            console.print(
                f"⚠️ [yellow]Orchestrator error: {str(e)}, falling back to AI[/yellow]"
            )
            return await self._process_conversation(user_input)

    async def _process_utility(
        self, user_input: str, classification: ClassificationResult
    ) -> bool:
        """Process utility operations using smart handler selection."""
        console.print(
            f"🔧 [blue]Utility Operation: {classification.suggested_action}[/blue]"
        )

        # Smart handler selection based on classification
        context_hints = classification.context_hints

        # Prioritize handlers based on context
        prioritized_handlers = self._prioritize_handlers(self.handlers, context_hints)

        for handler in prioritized_handlers:
            try:
                if await handler.handle(user_input):
                    return True
            except Exception as e:
                if self.debug:
                    console.print(
                        f"⚠️ [dim yellow]Handler {handler.__class__.__name__} error: {str(e)}[/dim yellow]"
                    )
                continue

        # Enhanced fallback with context awareness
        console.print(
            "🤖 [yellow]No specific handler found, routing to AI conversation[/yellow]"
        )
        return await self._process_conversation(user_input)

    def _prioritize_handlers(self, handlers, context_hints):
        """Prioritize handlers based on context hints."""
        # Simple priority logic - can be enhanced
        git_keywords = ["git", "commit", "push", "pull"]
        cost_keywords = ["cost", "budget", "xərc"]

        prioritized = []
        regular = []

        for handler in handlers:
            handler_name = handler.__class__.__name__.lower()

            # Prioritize git handler for git operations
            if "git" in handler_name and any(
                kw in context_hints.get("original_text", "") for kw in git_keywords
            ):
                prioritized.append(handler)
            # Prioritize cost handler for cost operations
            elif "cost" in handler_name and any(
                kw in context_hints.get("original_text", "") for kw in cost_keywords
            ):
                prioritized.append(handler)
            else:
                regular.append(handler)

        return prioritized + regular

    async def _process_analysis(
        self, user_input: str, classification: ClassificationResult
    ) -> bool:
        """Process analysis requests with enhanced intelligence."""
        console.print("🔍 [green]Analysis Mode Activated[/green]")

        # Check if orchestrator can handle analysis
        if self.orchestrator:
            try:
                # Create analysis-focused plan
                plan = await self.orchestrator.create_detailed_plan(
                    f"Analyze: {user_input}"
                )
                plan["analysis_mode"] = True
                plan["context_hints"] = classification.context_hints

                return await self.orchestrator.execute_task_plan(plan, user_input)
            except Exception as e:
                if self.debug:
                    console.print(
                        f"⚠️ [dim yellow]Analysis orchestrator error: {str(e)}[/dim yellow]"
                    )

        # Fallback to AI conversation with analysis context
        return await self._process_conversation(f"Please analyze: {user_input}")

    async def _process_learning(
        self, user_input: str, classification: ClassificationResult
    ) -> bool:
        """Process learning/help requests with educational focus."""
        console.print("📚 [magenta]Learning Mode Activated[/magenta]")

        # Enhanced learning response with context
        context = classification.context_hints
        tech_stack = context.get("tech_stack", "general")

        # Create educational prompt
        educational_prompt = f"Please provide educational explanation for: {user_input}"
        if tech_stack != "general":
            educational_prompt += f" (Focus on {tech_stack} context)"

        return await self._process_conversation(educational_prompt)

    async def _process_conversation(self, user_input: str) -> bool:
        """Process general AI conversation."""
        if hasattr(self.smart_cli, "_process_ai_request"):
            try:
                await asyncio.wait_for(
                    self.smart_cli._process_ai_request(user_input), timeout=30.0
                )
            except asyncio.TimeoutError:
                console.print("⏰ [yellow]AI request timed out[/yellow]")
            except Exception as e:
                console.print(f"❌ [red]AI processing error: {str(e)}[/red]")
        else:
            console.print("⚠️ [yellow]AI processing not available[/yellow]")

        return True
