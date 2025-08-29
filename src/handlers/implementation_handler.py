"""Implementation Handler for Smart CLI - AI-powered code generation."""

import os
import re

from rich.console import Console

from .base_handler import BaseHandler

console = Console()


class ImplementationHandler(BaseHandler):
    """Handler for implementation and code generation tasks."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger implementation operations."""
        return [
            "tətbiq et",
            "implement",
            "yarat",
            "create",
            "build",
            "kodu yaz",
            "write code",
            "layihəni tətbiq et",
            "generate",
            "icra et",
            "execute",
            "həyata keçir",
            "realize",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle implementation and code generation tasks."""
        if not self.matches_input(user_input):
            return False

        self.log_debug(f"Processing implementation task: {user_input}")
        console.print("🔥 [bold green]Implementation Mode Activated![/bold green]")

        if self.smart_cli.orchestrator:
            # Use orchestrator for AI-powered implementation
            console.print("🤖 [blue]Using AI Orchestrator for implementation...[/blue]")
            success = await self._use_orchestrator(user_input)
            if not success:
                console.print(
                    "⚠️ [yellow]Orchestrator failed, falling back to direct AI implementation[/yellow]"
                )
                await self._ai_generate_implementation(user_input)
            return success
        else:
            # Fallback to AI-based file generation
            console.print("🎯 [blue]Using AI for direct implementation...[/blue]")
            await self._ai_generate_implementation(user_input)
            return True

    async def _use_orchestrator(self, user_input: str) -> bool:
        """Use orchestrator for complex implementation tasks."""
        # Create implementation plan
        implementation_plan = {
            "steps": [
                {
                    "step": 1,
                    "action": "analyze_requirements",
                    "target": "project_documents",
                    "description": "Analyze project requirements from documentation",
                },
                {
                    "step": 2,
                    "action": "generate_code_structure",
                    "target": "file_structure",
                    "description": "Generate complete code structure and files",
                },
                {
                    "step": 3,
                    "action": "implement_functionality",
                    "target": "code_modules",
                    "description": "Implement all required functionality",
                },
                {
                    "step": 4,
                    "action": "test_implementation",
                    "target": "validation",
                    "description": "Test and validate implementation",
                },
            ]
        }

        # First create a plan, then execute it
        plan = await self.smart_cli.orchestrator.create_detailed_plan(user_input)
        if plan:
            return await self.smart_cli.orchestrator.execute_task_plan(plan, user_input)
        else:
            return False

    async def _ai_generate_implementation(self, user_input: str):
        """Generate implementation using AI based on user request and available documents."""
        if not self.ai_client:
            console.print("❌ [red]AI client not available for implementation[/red]")
            return

        try:
            # Read available documentation
            docs = await self._read_project_documentation()
            documentation = "\\n\\n".join(docs)

            # Create AI prompt for implementation
            implementation_prompt = f"""
Based on the user request: "{user_input}"

And the following documentation:
{documentation}

Please generate a complete implementation with the following files:

1. Create a modular, professional implementation
2. Include proper error handling and logging
3. Follow the architecture described in the documentation
4. Generate actual working code, not pseudocode
5. Include necessary imports and dependencies

Generate the files with this format:
FILENAME: filename.py
CODE:
```python
[actual code here]
```

Generate all necessary files for a complete implementation.
"""

            # Get AI response
            task_id = self.ui_manager.start_task(
                "ai_implementation", "AI Implementation Generation"
            )
            response = await self.ai_client.generate_response(implementation_prompt)
            self.ui_manager.complete_task(task_id, "✅ AI Implementation Generated")

            # Create files from AI response
            await self._create_files_from_response(response.content)

        except Exception as e:
            console.print(f"❌ [red]AI implementation failed: {e}[/red]")

    async def _read_project_documentation(self) -> list[str]:
        """Read all available project documentation."""
        docs = []
        try:
            for file in os.listdir("."):
                if file.endswith(".md"):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            content = f.read()
                            docs.append(f"=== {file} ===\\n{content[:3000]}...")
                    except Exception as e:
                        self.log_debug(f"Could not read {file}: {e}")
        except Exception as e:
            self.log_debug(f"Error reading directory: {e}")

        return docs

    async def _create_files_from_response(self, ai_response: str):
        """Create actual files from AI response."""
        try:
            files_created = []

            # Try multiple parsing patterns to extract code blocks
            patterns = [
                # Pattern 1: FILENAME: xxx CODE: ```python ... ```
                r"FILENAME:\s*([^\n\r]+)\s*CODE:\s*```(?:python|text|markdown)?\s*(.*?)```",
                # Pattern 2: ## filename.py ```python ... ```
                r"##\s*([^\n\r]+\.(?:py|txt|md))\s*```(?:python|text|markdown)?\s*(.*?)```",
                # Pattern 3: **filename.py** ```python ... ```
                r"\*\*([^\n\r]+\.(?:py|txt|md))\*\*\s*```(?:python|text|markdown)?\s*(.*?)```",
                # Pattern 4: filename.py: ```python ... ```
                r"([^\n\r]+\.(?:py|txt|md)):\s*```(?:python|text|markdown)?\s*(.*?)```",
                # Pattern 5: Simple ```python blocks with preceding filename
                r"([a-zA-Z_][a-zA-Z0-9_]*\.(?:py|txt|md))\s*```(?:python|text|markdown)?\s*(.*?)```",
            ]

            # Try each pattern
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
                if found:
                    matches.extend(found)
                    break

            if not matches:
                # Fallback: Look for any code blocks and create generic files
                code_blocks = re.findall(
                    r"```(?:python)?\s*(.*?)```", ai_response, re.DOTALL
                )
                if code_blocks:
                    for i, code in enumerate(code_blocks):
                        if len(code.strip()) > 50:  # Only substantial code blocks
                            filename = f"generated_file_{i+1}.py"
                            matches.append((filename, code))

            # Create files
            for filename, code in matches:
                filename = filename.strip()
                code = code.strip()

                # Clean filename - only add .py if no extension
                if not ("." in filename):
                    filename += ".py"
                # Don't change files that already have proper extensions
                elif filename.endswith(".md.py"):
                    filename = filename.replace(".md.py", ".md")
                elif filename.endswith(".txt.py"):
                    filename = filename.replace(".txt.py", ".txt")
                elif filename.endswith(".gitignore.py"):
                    filename = filename.replace(".gitignore.py", ".gitignore")

                # Create the file
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(code)

                    files_created.append(filename)
                    console.print(f"✅ [green]Created: {filename}[/green]")
                except Exception as file_error:
                    console.print(
                        f"❌ [red]Failed to create {filename}: {file_error}[/red]"
                    )

            if files_created:
                console.print(
                    f"🎉 [bold green]Successfully created {len(files_created)} files![/bold green]"
                )
                console.print("📁 Created files:", style="blue")
                for f in files_created:
                    console.print(f"   • {f}", style="cyan")

                # Show file contents summary
                console.print("\\n📋 [blue]File Contents Summary:[/blue]")
                for f in files_created:
                    try:
                        with open(f, "r", encoding="utf-8") as file:
                            lines = len(file.readlines())
                        console.print(f"   • {f}: {lines} lines", style="cyan")
                    except:
                        pass
            else:
                console.print(
                    "⚠️ [yellow]No files could be extracted from AI response[/yellow]"
                )
                console.print("📄 [blue]Showing AI response as text instead:[/blue]")
                # Fallback: display the response as text
                self.ui_manager.display_ai_response(ai_response, "Code Generator")

        except Exception as e:
            console.print(f"❌ File creation failed: {e}", style="red")
            # Fallback: display the response as text
            console.print("📄 [blue]Showing AI response as text instead:[/blue]")
            self.ui_manager.display_ai_response(ai_response, "Code Generator")
