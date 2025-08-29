"""Smart CLI File Manager - File operations and management."""

import os
from typing import Optional

from rich.console import Console

console = Console()


class FileManager:
    """Handles all file operations for Smart CLI."""

    def __init__(self):
        try:
            self.current_directory = os.getcwd()
        except (FileNotFoundError, OSError):
            # Fallback to home directory if current directory doesn't exist
            self.current_directory = os.path.expanduser("~")

    async def read_file_content(self, file_path: str, show_full: bool = False):
        """Read and display file content with smart formatting."""
        try:
            # Find file if not absolute path
            if not os.path.isabs(file_path):
                file_path = self._find_file(file_path)

            if not os.path.exists(file_path):
                console.print(f"❌ File '{file_path}' not found.", style="red")
                return

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            file_size = len(content)
            line_count = content.count("\n") + 1
            filename = os.path.basename(file_path)

            # Display file info
            console.print(f"\n📄 [bold blue]{filename}[/bold blue]")
            console.print(f"📊 Size: {file_size:,} characters, {line_count:,} lines")
            console.print(f"📍 Path: {file_path}\n")

            # Smart content display
            if file_size > 2000 and not show_full:
                lines = content.split("\n")
                console.print("📋 [bold green]File Summary:[/bold green]")

                console.print("[bold cyan]📖 Beginning:[/bold cyan]")
                for i, line in enumerate(lines[:5], 1):
                    display_line = line[:80] + ("..." if len(line) > 80 else "")
                    console.print(f"  {i}. {display_line}")

                console.print("\n[bold cyan]📖 End:[/bold cyan]")
                for i, line in enumerate(lines[-3:], len(lines) - 2):
                    display_line = line[:80] + ("..." if len(line) > 80 else "")
                    console.print(f"  {i}. {display_line}")

                console.print(
                    f"\n💡 [dim]File is large ({file_size:,} chars). Use 'read full {filename}' to see complete content.[/dim]"
                )
            else:
                # Show full content
                if show_full and file_size > 2000:
                    console.print("📖 [bold green]Full Content:[/bold green]\n")

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    console.print(f"  {i:3d} │ {line}")

        except Exception as e:
            console.print(f"❌ Error reading file: {str(e)}", style="red")

    def _find_file(self, filename: str) -> str:
        """Find file in current directory and common locations."""
        # Try current directory first
        current_file = os.path.join(os.getcwd(), filename)
        if os.path.exists(current_file):
            return current_file

        # Search in common locations
        search_paths = [
            os.getcwd(),
            os.path.join(os.getcwd(), "src"),
            os.path.expanduser("~"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Documents/Projects"),
        ]

        for search_path in search_paths:
            for root, dirs, files in os.walk(search_path):
                if filename in files:
                    return os.path.join(root, filename)
                # Limit search depth
                if root != search_path:
                    break

        return filename  # Return original if not found

    async def write_file_content(self, file_path: str, content: str):
        """Write content to file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"✅ File written: {file_path}", style="green")
        except Exception as e:
            console.print(f"❌ Error writing file: {str(e)}", style="red")

    async def list_directory_contents(self):
        """List current directory contents."""
        try:
            files = []
            dirs = []

            for item in os.listdir(self.current_directory):
                if os.path.isdir(item):
                    dirs.append(item)
                else:
                    files.append(item)

            console.print(
                f"📁 [bold blue]Current Directory: {self.current_directory}[/bold blue]\n"
            )

            if dirs:
                console.print("📂 [bold green]Directories:[/bold green]")
                for dir_name in sorted(dirs):
                    console.print(f"  📁 {dir_name}")
                console.print()

            if files:
                console.print("📄 [bold green]Files:[/bold green]")
                for file_name in sorted(files):
                    file_path = os.path.join(self.current_directory, file_name)
                    file_size = os.path.getsize(file_path)
                    console.print(f"  📄 {file_name} ({file_size:,} bytes)")

        except Exception as e:
            console.print(f"❌ Error listing directory: {str(e)}", style="red")

    def extract_file_path(self, user_input: str) -> Optional[str]:
        """Extract file path from user input."""
        # Look for common file extensions
        file_patterns = [
            ".py",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".json",
            ".yaml",
            ".yml",
            ".md",
            ".txt",
        ]

        words = user_input.split()
        for word in words:
            if any(pattern in word for pattern in file_patterns):
                return word.strip("\"'")

        return None
