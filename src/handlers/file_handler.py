"""File Operations Handler for Smart CLI."""

import os

from rich.console import Console

from .base_handler import BaseHandler

console = Console()


class FileHandler(BaseHandler):
    """Handler for file operations like read, show, display."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger file operations."""
        return ["oxu", "read", "show", "display", "cat"]

    async def handle(self, user_input: str) -> bool:
        """Handle file operations."""
        if not self.matches_input(user_input):
            return False

        self.log_debug(f"Processing file operation: {user_input}")

        lower_input = user_input.lower()
        file_path = self.smart_cli.file_manager.extract_file_path(user_input)

        if file_path:
            show_full = "full" in lower_input or "tam" in lower_input
            await self.smart_cli.file_manager.read_file_content(file_path, show_full)

            # Technical document analysis for coding
            if file_path.endswith(".md") and self.ai_client:
                await self._analyze_technical_document(file_path)

            return True
        else:
            # List directory contents if no specific file
            await self.smart_cli.file_manager.list_directory_contents()
            return True

    async def _analyze_technical_document(self, file_path: str):
        """Analyze technical document for coding implementation."""
        try:
            # Start analysis task
            analysis_task_id = self.ui_manager.start_task(
                "doc_analysis", f"Sənəd analizi: {file_path}"
            )

            # Read document content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.ui_manager.update_task(
                analysis_task_id, "in_progress", f"Oxundu: {len(content)} simvol"
            )

            analysis_prompt = f"""
Sənədin məzmununa əsasən koder kimi cavab ver:

SƏNƏD: {content[:3000]}...

Bu sənəddə təsvir edilən sistemi tətbiq etmək üçün:
1. Hansı Python faylları yaratmalıyam?
2. Hansı kitabxanalar lazımdır?
3. Əsas modulların strukturu necə olmalıdır?
4. İlk növbədə hansı funksiyaları yazmalıyam?

QISA VƏ KONKRET CAVAB VER - kod plan kimi."""

            ai_task_id = self.ui_manager.start_task("ai_analysis", "AI analiz prosesi")
            response = await self.ai_client.generate_response(analysis_prompt)

            self.ui_manager.complete_task(ai_task_id, "✅ AI analizi tamamlandı")
            self.ui_manager.complete_task(analysis_task_id, "✅ Texniki analiz hazır")

            # Add analysis todos
            doc_name = os.path.basename(file_path)
            self.smart_cli.todo_manager.add_analysis_todos(doc_name)

            console.print("📋 [bold green]Technical Analysis:[/bold green]")
            self.ui_manager.display_ai_response(response.content, "Code Analyzer")

        except Exception as e:
            self.ui_manager.update_task(analysis_task_id, "failed", f"Xəta: {e}")
            console.print(f"❌ Document analysis failed: {e}", style="red")
