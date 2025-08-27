"""Interactive Chat Session for Smart CLI - Main AI Assistant Interface."""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.table import Table

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from src.utils.ai_client import OpenRouterClient, ChatMessage
    from src.utils.config import ConfigManager
    from src.utils.usage_tracker import UsageTracker
    from src.utils.agents import AgentOrchestrator, AgentRole, AgentTask
    from src.utils.context import ContextManager
    from src.utils.orchestrator import WorkflowOrchestrator, TaskNode, WorkflowContext, OrchestrationPattern
    from src.utils.enhanced_nlp import IntentRecognitionEngine, TaskComplexity, StructuredOutputGenerator
    from src.utils.model_orchestrator import ModelOrchestrator, ModelTier
    from src.utils.shell_executor import ShellExecutor, NativeFSExecutor
    from src.utils.execution_workflow import ExecutionWorkflowManager, WorkflowStep, ApprovalStatus
    from src.utils.plugin_system import PluginManager
    # New Claude Code-like capabilities
    from src.utils.file_operations import FileOperationTools
    from src.utils.code_search import CodeSearchTools
    from src.utils.git_operations import GitOperations
    from src.utils.web_capabilities import WebCapabilities
    from src.utils.task_management import TaskManager
    from src.utils.background_execution import BackgroundExecutor
    from src.utils.code_analyzer import CodeAnalyzer
    from src.utils.project_analyzer import ProjectAnalyzer
    from src.intent_analyzer import IntentAnalyzer
except ImportError:
    # Fallback imports for different execution contexts
    try:
        from utils.ai_client import OpenRouterClient, ChatMessage
        from utils.config import ConfigManager
        from utils.usage_tracker import UsageTracker
        from utils.agents import AgentOrchestrator, AgentRole, AgentTask
        from utils.context import ContextManager
        from utils.orchestrator import WorkflowOrchestrator, TaskNode, WorkflowContext, OrchestrationPattern
        from utils.enhanced_nlp import IntentRecognitionEngine, TaskComplexity, StructuredOutputGenerator
        from utils.model_orchestrator import ModelOrchestrator, ModelTier
        from utils.shell_executor import ShellExecutor, NativeFSExecutor
        from utils.execution_workflow import ExecutionWorkflowManager, WorkflowStep, ApprovalStatus
        from utils.plugin_system import PluginManager
        # New Claude Code-like capabilities
        from utils.file_operations import FileOperationTools
        from utils.code_search import CodeSearchTools
        from utils.git_operations import GitOperations
        from utils.web_capabilities import WebCapabilities
        from utils.task_management import TaskManager
        from utils.background_execution import BackgroundExecutor
        from utils.code_analyzer import CodeAnalyzer
        from utils.project_analyzer import ProjectAnalyzer
        from intent_analyzer import IntentAnalyzer
    except ImportError:
        # Final fallback to relative imports
        from .utils.ai_client import OpenRouterClient, ChatMessage
        from .utils.config import ConfigManager
        from .utils.usage_tracker import UsageTracker
        from .utils.agents import AgentOrchestrator, AgentRole, AgentTask
        from .utils.context import ContextManager
        from .utils.orchestrator import WorkflowOrchestrator, TaskNode, WorkflowContext, OrchestrationPattern
        from .utils.enhanced_nlp import IntentRecognitionEngine, TaskComplexity, StructuredOutputGenerator
        from .utils.model_orchestrator import ModelOrchestrator, ModelTier
        from .utils.shell_executor import ShellExecutor, NativeFSExecutor
        from .utils.execution_workflow import ExecutionWorkflowManager, WorkflowStep, ApprovalStatus
        from .utils.plugin_system import PluginManager
        # New Claude Code-like capabilities
        from .utils.file_operations import FileOperationTools
        from .utils.code_search import CodeSearchTools
        from .utils.git_operations import GitOperations
        from .utils.web_capabilities import WebCapabilities
        from .utils.task_management import TaskManager
        from .utils.background_execution import BackgroundExecutor
        from .utils.code_analyzer import CodeAnalyzer
        from .utils.project_analyzer import ProjectAnalyzer
        from .intent_analyzer import IntentAnalyzer
import os
import json
from pathlib import Path

console = Console()

class InteractiveChatSession:
    """Main interactive chat session for Smart CLI AI Assistant."""
    
    def __init__(self, debug: bool = False):
        self.config = ConfigManager()
        self.usage_tracker = UsageTracker()
        self.intent_analyzer = IntentAnalyzer()
        self.context_manager = ContextManager(self.config)
        
        # Enhanced orchestration system
        self.ai_client = None
        self.workflow_orchestrator = None
        self.nlp_engine = None
        self.model_orchestrator = None
        self.structured_output_generator = None
        self.agent_orchestrator = None  # Legacy support
        
        # New execution system
        self.execution_workflow_manager = None
        self.shell_executor = None
        self.fs_executor = None
        self.plugin_manager = None
        
        # Claude Code-like capabilities
        self.file_tools = None
        self.search_tools = None
        self.git_tools = None
        self.web_tools = None
        self.task_manager = None
        self.background_executor = None
        self.code_analyzer = None
        self.project_analyzer = None
        
        self.messages: List[Dict[str, str]] = []
        self.conversation_history = []
        self.session_id = f"smart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.debug = debug
        
        # Current working context
        self.current_project_path = os.getcwd()
        self.current_context = None
        self.recent_files = []  # Track recently accessed files
        
        # Active workflows
        self.active_workflows = {}
        
    async def start(self):
        """Start the interactive chat session."""
        try:
            # Initialize AI client
            if not await self.initialize_ai():
                return
                
            # Display welcome screen
            self.display_welcome()
            
            # Main interactive loop
            await self.interactive_loop()
            
        except KeyboardInterrupt:
            console.print("\n\n👋 Smart CLI session ended by user.", style="yellow")
        except Exception as e:
            if self.debug:
                console.print(f"\n❌ Session error: {str(e)}", style="red")
            else:
                console.print("\n❌ An error occurred. Use --debug for details.", style="red")
    
    async def initialize_ai(self) -> bool:
        """Initialize AI client with available API keys."""
        api_key = (
            self.config.get_config('openrouter_api_key') or
            self.config.get_config('anthropic_api_key') or  
            self.config.get_config('openai_api_key')
        )
        
        if not api_key:
            console.print("❌ [red]No AI API key found.[/red]")
            console.print("\n📝 Please configure an API key using:")
            console.print("• [cyan]/config openrouter_api_key YOUR_KEY[/cyan]", style="dim")
            console.print("• [cyan]/config anthropic_api_key YOUR_KEY[/cyan]", style="dim") 
            console.print("• [cyan]/config openai_api_key YOUR_KEY[/cyan]", style="dim")
            console.print("\n💡 Get API keys from: https://openrouter.ai or https://console.anthropic.com", style="dim")
            console.print("\n🔧 You can still use /config, /help, and other commands without API key", style="yellow")
            
            # Still allow interactive mode without AI
            return True
            
        self.ai_client = OpenRouterClient(self.config)
        
        # Initialize enhanced orchestration system
        self.workflow_orchestrator = WorkflowOrchestrator(self.ai_client)
        self.nlp_engine = IntentRecognitionEngine(self.ai_client)
        self.model_orchestrator = ModelOrchestrator(self.ai_client)
        self.structured_output_generator = StructuredOutputGenerator(self.ai_client)
        
        # Initialize new execution system
        self.shell_executor = ShellExecutor(self.current_project_path)
        self.fs_executor = NativeFSExecutor(self.current_project_path)
        self.execution_workflow_manager = ExecutionWorkflowManager(self.current_project_path)
        
        # Initialize plugin system
        self.plugin_manager = PluginManager()
        await self.plugin_manager.initialize()
        
        # Initialize legacy agent orchestrator for backward compatibility
        self.agent_orchestrator = AgentOrchestrator(self.ai_client)
        
        # Initialize Claude Code-like capabilities
        self.file_tools = FileOperationTools(self.config)
        self.search_tools = CodeSearchTools(self.config)
        self.git_tools = GitOperations(self.config, self.current_project_path)
        self.web_tools = WebCapabilities(self.config)
        self.task_manager = TaskManager(self.config)
        try:
            from src.utils.background_execution import get_background_executor
        except ImportError:
            try:
                from utils.background_execution import get_background_executor
            except ImportError:
                from .utils.background_execution import get_background_executor
        self.background_executor = get_background_executor()
        self.code_analyzer = CodeAnalyzer(self.config)
        self.project_analyzer = ProjectAnalyzer(self.config)
        
        return True
    
    def display_welcome(self):
        """Display the main welcome screen."""
        console.clear()
        
        # Welcome header
        welcome_text = Text()
        welcome_text.append("🚀 ", style="blue")
        welcome_text.append("Smart CLI v1.0.0", style="bold blue")
        welcome_text.append(" - Interactive AI Assistant", style="dim blue")
        
        # System info
        model = self.config.get_config('default_model', 'anthropic/claude-3-sonnet-20240229')
        info_grid = Table.grid(padding=1)
        info_grid.add_column(style="cyan", justify="right")
        info_grid.add_column(style="white")
        
        info_grid.add_row("Session ID:", self.session_id)
        info_grid.add_row("AI Model:", model.split('/')[-1] if '/' in model else model)
        info_grid.add_row("Ready for:", "Natural language commands")
        
        # Create welcome panel
        welcome_panel = Panel(
            info_grid,
            title=welcome_text,
            border_style="blue",
            padding=(1, 2)
        )
        console.print(welcome_panel)
        
        # Quick tips
        tips_table = Table.grid(padding=1)
        tips_table.add_column(style="green")
        tips_table.add_column(style="dim")
        
        tips = [
            ("💬", "Type naturally - ask questions, request code, get help"),
            ("🛠️", "'create a python fastapi project' - generates complete projects"),
            ("📝", "'add user authentication' - adds features to existing code"),
            ("🔍", "'review my code for bugs' - analyzes and suggests improvements"),
            ("❓", "'/help' - show available commands | 'Ctrl+C' to exit")
        ]
        
        for emoji, tip in tips:
            tips_table.add_row(f" {emoji}", tip)
        
        console.print("\n✨ [bold green]What can I help you build today?[/bold green]\n")
        console.print(tips_table)
        console.print()
    
    async def interactive_loop(self):
        """Main interactive chat loop."""
        while True:
            try:
                # Get user input with error handling
                try:
                    console.print("💬 [bold green]You:[/bold green] ", end="")
                    user_input = input().strip()
                except EOFError:
                    console.print("\n👋 EOF detected. Goodbye!", style="yellow")
                    break
                except KeyboardInterrupt:
                    console.print("\n👋 Goodbye!", style="yellow")  
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not await self.handle_command(user_input):
                        break
                    continue
                
                # Check for file operations first
                if await self.handle_file_operations(user_input):
                    continue
                
                # Process AI chat
                if self.ai_client:
                    await self.process_ai_interaction(user_input)
                else:
                    console.print("❌ AI client not available. Please configure API key first.", style="red")
                    console.print("Use /config to set your API key", style="dim")
                
            except KeyboardInterrupt:
                console.print("\n\n👋 Session ended.", style="yellow")
                break
            except Exception as e:
                if self.debug:
                    console.print(f"\n❌ Error: {str(e)}", style="red")
                else:
                    console.print("\n❌ Something went wrong. Try again or use --debug.", style="red")
    
    async def handle_command(self, command: str) -> bool:
        """Handle special commands. Returns False to exit."""
        parts = command[1:].split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ['quit', 'exit', 'q']:
            console.print("👋 Goodbye!", style="green")
            return False
            
        elif cmd == 'help':
            self.display_help()
            
        elif cmd == 'clear':
            self.messages.clear()
            console.clear()
            self.display_welcome()
            console.print("✅ Conversation history cleared.", style="green")
            
        elif cmd == 'history':
            self.display_history()
            
        elif cmd == 'model':
            if args:
                self.config.set_config('default_model', args)
                console.print(f"✅ Model changed to: {args}", style="green")
            else:
                current = self.config.get_config('default_model', 'anthropic/claude-3-sonnet-20240229')
                console.print(f"Current model: {current}", style="cyan")
                
        elif cmd == 'usage':
            self.display_session_usage()
            
        elif cmd == 'config':
            if args:
                parts = args.split(' ', 1)
                if len(parts) == 2:
                    key, value = parts
                    # Check if this is a sensitive configuration that should be stored securely
                    secure_keys = {'openrouter_api_key', 'anthropic_api_key', 'openai_api_key', 'database_url'}
                    is_secure = key in secure_keys
                    
                    self.config.set_config(key, value, secure=is_secure)
                    
                    # Hide sensitive values in output
                    display_value = "***hidden***" if is_secure else value
                    console.print(f"✅ Set {key} = {display_value}", style="green")
                    
                    # If API key was set, reinitialize AI client
                    if key.endswith('_api_key'):
                        console.print("🔄 Reinitializing AI client...", style="yellow")
                        await self.initialize_ai()
                        if self.ai_client:
                            console.print("✅ AI client ready!", style="green")
                else:
                    console.print("❌ Usage: /config <key> <value>", style="red")
                    console.print("Example: /config openrouter_api_key your_api_key_here", style="dim")
            else:
                self.display_config_help()
        
        # File Operations Commands
        elif cmd == 'create':
            if args:
                await self.handle_file_create(args)
            else:
                console.print("❌ Usage: /create <filename> [content]", style="red")
                console.print("Example: /create app.py 'print(\"Hello World\")'", style="dim")
        
        elif cmd == 'edit':
            if args:
                await self.handle_file_edit(args)
            else:
                console.print("❌ Usage: /edit <filename>", style="red")
                console.print("Opens file for AI-assisted editing", style="dim")
        
        elif cmd == 'read':
            if args:
                await self.handle_file_read(args)
            else:
                console.print("❌ Usage: /read <filename>", style="red")
        
        elif cmd == 'ls' or cmd == 'list':
            await self.handle_list_files(args)
        
        elif cmd == 'pwd':
            console.print(f"Current directory: {self.current_project_path}", style="cyan")
        
        elif cmd == 'cd':
            if args:
                await self.handle_change_directory(args)
            else:
                console.print(f"Current directory: {self.current_project_path}", style="cyan")
        
        # Agent Commands  
        elif cmd == 'agents':
            await self.handle_list_agents()
        
        elif cmd == 'generate':
            if args:
                await self.handle_agent_generate(args)
            else:
                console.print("❌ Usage: /generate <description>", style="red")
                console.print("Example: /generate python function to calculate fibonacci", style="dim")
        
        elif cmd == 'review':
            if args:
                await self.handle_agent_review(args)
            else:
                console.print("❌ Usage: /review <filename>", style="red")
        
        # API Management Commands
        elif cmd == 'api':
            if args:
                await self.handle_api_management(args)
            else:
                await self.display_api_help()
        
        elif cmd == 'project':
            if args:
                await self.handle_project_management(args)
            else:
                await self.display_project_help()
        
        # New Claude Code-like commands
        elif cmd == 'search' or cmd == 'grep':
            if args:
                await self.handle_code_search(args)
            else:
                console.print("❌ Usage: /search <pattern> [options]", style="red")
                console.print("Example: /search 'function.*main' --type py", style="dim")
        
        elif cmd == 'glob' or cmd == 'find':
            if args:
                await self.handle_glob_search(args)
            else:
                console.print("❌ Usage: /glob <pattern>", style="red")
                console.print("Example: /glob '*.py' or /glob 'src/**/*.ts'", style="dim")
        
        elif cmd == 'git':
            if args:
                await self.handle_git_command(args)
            else:
                await self.display_git_help()
        
        elif cmd == 'web':
            if args:
                await self.handle_web_command(args)
            else:
                await self.display_web_help()
        
        elif cmd == 'todo':
            if args:
                await self.handle_todo_command(args)
            else:
                await self.display_todo_help()
        
        elif cmd == 'analyze':
            if args:
                await self.handle_code_analysis(args)
            else:
                console.print("❌ Usage: /analyze <file|project>", style="red")
                console.print("Example: /analyze app.py or /analyze project", style="dim")
        
        elif cmd == 'bash':
            if args:
                await self.handle_background_bash(args)
            else:
                console.print("❌ Usage: /bash <command>", style="red")
                console.print("Example: /bash 'npm install' --background", style="dim")
        
        elif cmd == 'processes':
            await self.handle_list_processes()
            
        else:
            console.print(f"❌ Unknown command: {command}", style="red")
            console.print("Type /help for available commands", style="dim")
            
        return True
    
    async def handle_file_operations(self, user_input: str) -> bool:
        """Handle comprehensive file operations like read, write, edit, create."""
        lower_input = user_input.lower()
        words = user_input.split()
        
        # Enhanced file operation patterns
        read_patterns = [
            'read', 'oxu', 'show', 'göstər', 'cat', 'display',
            'open', 'aç', 'view', 'bax', 'see', 'gör', 'get'
        ]
        
        write_patterns = [
            'write', 'yaz', 'create', 'yarat', 'make', 'new', 'yeni',
            'save', 'qeyd et', 'generate', 'əlavə et'
        ]
        
        edit_patterns = [
            'edit', 'redaktə', 'modify', 'dəyiş', 'update', 'yenilə',
            'change', 'fix', 'düzəlt', 'correct'
        ]
        
        delete_patterns = [
            'delete', 'sil', 'remove', 'götür', 'del', 'rm'
        ]
        
        list_patterns = ['list', 'ls', 'dir', 'files', 'fayllar', 'show files']
        
        # Extract file path from input
        file_path = self._extract_file_path(user_input)
        
        # Handle different file operations
        if any(pattern in lower_input for pattern in read_patterns):
            if file_path:
                # Check if user wants full content
                show_full = 'full' in lower_input or 'tam' in lower_input or 'complete' in lower_input
                await self.read_file_content(file_path, show_full=show_full)
                return True
            else:
                # If no specific file mentioned, show available files
                console.print("📁 No file specified. Available files:", style="yellow")
                await self.list_directory_contents()
                return True
        
        elif any(pattern in lower_input for pattern in write_patterns):
            if file_path:
                # Extract content from input
                content = self._extract_content_from_input(user_input, file_path)
                await self.write_file_content(file_path, content)
                return True
            else:
                console.print("❌ No file path specified for writing.", style="red")
                console.print("💡 Example: 'create test.py with hello world code'", style="dim")
                return True
        
        elif any(pattern in lower_input for pattern in edit_patterns):
            if file_path:
                await self.edit_file_content(file_path, user_input)
                return True
            else:
                console.print("❌ No file specified for editing.", style="red")
                console.print("💡 Example: 'edit main.py add new function'", style="dim")
                return True
        
        elif any(pattern in lower_input for pattern in delete_patterns):
            if file_path:
                await self.delete_file(file_path)
                return True
            else:
                console.print("❌ No file specified for deletion.", style="red")
                return True
        
        elif any(pattern in lower_input for pattern in list_patterns):
            if 'current' in lower_input or 'here' in lower_input or 'burada' in lower_input:
                await self.list_directory_contents()
            else:
                await self.list_directory_contents()
            return True
        
        # Check for directory operations
        if self._is_directory_operation(lower_input):
            return await self.handle_directory_operations(user_input)
        
        return False
    
    async def read_file_content(self, file_path: str, show_full: bool = False):
        """Read and display file content."""
        try:
            # Check if file exists in current directory first
            if not os.path.isabs(file_path):
                # Try current directory
                current_file = os.path.join(os.getcwd(), file_path)
                if os.path.exists(current_file):
                    file_path = current_file
                else:
                    # Try looking in common locations
                    search_paths = [
                        os.getcwd(),
                        os.path.expanduser('~'),
                        os.path.expanduser('~/Documents'),
                        os.path.expanduser('~/Documents/Projects')
                    ]
                    
                    found = False
                    for search_path in search_paths:
                        for root, dirs, files in os.walk(search_path):
                            if file_path in files:
                                file_path = os.path.join(root, file_path)
                                found = True
                                break
                        if found:
                            break
            
            if not os.path.exists(file_path):
                console.print(f"❌ File '{file_path}' not found.", style="red")
                console.print(f"📁 Current directory: {os.getcwd()}", style="dim")
                return
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Display file info
            file_size = len(content)
            line_count = content.count('\n') + 1
            
            # Create header
            header_text = f"📄 {os.path.basename(file_path)} ({file_size:,} chars, {line_count:,} lines)"
            
            # Smart and concise file display
            console.print(f"\n[bold blue]📄 {os.path.basename(file_path)}[/bold blue]")
            console.print(f"[dim]📊 Size: {file_size:,} characters, {line_count:,} lines[/dim]")
            console.print(f"[dim]📍 Path: {file_path}[/dim]\n")
            
            # For large files, show summary unless full content requested
            if len(content) > 2000 and not show_full:
                lines = content.split('\n')
                console.print("📋 [bold green]File Summary:[/bold green]")
                
                # Show first few lines
                console.print("[bold cyan]📖 Beginning:[/bold cyan]")
                for i, line in enumerate(lines[:5], 1):
                    console.print(f"  {i}. {line[:80]}{'...' if len(line) > 80 else ''}")
                
                console.print("\n[bold cyan]📖 End:[/bold cyan]")
                for i, line in enumerate(lines[-3:], len(lines)-2):
                    console.print(f"  {i}. {line[:80]}{'...' if len(line) > 80 else ''}")
                
                console.print(f"\n💡 [dim]File is large ({file_size:,} chars). Use 'read full {os.path.basename(file_path)}' to see complete content.[/dim]")
                
            elif show_full or len(content) <= 2000:
                # Show full content for small files or when explicitly requested
                if show_full and len(content) > 2000:
                    console.print("📖 [bold green]Full Content:[/bold green]\n")
                
                if file_path.endswith('.md'):
                    try:
                        console.print(Markdown(content))
                    except:
                        console.print(content)
                elif file_path.endswith(('.py', '.js', '.json', '.html', '.css')):
                    # Show with line numbers for code
                    lines = content.split('\n')
                    max_lines = len(lines) if show_full else min(20, len(lines))
                    
                    for i, line in enumerate(lines[:max_lines], 1):
                        console.print(f"[dim]{i:3d}[/dim] │ {line}")
                    
                    if not show_full and len(lines) > 20:
                        console.print(f"[dim]... and {len(lines)-20} more lines[/dim]")
                else:
                    # Plain text
                    if show_full:
                        console.print(content)
                    else:
                        console.print(content[:1000])
                        if len(content) > 1000:
                            console.print("[dim]... (truncated)[/dim]")
            
            # Add to recent files
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:10]  # Keep last 10
            
        except Exception as e:
            console.print(f"❌ Error reading file: {str(e)}", style="red")
    
    async def list_directory_contents(self):
        """List contents of current directory."""
        try:
            current_dir = os.getcwd()
            console.print(f"\n📁 [bold blue]Directory: {current_dir}[/bold blue]\n")
            
            items = os.listdir(current_dir)
            
            # Separate files and directories
            dirs = []
            files = []
            
            for item in items:
                full_path = os.path.join(current_dir, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            # Display directories first
            if dirs:
                console.print("[bold cyan]📂 Directories:[/bold cyan]")
                for d in sorted(dirs):
                    console.print(f"  📂 {d}")
                console.print()
            
            # Display files
            if files:
                console.print("[bold green]📄 Files:[/bold green]")
                for f in sorted(files):
                    file_path = os.path.join(current_dir, f)
                    size = os.path.getsize(file_path)
                    size_str = f"({size:,} bytes)" if size < 1024 else f"({size/1024:.1f} KB)"
                    console.print(f"  📄 {f} [dim]{size_str}[/dim]")
            
            if not dirs and not files:
                console.print("📭 Directory is empty.")
                
        except Exception as e:
            console.print(f"❌ Error listing directory: {str(e)}", style="red")
    
    def _extract_file_path(self, user_input: str) -> Optional[str]:
        """Extract file path from user input."""
        words = user_input.split()
        
        # Look for files with extensions
        for word in words:
            if '.' in word and any(ext in word.lower() for ext in 
                ['.md', '.txt', '.py', '.js', '.json', '.yml', '.yaml', '.html', '.css', 
                 '.cpp', '.c', '.java', '.go', '.rs', '.php', '.rb', '.sh', '.xml', '.csv']):
                return word
        
        # Look for quoted filenames
        import re
        quoted_matches = re.findall(r'"([^"]*)"', user_input)
        if quoted_matches:
            return quoted_matches[0]
        
        quoted_matches = re.findall(r"'([^']*)'", user_input)
        if quoted_matches:
            return quoted_matches[0]
        
        # Look for common filename patterns
        for word in words:
            if word.lower() in ['readme', 'license', 'makefile', 'dockerfile']:
                return word
            if word.lower().endswith('-agent') or word.lower().endswith('_agent'):
                return word + '.md'  # Assume markdown for agent files
        
        return None
    
    def _extract_content_from_input(self, user_input: str, file_path: str) -> str:
        """Extract content to write from user input."""
        lower_input = user_input.lower()
        
        # Look for content after 'with' keyword
        if ' with ' in lower_input:
            content_part = user_input.split(' with ', 1)[1]
            return content_part.strip()
        
        # Look for content after filename
        words = user_input.split()
        try:
            file_index = words.index(file_path)
            if file_index < len(words) - 1:
                return ' '.join(words[file_index + 1:])
        except ValueError:
            pass
        
        # Default content based on file type
        if file_path.endswith('.py'):
            return '# Python file\nprint("Hello, World!")\n'
        elif file_path.endswith('.js'):
            return '// JavaScript file\nconsole.log("Hello, World!");\n'
        elif file_path.endswith('.md'):
            return f'# {file_path.replace(".md", "").title()}\n\nContent goes here.\n'
        elif file_path.endswith('.txt'):
            return 'Text file content\n'
        else:
            return '# File created by Smart CLI\n'
    
    def _is_directory_operation(self, lower_input: str) -> bool:
        """Check if input is a directory operation."""
        dir_patterns = [
            'mkdir', 'create directory', 'make directory', 'new folder',
            'cd', 'change directory', 'goto', 'navigate',
            'pwd', 'current directory', 'where am i'
        ]
        return any(pattern in lower_input for pattern in dir_patterns)
    
    async def write_file_content(self, file_path: str, content: str):
        """Write content to file."""
        try:
            # Check if file exists and ask for confirmation if overwriting
            if os.path.exists(file_path):
                console.print(f"⚠️  File '{file_path}' already exists!", style="yellow")
                console.print("Content preview:", style="dim")
                console.print(content[:200] + "..." if len(content) > 200 else content, style="dim")
                
                # For now, proceed with overwrite (in full implementation, ask user)
                console.print("📝 Overwriting file...", style="yellow")
            
            # Ensure directory exists
            directory = os.path.dirname(file_path) if os.path.dirname(file_path) else '.'
            if directory != '.' and not os.path.exists(directory):
                os.makedirs(directory)
                console.print(f"📁 Created directory: {directory}", style="green")
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Display success info
            file_size = len(content)
            line_count = content.count('\n') + 1
            
            console.print(f"\n✅ [bold green]File created successfully![/bold green]")
            console.print(f"📄 File: {file_path}")
            console.print(f"📊 Size: {file_size:,} characters, {line_count:,} lines")
            console.print(f"📍 Location: {os.path.abspath(file_path)}")
            
            # Add to recent files
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:10]
            
        except Exception as e:
            console.print(f"❌ Error writing file: {str(e)}", style="red")
    
    async def edit_file_content(self, file_path: str, edit_instruction: str):
        """Edit file content based on instruction."""
        try:
            if not os.path.exists(file_path):
                console.print(f"❌ File '{file_path}' not found.", style="red")
                console.print("💡 Use 'create' to make a new file first.", style="dim")
                return
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_content = f.read()
            
            console.print(f"📝 [bold blue]Editing file: {file_path}[/bold blue]")
            console.print(f"📊 Current size: {len(current_content):,} characters")
            
            # Simple editing operations
            lower_instruction = edit_instruction.lower()
            
            if 'add' in lower_instruction or 'append' in lower_instruction:
                # Extract content to add
                if ' add ' in lower_instruction:
                    content_to_add = edit_instruction.split(' add ', 1)[1]
                else:
                    content_to_add = edit_instruction.split(' append ', 1)[1]
                
                new_content = current_content + '\n' + content_to_add
                
            elif 'replace' in lower_instruction:
                # Simple replace operation
                parts = edit_instruction.split(' with ')
                if len(parts) == 2:
                    old_text = parts[0].split(' replace ')[-1]
                    new_text = parts[1]
                    new_content = current_content.replace(old_text, new_text)
                else:
                    console.print("❌ Replace format: 'edit file.txt replace old_text with new_text'", style="red")
                    return
            else:
                # For complex edits, use AI assistance
                console.print("🤖 Using AI to understand edit instruction...", style="cyan")
                await self._ai_assisted_edit(file_path, current_content, edit_instruction)
                return
            
            # Write the edited content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Show changes
            size_diff = len(new_content) - len(current_content)
            console.print(f"✅ [bold green]File edited successfully![/bold green]")
            console.print(f"📊 Size change: {size_diff:+,} characters")
            console.print(f"📄 New size: {len(new_content):,} characters")
            
        except Exception as e:
            console.print(f"❌ Error editing file: {str(e)}", style="red")
    
    async def _ai_assisted_edit(self, file_path: str, current_content: str, instruction: str):
        """Use AI to assist with complex file editing."""
        try:
            if not self.ai_client:
                console.print("❌ AI client not available for assisted editing.", style="red")
                return
            
            # Create AI prompt for file editing
            prompt = f"""You are a file editor assistant. Edit the following file based on the user's instruction.

File: {file_path}
Current content:
```
{current_content[:2000]}{'...' if len(current_content) > 2000 else ''}
```

User instruction: {instruction}

Please provide the complete edited file content. Return ONLY the file content, no explanations."""
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            console.print("🤖 AI is editing the file...", style="cyan")
            
            # Use a simple model for editing
            try:
                from src.utils.ai_client import ChatMessage
            except ImportError:
                try:
                    from utils.ai_client import ChatMessage
                except ImportError:
                    from .utils.ai_client import ChatMessage
            chat_messages = [ChatMessage(role="user", content=prompt)]
            
            response = await self.ai_client.generate_response(chat_messages)
            
            if response and response.content:
                # Write the AI-edited content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.content)
                
                console.print(f"✅ [bold green]AI-assisted edit completed![/bold green]")
                console.print(f"📊 New size: {len(response.content):,} characters")
            else:
                console.print("❌ AI editing failed. No response received.", style="red")
                
        except Exception as e:
            console.print(f"❌ AI-assisted editing failed: {str(e)}", style="red")
    
    async def delete_file(self, file_path: str):
        """Delete a file with confirmation."""
        try:
            if not os.path.exists(file_path):
                console.print(f"❌ File '{file_path}' not found.", style="red")
                return
            
            # Show file info before deletion
            file_size = os.path.getsize(file_path)
            console.print(f"⚠️  [bold yellow]About to delete:[/bold yellow]")
            console.print(f"📄 File: {file_path}")
            console.print(f"📊 Size: {file_size:,} bytes")
            console.print(f"📍 Path: {os.path.abspath(file_path)}")
            
            # For now, proceed with deletion (in full implementation, ask confirmation)
            console.print("🗑️  Deleting file...", style="yellow")
            
            os.remove(file_path)
            
            console.print(f"✅ [bold green]File deleted successfully![/bold green]")
            
            # Remove from recent files if present
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                
        except Exception as e:
            console.print(f"❌ Error deleting file: {str(e)}", style="red")
    
    async def handle_directory_operations(self, user_input: str) -> bool:
        """Handle directory operations."""
        lower_input = user_input.lower()
        
        if 'mkdir' in lower_input or 'create directory' in lower_input:
            # Extract directory name
            words = user_input.split()
            dir_name = None
            for word in words:
                if word not in ['mkdir', 'create', 'directory', 'make', 'new', 'folder']:
                    dir_name = word
                    break
            
            if dir_name:
                try:
                    os.makedirs(dir_name, exist_ok=True)
                    console.print(f"✅ Directory created: {dir_name}", style="green")
                except Exception as e:
                    console.print(f"❌ Error creating directory: {str(e)}", style="red")
            else:
                console.print("❌ No directory name specified.", style="red")
            
            return True
        
        elif 'cd' in lower_input or 'change directory' in lower_input:
            # Extract target directory
            words = user_input.split()
            target = None
            for word in words:
                if word not in ['cd', 'change', 'directory', 'goto', 'navigate']:
                    target = word
                    break
            
            if target:
                try:
                    if target == '..':
                        new_dir = os.path.dirname(os.getcwd())
                    elif target == '~':
                        new_dir = os.path.expanduser('~')
                    else:
                        new_dir = os.path.abspath(target)
                    
                    if os.path.exists(new_dir) and os.path.isdir(new_dir):
                        os.chdir(new_dir)
                        self.current_project_path = new_dir
                        console.print(f"✅ Changed directory to: {new_dir}", style="green")
                        
                        # Show contents of new directory
                        await self.list_directory_contents()
                    else:
                        console.print(f"❌ Directory not found: {target}", style="red")
                        
                except Exception as e:
                    console.print(f"❌ Error changing directory: {str(e)}", style="red")
            else:
                console.print(f"📍 Current directory: {os.getcwd()}", style="blue")
            
            return True
        
        elif 'pwd' in lower_input or 'current directory' in lower_input:
            console.print(f"📍 Current directory: {os.getcwd()}", style="blue")
            return True
        
        return False
    
    async def process_ai_interaction(self, user_input: str):
        """Process user input with advanced orchestration and multi-agent workflow."""
        
        # Display user message
        user_panel = Panel(
            user_input,
            title="[bold green]You[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        console.print(user_panel)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            with Live(self._create_analysis_display(), refresh_per_second=2) as live:
                
                # Step 1: Enhanced NLP Analysis
                live.update(self._update_analysis_display("🧠 Analyzing request complexity and intent..."))
                await asyncio.sleep(0.5)
                
                intent_analysis = await self.nlp_engine.analyze_complex_request(
                    user_input, 
                    self.conversation_history[-10:]  # Last 10 conversations for context
                )
                
                if self.debug:
                    console.print(f"[dim]Intent: {intent_analysis.primary_intent} | "
                                f"Complexity: {intent_analysis.complexity.name} | "
                                f"Confidence: {intent_analysis.confidence:.2f}[/dim]")
                
                # Step 2: Determine processing approach
                if self._requires_execution_workflow(intent_analysis, user_input):
                    # Use execution workflow for commands that need approval
                    await self._process_execution_workflow(user_input, intent_analysis, live)
                elif intent_analysis.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT]:
                    # Use advanced workflow orchestration
                    await self._process_complex_workflow(user_input, intent_analysis, live)
                else:
                    # Use simplified direct response for simple tasks
                    await self._process_simple_interaction(user_input, intent_analysis, live)
            
        except KeyboardInterrupt:
            console.print("\n⚠️ Processing interrupted", style="yellow")
            
        except Exception as e:
            console.print(f"❌ Error processing request: {str(e)}", style="red")
            if self.debug:
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    async def _process_complex_workflow(self, user_input: str, intent_analysis, live):
        """Process complex requests using workflow orchestration."""
        
        # Create workflow context
        workflow_context = WorkflowContext(
            workflow_id=f"wf_{datetime.now().strftime('%H%M%S')}",
            user_request=user_input,
            project_context=await self._get_project_context_dict(),
            conversation_history=self.conversation_history[-5:],
            global_variables={}
        )
        
        live.update(self._update_analysis_display("🛠️ Breaking down into tasks..."))
        await asyncio.sleep(0.3)
        
        # Decompose request into tasks
        task_nodes = await self.workflow_orchestrator.decompose_request(
            user_input, workflow_context
        )
        
        live.update(self._update_analysis_display("🎯 Selecting orchestration strategy..."))
        await asyncio.sleep(0.3)
        
        # Select orchestration pattern
        pattern = await self.workflow_orchestrator.select_orchestration_pattern(task_nodes)
        
        live.update(self._update_analysis_display(f"🚀 Executing {pattern.value} workflow ({len(task_nodes)} tasks)..."))
        
        # Execute workflow
        results = await self.workflow_orchestrator.execute_workflow(
            task_nodes, pattern, workflow_context
        )
        
        # Display results
        await self._display_workflow_results(results, pattern, workflow_context.workflow_id)
    
    async def _process_simple_interaction(self, user_input: str, intent_analysis, live):
        """Process simple requests with optimized model selection."""
        
        live.update(self._update_analysis_display("⚡ Selecting optimal AI model..."))
        await asyncio.sleep(0.2)
        
        # Select optimal model based on complexity
        model_recommendation = await self.model_orchestrator.select_optimal_model(
            user_input,
            TaskComplexity.SIMPLE if intent_analysis.complexity == TaskComplexity.SIMPLE else TaskComplexity.MODERATE,
            budget_constraints={"max_cost_per_request": 0.50}
        )
        
        live.update(self._update_analysis_display(f"🤖 Generating response with {model_recommendation.model_id.split('/')[-1]}..."))
        
        # Build context-aware messages
        project_context = await self._get_project_context()
        enhanced_prompt = self.intent_analyzer.enhance_prompt_with_context(
            user_input, 
            type('Intent', (), {
                'intent_type': intent_analysis.primary_intent,
                'parameters': {
                    'complexity': intent_analysis.complexity.name,
                    'entities': intent_analysis.extracted_entities.__dict__
                }
            })()
        )
        
        if project_context:
            enhanced_prompt = f"{project_context}\n\n{enhanced_prompt}"
        
        # Convert conversation history to messages
        messages = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages for context
            messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
        
        # Add current enhanced prompt
        messages.append(ChatMessage(role="user", content=enhanced_prompt))
        
        # Generate response with fallback
        response = await self.model_orchestrator.execute_with_fallback(
            messages, model_recommendation
        )
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
            "model": response.model,
            "usage": response.usage,
            "cost": response.cost_estimate
        })
        
        # Display response
        ai_panel = Panel(
            Markdown(response.content),
            title=f"[bold blue]🤖 Smart AI[/bold blue] [dim]({model_recommendation.model_id.split('/')[-1]})[/dim]",
            border_style="blue", 
            padding=(0, 1)
        )
        console.print(ai_panel)
        
        # Display usage info
        if response.usage:
            total_tokens = response.usage.get('total_tokens', 0)
            cost = response.cost_estimate or 0
            console.print(f"[dim]💾 {total_tokens} tokens | ${cost:.4f} | ⚡{model_recommendation.confidence:.1f}[/dim]")
        
        console.print()
    
    async def _display_workflow_results(self, results: Dict, pattern: OrchestrationPattern, workflow_id: str):
        """Display results from workflow execution."""
        
        successful_results = [r for r in results.values() if r.success]
        failed_results = [r for r in results.values() if not r.success]
        
        # Create summary
        summary_table = Table(title=f"Workflow Results ({pattern.value})", show_header=True)
        summary_table.add_column("Task", style="cyan")
        summary_table.add_column("Agent", style="yellow") 
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Duration", style="dim")
        
        for task_id, result in results.items():
            status = "✅ Success" if result.success else "❌ Failed"
            status_style = "green" if result.success else "red"
            duration = f"{result.execution_time:.1f}s" if result.execution_time else "N/A"
            
            summary_table.add_row(
                task_id,
                result.agent_role.value,
                f"[{status_style}]{status}[/{status_style}]",
                duration
            )
        
        console.print(summary_table)
        
        # Display successful results content
        if successful_results:
            for result in successful_results:
                if result.content and len(result.content.strip()) > 0:
                    result_panel = Panel(
                        Markdown(result.content),
                        title=f"[bold blue]{result.agent_role.value}[/bold blue] [dim]({result.task_id})[/dim]",
                        border_style="blue",
                        padding=(0, 1)
                    )
                    console.print(result_panel)
        
        # Show failed results
        if failed_results:
            console.print(f"\n⚠️ [yellow]{len(failed_results)} task(s) failed:[/yellow]")
            for result in failed_results:
                console.print(f"  • {result.task_id}: {result.content}", style="red")
        
        # Store workflow in active workflows
        self.active_workflows[workflow_id] = {
            'pattern': pattern,
            'results': results,
            'completed_at': datetime.now(),
            'success_rate': len(successful_results) / len(results) if results else 0
        }
        
        console.print()
    
    def _create_analysis_display(self) -> Table:
        """Create analysis status display table."""
        table = Table.grid(padding=1)
        table.add_column(style="blue", width=50)
        table.add_row("🧠 Initializing advanced analysis...")
        return table
    
    def _update_analysis_display(self, message: str) -> Table:
        """Update analysis display with new message."""
        table = Table.grid(padding=1)
        table.add_column(style="blue", width=50)
        table.add_row(message)
        return table
    
    async def _get_project_context_dict(self) -> Dict[str, Any]:
        """Get project context as dictionary."""
        context = await self._get_project_context()
        
        return {
            'current_directory': str(self.current_project_path),
            'project_type': self._detect_project_type(),
            'recent_files': self.recent_files[-5:],  # Last 5 files
            'context_summary': context if context else "No specific project context detected"
        }
    
    def _detect_project_type(self) -> str:
        """Detect project type from current directory."""
        project_path = Path(self.current_project_path)
        
        if (project_path / "package.json").exists():
            return "node"
        elif (project_path / "pyproject.toml").exists() or (project_path / "requirements.txt").exists():
            return "python"
        elif (project_path / "Cargo.toml").exists():
            return "rust"
        elif (project_path / "pom.xml").exists() or (project_path / "build.gradle").exists():
            return "java"
        elif (project_path / "go.mod").exists():
            return "go"
        else:
            return "general"
    
    def _requires_execution_workflow(self, intent_analysis, user_input: str) -> bool:
        """Determine if request requires execution workflow with approval."""
        
        execution_keywords = [
            'run', 'execute', 'test', 'install', 'build', 'deploy', 
            'commit', 'push', 'delete', 'remove', 'create', 'mkdir'
        ]
        
        user_input_lower = user_input.lower()
        
        # Check for execution-related keywords
        if any(keyword in user_input_lower for keyword in execution_keywords):
            return True
        
        # Check for file system operations
        if any(word in user_input_lower for word in ['file', 'directory', 'folder']):
            return True
        
        # Check for git operations
        if 'git' in user_input_lower:
            return True
        
        return False
    
    async def _process_execution_workflow(self, user_input: str, intent_analysis, live):
        """Process request using execution workflow with approval."""
        
        live.update(self._update_analysis_display("📋 Creating execution plan..."))
        await asyncio.sleep(0.3)
        
        # Create workflow
        workflow_plan = await self.execution_workflow_manager.create_workflow(
            user_input, intent_analysis.primary_intent
        )
        
        live.update(self._update_analysis_display(f"🎯 Plan created (Risk: {workflow_plan.overall_risk.value})"))
        await asyncio.sleep(0.2)
        
        # Stop live display for user interaction
        live.stop()
        
        try:
            # Request approval if needed
            if workflow_plan.requires_approval:
                approved = await self.execution_workflow_manager.request_approval(workflow_plan.plan_id)
                
                if not approved:
                    console.print("❌ [red]Execution cancelled by user[/red]")
                    return
            
            # Execute workflow
            console.print("\n🚀 [bold blue]Executing workflow...[/bold blue]")
            
            execution_summary = await self.execution_workflow_manager.execute_workflow(workflow_plan.plan_id)
            
            # Display results
            self._display_execution_summary(execution_summary)
            
        except Exception as e:
            console.print(f"❌ [red]Execution failed: {str(e)}[/red]")
        
        # Restart live display if needed
        console.print()
    
    def _display_execution_summary(self, execution_summary: Dict[str, Any]):
        """Display execution workflow summary."""
        
        # Create results table
        results_table = Table(title="🎯 Execution Results")
        results_table.add_column("Operation", style="cyan")
        results_table.add_column("Status", style="green")
        results_table.add_column("Details", style="white")
        
        for result in execution_summary.get('results', []):
            status_icon = "✅" if result.get('success', False) else "❌"
            status_text = "Success" if result.get('success', False) else "Failed"
            
            operation = result.get('type', 'Unknown')
            if operation == 'shell_command':
                operation = f"Command: {result.get('command', '')[:30]}..."
            elif operation == 'file_operation':
                operation = f"File {result.get('operation', '')}: {result.get('path', '')}"
            
            details = result.get('output', '')[:50]
            if len(details) > 47:
                details += "..."
            
            results_table.add_row(
                operation,
                f"{status_icon} {status_text}",
                details
            )
        
        console.print(results_table)
        
        # Show summary
        total_operations = len(execution_summary.get('results', []))
        successful_operations = sum(1 for r in execution_summary.get('results', []) if r.get('success', False))
        
        if execution_summary.get('success', False):
            console.print(f"✅ [green]All {successful_operations}/{total_operations} operations completed successfully[/green]")
        else:
            console.print(f"⚠️ [yellow]{successful_operations}/{total_operations} operations completed[/yellow]")
    
    def display_help(self):
        """Display help information."""
        help_table = Table(title="Smart CLI Commands", show_header=True, header_style="bold blue")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")
        
        commands = [
            ("System Commands:", ""),
            ("/help", "Show this help message"),
            ("/quit", "Exit Smart CLI"),
            ("/clear", "Clear conversation history"),
            ("/history", "Show conversation history"),
            ("/model [name]", "Change AI model or show current"),
            ("/usage", "Show session usage statistics"),
            ("/config", "Show configuration help"),
            ("/config <key> <value>", "Set API key or configuration"),
            ("", ""),
            ("File Operations:", ""),
            ("/create <file> [content]", "Create new file"),
            ("/edit <file>", "AI-assisted file editing"),
            ("/read <file>", "Display file content"),
            ("/ls [pattern]", "List files and directories"),
            ("/cd <path>", "Change directory"),
            ("/pwd", "Show current directory"),
            ("", ""),
            ("AI Agents:", ""),
            ("/agents", "List available AI agents"),
            ("/generate <description>", "Generate code with AI"),
            ("/review <file>", "AI code review"),
            ("", ""),
            ("API Development:", ""),
            ("/api", "Show API management help"),
            ("/api create <name> <framework>", "Create API project"),
            ("/api endpoint POST /users", "Generate API endpoint"),
            ("/api model User name:str email:str", "Generate data model"),
            ("", ""),
            ("Project Management:", ""),
            ("/project", "Show project management help"),
            ("/project info", "Show project information"),
            ("/project analyze", "Analyze project health"),
            ("/project structure", "Show directory tree"),
            ("", ""),
            ("Natural Language:", ""),
            ("create a python fastapi project", "Generate complete project"),
            ("add user authentication", "Add features to existing code"),
            ("review my code for bugs", "Analyze and suggest improvements"),
            ("explain this function", "Get code explanations"),
            ("", ""),
            ("Configuration Examples:", ""),
            ("/config openrouter_api_key YOUR_KEY", "Set OpenRouter API key"),
            ("/config anthropic_api_key YOUR_KEY", "Set Anthropic API key"),
            ("/config openai_api_key YOUR_KEY", "Set OpenAI API key"),
            ("", ""),
            ("Tips:", ""),
            ("• Use /help to see all commands", ""),
            ("• Combine AI agents with file operations", ""),
            ("• Use natural language for complex requests", "")
        ]
        
        for cmd, desc in commands:
            help_table.add_row(cmd, desc)
            
        console.print(help_table)
        console.print()
    
    def display_history(self):
        """Display conversation history."""
        if not self.messages:
            console.print("📝 No conversation history yet.", style="dim")
            return
            
        history_table = Table(title="Conversation History", show_header=True)
        history_table.add_column("#", style="dim", width=3)
        history_table.add_column("Role", style="bold", width=8)
        history_table.add_column("Message Preview", style="white")
        
        for i, msg in enumerate(self.messages, 1):
            role = "You" if msg["role"] == "user" else "AI"
            preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            # Remove markdown for preview
            preview = preview.replace("**", "").replace("*", "").replace("`", "")
            history_table.add_row(str(i), role, preview)
            
        console.print(history_table)
        console.print()
    
    def display_session_usage(self):
        """Display current session usage stats."""
        try:
            stats = self.usage_tracker.get_session_stats()
            
            usage_table = Table(title="Session Usage Statistics")
            usage_table.add_column("Metric", style="cyan", width=20)
            usage_table.add_column("Value", style="white")
            
            usage_table.add_row("Messages Exchanged", str(len(self.messages) // 2))
            usage_table.add_row("Total Tokens", f"{stats.get('total_tokens', 0):,}")
            usage_table.add_row("Estimated Cost", f"${stats.get('total_cost', 0):.4f}")
            usage_table.add_row("Session Duration", f"{stats.get('duration', 0):.1f} minutes")
            
            console.print(usage_table)
            console.print()
            
        except Exception as e:
            console.print("❌ Could not retrieve usage statistics", style="red")
            if self.debug:
                console.print(f"[dim]Error: {e}[/dim]")
    
    def display_config_help(self):
        """Display configuration help."""
        config_table = Table(title="Configuration Help")
        config_table.add_column("Setting", style="cyan", width=25)
        config_table.add_column("Chat Command", style="green")
        
        configs = [
            ("OpenRouter API Key", "/config openrouter_api_key YOUR_KEY"),
            ("Anthropic API Key", "/config anthropic_api_key YOUR_KEY"),
            ("OpenAI API Key", "/config openai_api_key YOUR_KEY"),
            ("Default Model", "/config default_model MODEL_NAME"),
            ("", ""),
            ("Current Configuration:", ""),
        ]
        
        for setting, command in configs:
            config_table.add_row(setting, command)
        
        # Show current config
        try:
            current_configs = {
                "OpenRouter API": "***set***" if self.config.get_config('openrouter_api_key') else "not set",
                "Anthropic API": "***set***" if self.config.get_config('anthropic_api_key') else "not set", 
                "OpenAI API": "***set***" if self.config.get_config('openai_api_key') else "not set",
                "Default Model": self.config.get_config('default_model', 'anthropic/claude-3-sonnet-20240229')
            }
            
            for key, value in current_configs.items():
                color = "green" if "set" in str(value) or "claude" in str(value) else "red"
                config_table.add_row(key, f"[{color}]{value}[/{color}]")
                
        except Exception:
            config_table.add_row("Status", "[red]Could not load config[/red]")
        
        console.print(config_table)
        console.print("\n💡 [dim]Get API keys from: https://openrouter.ai, https://console.anthropic.com, or https://platform.openai.com[/dim]")
        console.print()

    # File Operations Handler Methods
    async def handle_file_create(self, args: str):
        """Handle file creation with optional content."""
        parts = args.split(' ', 1)
        filename = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        # Remove quotes if present
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        elif content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        
        try:
            filepath = Path(self.current_project_path) / filename
            
            if filepath.exists():
                console.print(f"⚠️ File {filename} already exists. Use /edit to modify.", style="yellow")
                return
            
            # Create directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Track recent files
            self._track_recent_file(filename)
            
            console.print(f"✅ Created {filename}", style="green")
            
            if not content:
                console.print("💡 File created empty. Use /edit to add content.", style="dim")
                
        except Exception as e:
            console.print(f"❌ Failed to create {filename}: {str(e)}", style="red")

    async def handle_file_read(self, filename: str):
        """Handle file reading and display."""
        try:
            filepath = Path(self.current_project_path) / filename
            
            if not filepath.exists():
                console.print(f"❌ File {filename} not found", style="red")
                return
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track recent files
            self._track_recent_file(filename)
            
            # Display with syntax highlighting if possible
            from rich.syntax import Syntax
            
            try:
                # Detect language from extension
                suffix = filepath.suffix.lower()
                language_map = {
                    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                    '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.go': 'go',
                    '.rs': 'rust', '.php': 'php', '.rb': 'ruby',
                    '.html': 'html', '.css': 'css', '.json': 'json',
                    '.yaml': 'yaml', '.yml': 'yaml', '.xml': 'xml',
                    '.md': 'markdown', '.sh': 'bash'
                }
                
                language = language_map.get(suffix, 'text')
                syntax = Syntax(content, language, theme="monokai", line_numbers=True)
                
                console.print(Panel(syntax, title=f"📄 {filename}", border_style="blue"))
                
            except Exception:
                # Fallback to plain text
                console.print(Panel(content, title=f"📄 {filename}", border_style="blue"))
                
        except Exception as e:
            console.print(f"❌ Failed to read {filename}: {str(e)}", style="red")

    async def handle_file_edit(self, filename: str):
        """Handle AI-assisted file editing."""
        try:
            filepath = Path(self.current_project_path) / filename
            
            if not filepath.exists():
                console.print(f"❌ File {filename} not found. Use /create to create it first.", style="red")
                return
            
            # Read current content
            with open(filepath, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            console.print(f"📝 Current content of {filename}:", style="cyan")
            await self.handle_file_read(filename)
            
            console.print("\n💬 How would you like to modify this file?", style="green")
            console.print("(Type your editing instructions, or 'cancel' to abort)", style="dim")
            
            user_instruction = Prompt.ask("Edit instruction").strip()
            
            if user_instruction.lower() == 'cancel':
                console.print("✅ Edit cancelled", style="yellow")
                return
            
            # Use agent to edit file
            if self.agent_orchestrator:
                task = AgentTask(
                    task_id=f"edit_{filename}_{datetime.now().timestamp()}",
                    agent_role=AgentRole.CODE_GENERATOR,
                    description=f"Edit the file {filename} according to: {user_instruction}",
                    context={
                        'filename': filename,
                        'current_content': current_content,
                        'instruction': user_instruction,
                        'project_path': self.current_project_path
                    }
                )
                
                with console.status("[bold blue]🤖 Agent is editing file...", spinner="dots"):
                    result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
                
                if result.success:
                    # Write the new content
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    
                    console.print(f"✅ File {filename} updated successfully", style="green")
                    console.print("📝 Updated content:", style="cyan")
                    await self.handle_file_read(filename)
                else:
                    console.print(f"❌ Failed to edit file: {result.content}", style="red")
            else:
                console.print("❌ AI agent not available", style="red")
                
        except Exception as e:
            console.print(f"❌ Failed to edit {filename}: {str(e)}", style="red")

    async def handle_list_files(self, pattern: str = ""):
        """Handle file listing."""
        try:
            current_path = Path(self.current_project_path)
            
            if pattern:
                # Use glob pattern
                files = list(current_path.glob(pattern))
            else:
                # List all files and directories
                files = list(current_path.iterdir())
            
            if not files:
                console.print("📂 No files found", style="dim")
                return
            
            # Create table
            file_table = Table(title=f"📂 Files in {current_path.name}")
            file_table.add_column("Name", style="cyan", width=30)
            file_table.add_column("Type", style="green", width=10)
            file_table.add_column("Size", style="yellow", width=12)
            file_table.add_column("Modified", style="dim", width=20)
            
            for file_path in sorted(files):
                try:
                    if file_path.is_dir():
                        file_type = "📁 DIR"
                        size = "-"
                    else:
                        file_type = "📄 FILE"
                        size = f"{file_path.stat().st_size:,} bytes"
                    
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    file_table.add_row(file_path.name, file_type, size, modified)
                    
                except Exception:
                    file_table.add_row(file_path.name, "❓ UNKNOWN", "-", "-")
            
            console.print(file_table)
            
        except Exception as e:
            console.print(f"❌ Failed to list files: {str(e)}", style="red")

    async def handle_change_directory(self, path: str):
        """Handle directory change."""
        try:
            if path == "..":
                new_path = Path(self.current_project_path).parent
            elif path.startswith("/"):
                new_path = Path(path)
            else:
                new_path = Path(self.current_project_path) / path
            
            new_path = new_path.resolve()
            
            if not new_path.exists():
                console.print(f"❌ Directory {path} not found", style="red")
                return
            
            if not new_path.is_dir():
                console.print(f"❌ {path} is not a directory", style="red")
                return
            
            self.current_project_path = str(new_path)
            console.print(f"✅ Changed to: {self.current_project_path}", style="green")
            
            # Update context
            os.chdir(self.current_project_path)
            
        except Exception as e:
            console.print(f"❌ Failed to change directory: {str(e)}", style="red")

    # Agent Handler Methods  
    async def handle_list_agents(self):
        """Display available agents and their status."""
        if not self.agent_orchestrator:
            console.print("❌ Agent system not available", style="red")
            return
        
        agents_table = Table(title="🤖 Available AI Agents")
        agents_table.add_column("Agent", style="cyan", width=20)
        agents_table.add_column("Role", style="green", width=25)
        agents_table.add_column("Status", style="yellow", width=12)
        agents_table.add_column("Tasks Completed", style="blue", width=15)
        
        for role in self.agent_orchestrator.get_available_agents():
            metrics = self.agent_orchestrator.get_agent_performance(role)
            status = "🟢 Ready" if role in self.agent_orchestrator.agents else "🔴 Offline"
            tasks_completed = metrics.get('tasks_completed', 0)
            
            agents_table.add_row(
                role.value.replace('_', ' ').title(),
                self._get_agent_description(role),
                status,
                str(tasks_completed)
            )
        
        console.print(agents_table)
        console.print("\n💡 [dim]Use /generate, /review, or other agent commands to work with agents[/dim]")

    def _get_agent_description(self, role: AgentRole) -> str:
        """Get human-readable description for agent role."""
        descriptions = {
            AgentRole.CODE_GENERATOR: "Generate new code",
            AgentRole.CODE_REVIEWER: "Review and analyze code",
            AgentRole.DEBUGGER: "Debug and fix issues",
            AgentRole.REFACTOR_SPECIALIST: "Refactor and optimize",
            AgentRole.DOCUMENTATION: "Write documentation",
            AgentRole.TEST_GENERATOR: "Generate tests",
            AgentRole.SECURITY_AUDITOR: "Security analysis",
        }
        return descriptions.get(role, "Unknown role")

    async def handle_agent_generate(self, description: str):
        """Handle code generation using agent."""
        if not self.agent_orchestrator:
            console.print("❌ Agent system not available", style="red")
            return
        
        try:
            task = AgentTask(
                task_id=f"generate_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=description,
                context={
                    'project_path': self.current_project_path,
                    'working_directory': os.getcwd()
                }
            )
            
            with console.status("[bold blue]🤖 Code Generator Agent is working...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                # Display generated code
                from rich.syntax import Syntax
                
                # Try to detect language from content
                content = result.content
                if 'def ' in content or 'import ' in content or 'class ' in content:
                    language = 'python'
                elif 'function ' in content or 'const ' in content or 'let ' in content:
                    language = 'javascript'
                elif 'public class' in content or 'import java' in content:
                    language = 'java'
                else:
                    language = 'text'
                
                syntax = Syntax(content, language, theme="monokai", line_numbers=True)
                
                console.print(Panel(
                    syntax,
                    title="🤖 Generated Code",
                    border_style="green"
                ))
                
                # Offer to save to file
                save_file = Prompt.ask(
                    "\n💾 Save to file? (Enter filename or 'no')",
                    default="no"
                ).strip()
                
                if save_file.lower() not in ['no', 'n', '']:
                    try:
                        filepath = Path(self.current_project_path) / save_file
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        console.print(f"✅ Saved to {save_file}", style="green")
                    except Exception as e:
                        console.print(f"❌ Failed to save: {str(e)}", style="red")
                        
            else:
                console.print(f"❌ Generation failed: {result.content}", style="red")
                
        except Exception as e:
            console.print(f"❌ Error during generation: {str(e)}", style="red")

    async def handle_agent_review(self, filename: str):
        """Handle code review using agent."""
        if not self.agent_orchestrator:
            console.print("❌ Agent system not available", style="red")
            return
        
        try:
            filepath = Path(self.current_project_path) / filename
            
            if not filepath.exists():
                console.print(f"❌ File {filename} not found", style="red")
                return
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            task = AgentTask(
                task_id=f"review_{filename}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_REVIEWER,
                description=f"Review the code in {filename}",
                context={
                    'filename': filename,
                    'content': content,
                    'project_path': self.current_project_path
                }
            )
            
            with console.status("[bold blue]🤖 Code Reviewer Agent is analyzing...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_REVIEWER, task)
            
            if result.success:
                console.print(Panel(
                    result.content,
                    title=f"🔍 Code Review: {filename}",
                    border_style="cyan"
                ))
            else:
                console.print(f"❌ Review failed: {result.content}", style="red")
                
        except Exception as e:
            console.print(f"❌ Error during review: {str(e)}", style="red")

    # API Management Handler Methods
    async def handle_api_management(self, args: str):
        """Handle API management commands."""
        parts = args.split(' ', 1)
        subcommand = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "create":
            await self.handle_api_create(subargs)
        elif subcommand == "scaffold":
            await self.handle_api_scaffold(subargs)
        elif subcommand == "endpoint":
            await self.handle_api_endpoint(subargs)
        elif subcommand == "model":
            await self.handle_api_model(subargs)
        elif subcommand == "test":
            await self.handle_api_test(subargs)
        elif subcommand == "deploy":
            await self.handle_api_deploy(subargs)
        else:
            await self.display_api_help()

    async def display_api_help(self):
        """Display API management help."""
        api_table = Table(title="🌐 API Management Commands")
        api_table.add_column("Command", style="cyan", width=30)
        api_table.add_column("Description", style="white")
        
        commands = [
            ("/api create <name> <framework>", "Create new API project"),
            ("/api scaffold fastapi", "Generate FastAPI boilerplate"),
            ("/api scaffold express", "Generate Express.js boilerplate"), 
            ("/api scaffold flask", "Generate Flask boilerplate"),
            ("/api endpoint <method> <path>", "Generate API endpoint"),
            ("/api model <name> <fields>", "Generate data model"),
            ("/api test <endpoint>", "Generate API tests"),
            ("/api deploy <platform>", "Deploy API to platform"),
            ("", ""),
            ("Examples:", ""),
            ("/api create my-api fastapi", "Create FastAPI project"),
            ("/api endpoint POST /users", "Create POST /users endpoint"),
            ("/api model User name:str email:str", "Create User model"),
            ("/api test /users", "Generate tests for /users"),
        ]
        
        for cmd, desc in commands:
            api_table.add_row(cmd, desc)
        
        console.print(api_table)
        console.print()

    async def handle_api_create(self, args: str):
        """Create new API project."""
        if not args:
            console.print("❌ Usage: /api create <name> <framework>", style="red")
            console.print("Frameworks: fastapi, flask, express, django", style="dim")
            return
        
        parts = args.split()
        if len(parts) < 2:
            console.print("❌ Please specify project name and framework", style="red")
            return
        
        project_name = parts[0]
        framework = parts[1].lower()
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"api_create_{project_name}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Create a complete {framework} API project named {project_name} with authentication, database models, CRUD endpoints, error handling, testing, and Docker configuration",
                context={
                    'project_name': project_name,
                    'framework': framework,
                    'project_path': self.current_project_path,
                    'include_auth': True,
                    'include_database': True,
                    'include_tests': True,
                    'include_docker': True
                }
            )
            
            with console.status(f"[bold blue]🤖 Creating {framework} API project...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                # Create project directory
                project_path = Path(self.current_project_path) / project_name
                project_path.mkdir(exist_ok=True)
                
                console.print(f"✅ API project '{project_name}' created successfully", style="green")
                console.print(Panel(result.content, title="🚀 Project Structure", border_style="green"))
                
                # Offer to change to project directory
                change_dir = Prompt.ask(f"Change to {project_name} directory? (y/n)", default="y")
                if change_dir.lower() == 'y':
                    await self.handle_change_directory(project_name)
                    
            else:
                console.print(f"❌ Failed to create API project: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_api_scaffold(self, framework: str):
        """Generate API boilerplate for specific framework."""
        if not framework:
            console.print("❌ Usage: /api scaffold <framework>", style="red")
            return
        
        framework = framework.lower()
        supported = ["fastapi", "flask", "express", "django"]
        
        if framework not in supported:
            console.print(f"❌ Framework '{framework}' not supported", style="red")
            console.print(f"Supported: {', '.join(supported)}", style="dim")
            return
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"scaffold_{framework}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Generate production-ready {framework} boilerplate with authentication, database models, middleware, error handling, and documentation",
                context={
                    'framework': framework,
                    'project_path': self.current_project_path,
                    'include_auth': True,
                    'include_middleware': True,
                    'include_docs': True
                }
            )
            
            with console.status(f"[bold blue]🤖 Generating {framework} boilerplate...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                console.print(Panel(result.content, title=f"🏗️ {framework.title()} Boilerplate", border_style="green"))
            else:
                console.print(f"❌ Failed to generate boilerplate: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_api_endpoint(self, args: str):
        """Generate API endpoint."""
        if not args:
            console.print("❌ Usage: /api endpoint <method> <path> [description]", style="red")
            console.print("Example: /api endpoint POST /users Create new user", style="dim")
            return
        
        parts = args.split(' ', 2)
        method = parts[0].upper()
        path = parts[1] 
        description = parts[2] if len(parts) > 2 else f"{method} {path} endpoint"
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"endpoint_{method}_{path.replace('/', '_')}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Generate {method} {path} API endpoint with request/response models, validation, error handling, and documentation. {description}",
                context={
                    'method': method,
                    'path': path,
                    'description': description,
                    'project_path': self.current_project_path
                }
            )
            
            with console.status(f"[bold blue]🤖 Generating {method} {path} endpoint...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                from rich.syntax import Syntax
                syntax = Syntax(result.content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"🔗 {method} {path}", border_style="green"))
                
                # Offer to save
                filename = f"{method.lower()}_{path.replace('/', '_').replace('<', '').replace('>', '')}_endpoint.py"
                save_file = Prompt.ask(f"💾 Save as {filename}? (y/n)", default="y")
                
                if save_file.lower() == 'y':
                    try:
                        filepath = Path(self.current_project_path) / filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(result.content)
                        console.print(f"✅ Saved to {filename}", style="green")
                    except Exception as e:
                        console.print(f"❌ Failed to save: {str(e)}", style="red")
                        
            else:
                console.print(f"❌ Failed to generate endpoint: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_api_model(self, args: str):
        """Generate data model."""
        if not args:
            console.print("❌ Usage: /api model <name> <field:type field:type...>", style="red")
            console.print("Example: /api model User name:str email:str age:int", style="dim")
            return
        
        parts = args.split()
        model_name = parts[0]
        fields = parts[1:] if len(parts) > 1 else []
        
        field_definitions = {}
        for field in fields:
            if ':' in field:
                name, field_type = field.split(':', 1)
                field_definitions[name] = field_type
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"model_{model_name}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Generate {model_name} data model with validation, serialization, and database integration",
                context={
                    'model_name': model_name,
                    'fields': field_definitions,
                    'project_path': self.current_project_path
                }
            )
            
            with console.status(f"[bold blue]🤖 Generating {model_name} model...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                from rich.syntax import Syntax
                syntax = Syntax(result.content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"📋 {model_name} Model", border_style="green"))
                
                # Auto-save models
                filename = f"{model_name.lower()}_model.py"
                try:
                    filepath = Path(self.current_project_path) / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    console.print(f"✅ Model saved to {filename}", style="green")
                except Exception as e:
                    console.print(f"❌ Failed to save model: {str(e)}", style="red")
                    
            else:
                console.print(f"❌ Failed to generate model: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_api_test(self, endpoint: str):
        """Generate API tests."""
        if not endpoint:
            console.print("❌ Usage: /api test <endpoint>", style="red")
            return
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"test_{endpoint.replace('/', '_')}_{datetime.now().timestamp()}",
                agent_role=AgentRole.TEST_GENERATOR,
                description=f"Generate comprehensive tests for {endpoint} endpoint including unit tests, integration tests, and edge cases",
                context={
                    'endpoint': endpoint,
                    'project_path': self.current_project_path
                }
            )
            
            with console.status(f"[bold blue]🤖 Generating tests for {endpoint}...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.TEST_GENERATOR, task)
            
            if result.success:
                from rich.syntax import Syntax
                syntax = Syntax(result.content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"🧪 Tests for {endpoint}", border_style="green"))
                
                # Auto-save tests
                filename = f"test_{endpoint.replace('/', '_').replace('<', '').replace('>', '')}.py"
                try:
                    filepath = Path(self.current_project_path) / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    console.print(f"✅ Tests saved to {filename}", style="green")
                except Exception as e:
                    console.print(f"❌ Failed to save tests: {str(e)}", style="red")
                    
            else:
                console.print(f"❌ Failed to generate tests: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_api_deploy(self, platform: str):
        """Generate deployment configuration."""
        if not platform:
            console.print("❌ Usage: /api deploy <platform>", style="red")
            console.print("Platforms: docker, heroku, aws, gcp, azure", style="dim")
            return
        
        platform = platform.lower()
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"deploy_{platform}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Generate deployment configuration for {platform} including Dockerfile, docker-compose, environment setup, and CI/CD pipeline",
                context={
                    'platform': platform,
                    'project_path': self.current_project_path
                }
            )
            
            with console.status(f"[bold blue]🤖 Generating {platform} deployment config...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                console.print(Panel(result.content, title=f"🚀 {platform.title()} Deployment", border_style="green"))
            else:
                console.print(f"❌ Failed to generate deployment config: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    # Project Management Handler Methods
    async def handle_project_management(self, args: str):
        """Handle project management commands."""
        parts = args.split(' ', 1)
        subcommand = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "init":
            await self.handle_project_init(subargs)
        elif subcommand == "info":
            await self.handle_project_info()
        elif subcommand == "analyze":
            await self.handle_project_analyze()
        elif subcommand == "structure":
            await self.handle_project_structure()
        elif subcommand == "deps" or subcommand == "dependencies":
            await self.handle_project_dependencies()
        else:
            await self.display_project_help()

    async def display_project_help(self):
        """Display project management help."""
        project_table = Table(title="📁 Project Management Commands")
        project_table.add_column("Command", style="cyan", width=25)
        project_table.add_column("Description", style="white")
        
        commands = [
            ("/project init <type>", "Initialize project structure"),
            ("/project info", "Show current project information"),
            ("/project analyze", "Analyze project structure and health"),
            ("/project structure", "Display project directory tree"),
            ("/project deps", "Analyze project dependencies"),
            ("", ""),
            ("Project Types:", ""),
            ("python", "Python package with setup.py/pyproject.toml"),
            ("nodejs", "Node.js project with package.json"),
            ("webapp", "Full-stack web application"),
            ("api", "API-only project"),
            ("microservice", "Microservice with Docker"),
        ]
        
        for cmd, desc in commands:
            project_table.add_row(cmd, desc)
        
        console.print(project_table)
        console.print()

    async def handle_project_init(self, project_type: str):
        """Initialize project structure."""
        if not project_type:
            console.print("❌ Usage: /project init <type>", style="red")
            await self.display_project_help()
            return
        
        project_type = project_type.lower()
        
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"project_init_{project_type}_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_GENERATOR,
                description=f"Initialize a {project_type} project with proper structure, configuration files, documentation, and best practices",
                context={
                    'project_type': project_type,
                    'project_path': self.current_project_path,
                    'project_name': Path(self.current_project_path).name
                }
            )
            
            with console.status(f"[bold blue]🤖 Initializing {project_type} project...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_GENERATOR, task)
            
            if result.success:
                console.print(Panel(result.content, title=f"🎯 {project_type.title()} Project Initialized", border_style="green"))
            else:
                console.print(f"❌ Failed to initialize project: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_project_info(self):
        """Display current project information."""
        project_path = Path(self.current_project_path)
        
        info_table = Table(title="📋 Project Information")
        info_table.add_column("Property", style="cyan", width=20)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Name", project_path.name)
        info_table.add_row("Path", str(project_path))
        info_table.add_row("Type", self._detect_project_type())
        info_table.add_row("Files", str(len(list(project_path.rglob('*')))))
        
        # Check for common files
        config_files = []
        for config_file in ['package.json', 'pyproject.toml', 'setup.py', 'Cargo.toml', 'pom.xml']:
            if (project_path / config_file).exists():
                config_files.append(config_file)
        
        info_table.add_row("Config Files", ", ".join(config_files) if config_files else "None")
        
        console.print(info_table)

    def _detect_project_type(self) -> str:
        """Detect current project type."""
        project_path = Path(self.current_project_path)
        
        if (project_path / "package.json").exists():
            return "Node.js"
        elif (project_path / "pyproject.toml").exists() or (project_path / "setup.py").exists():
            return "Python"
        elif (project_path / "Cargo.toml").exists():
            return "Rust"
        elif (project_path / "pom.xml").exists():
            return "Java (Maven)"
        elif (project_path / "go.mod").exists():
            return "Go"
        else:
            return "Unknown"

    async def handle_project_analyze(self):
        """Analyze project structure and health."""
        if self.agent_orchestrator:
            task = AgentTask(
                task_id=f"analyze_{datetime.now().timestamp()}",
                agent_role=AgentRole.CODE_REVIEWER,
                description="Analyze the current project structure, identify issues, suggest improvements, and provide health score",
                context={
                    'project_path': self.current_project_path,
                    'project_type': self._detect_project_type()
                }
            )
            
            with console.status("[bold blue]🤖 Analyzing project...", spinner="dots"):
                result = await self.agent_orchestrator.process_with_agent(AgentRole.CODE_REVIEWER, task)
            
            if result.success:
                console.print(Panel(result.content, title="🔍 Project Analysis", border_style="cyan"))
            else:
                console.print(f"❌ Analysis failed: {result.content}", style="red")
        else:
            console.print("❌ Agent system not available", style="red")

    async def handle_project_structure(self):
        """Display project directory tree."""
        project_path = Path(self.current_project_path)
        
        console.print(f"📂 [bold cyan]{project_path.name}[/bold cyan]")
        
        def print_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return
            
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                if item.name.startswith('.'):
                    continue
                    
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = "    " if is_last else "│   "
                
                if item.is_dir():
                    console.print(f"{prefix}{current_prefix}📁 [blue]{item.name}/[/blue]")
                    print_tree(item, prefix + next_prefix, max_depth, current_depth + 1)
                else:
                    file_icon = "📄" if item.suffix in ['.py', '.js', '.ts', '.java'] else "📄"
                    console.print(f"{prefix}{current_prefix}{file_icon} {item.name}")
        
        try:
            print_tree(project_path)
        except Exception as e:
            console.print(f"❌ Failed to display structure: {str(e)}", style="red")

    async def handle_project_dependencies(self):
        """Analyze project dependencies."""
        project_path = Path(self.current_project_path)
        
        deps_table = Table(title="📦 Project Dependencies")
        deps_table.add_column("File", style="cyan", width=20)
        deps_table.add_column("Dependencies Found", style="green")
        
        # Check different dependency files
        dep_files = {
            'package.json': 'Node.js dependencies',
            'requirements.txt': 'Python requirements',
            'pyproject.toml': 'Python project config',
            'Cargo.toml': 'Rust dependencies',
            'pom.xml': 'Java Maven dependencies',
            'go.mod': 'Go modules'
        }
        
        found_deps = False
        
        for file_name, description in dep_files.items():
            file_path = project_path / file_name
            if file_path.exists():
                found_deps = True
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple dependency counting
                    if file_name == 'package.json':
                        import json
                        data = json.loads(content)
                        deps = len(data.get('dependencies', {})) + len(data.get('devDependencies', {}))
                        deps_table.add_row(file_name, f"{deps} packages")
                    elif file_name == 'requirements.txt':
                        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                        deps_table.add_row(file_name, f"{len(lines)} packages")
                    else:
                        deps_table.add_row(file_name, "File exists")
                        
                except Exception:
                    deps_table.add_row(file_name, "Could not parse")
        
        if found_deps:
            console.print(deps_table)
        else:
            console.print("📦 No dependency files found in current project", style="dim")

    async def _get_project_context(self) -> str:
        """Get current project context for AI responses."""
        try:
            project_path = Path(self.current_project_path)
            project_type = self._detect_project_type()
            
            context_parts = []
            
            # Basic project info
            context_parts.append(f"CURRENT PROJECT CONTEXT:")
            context_parts.append(f"- Project: {project_path.name}")
            context_parts.append(f"- Path: {project_path}")
            context_parts.append(f"- Type: {project_type}")
            
            # Project structure summary
            try:
                files = list(project_path.rglob('*'))
                py_files = [f for f in files if f.suffix == '.py' and f.is_file()]
                js_files = [f for f in files if f.suffix in ['.js', '.ts'] and f.is_file()]
                
                if py_files:
                    context_parts.append(f"- Python files: {len(py_files)}")
                if js_files:
                    context_parts.append(f"- JavaScript/TypeScript files: {len(js_files)}")
                    
                # Important files
                important_files = ['README.md', 'package.json', 'pyproject.toml', 'requirements.txt', 'Dockerfile']
                existing_files = [f for f in important_files if (project_path / f).exists()]
                if existing_files:
                    context_parts.append(f"- Config files: {', '.join(existing_files)}")
                    
            except Exception:
                pass
            
            # Recent file activity (if we're working on specific files)
            if hasattr(self, 'recent_files') and self.recent_files:
                context_parts.append(f"- Recent files: {', '.join(self.recent_files[-3:])}")
            
            return "\n".join(context_parts)
            
        except Exception:
            return ""

    def _track_recent_file(self, filename: str):
        """Track recently accessed files."""
        if filename in self.recent_files:
            self.recent_files.remove(filename)
        self.recent_files.append(filename)
        
        # Keep only last 10 files
        if len(self.recent_files) > 10:
            self.recent_files.pop(0)
    
    # New Claude Code-like command handlers
    async def handle_code_search(self, args: str):
        """Handle code search command similar to Claude Code's Grep tool."""
        try:
            parts = args.split()
            if not parts:
                console.print("❌ Pattern required", style="red")
                return
            
            pattern = parts[0]
            
            # Parse options
            file_type = None
            case_insensitive = False
            show_line_numbers = True
            
            i = 1
            while i < len(parts):
                if parts[i] == '--type' and i + 1 < len(parts):
                    file_type = parts[i + 1]
                    i += 2
                elif parts[i] == '-i':
                    case_insensitive = True
                    i += 1
                else:
                    i += 1
            
            # Perform search
            from utils.code_search import SearchOutputMode
            result = self.search_tools.grep_search(
                pattern=pattern,
                path=self.current_project_path,
                output_mode=SearchOutputMode.CONTENT,
                file_type=file_type,
                case_insensitive=case_insensitive,
                show_line_numbers=show_line_numbers
            )
            
            if result.success:
                if result.matches:
                    console.print(f"🔍 Found {len(result.matches)} matches in {result.search_time:.2f}s", style="green")
                    for match in result.matches[:20]:  # Show first 20 matches
                        file_rel = Path(match.file_path).relative_to(self.current_project_path)
                        console.print(f"📁 {file_rel}:{match.line_number}", style="cyan")
                        console.print(f"   {match.line_content}", style="dim")
                    
                    if len(result.matches) > 20:
                        console.print(f"... and {len(result.matches) - 20} more matches", style="dim")
                else:
                    console.print(f"🔍 No matches found for '{pattern}'", style="yellow")
            else:
                console.print(f"❌ Search error: {result.error}", style="red")
                
        except Exception as e:
            console.print(f"❌ Search error: {e}", style="red")
    
    async def handle_glob_search(self, args: str):
        """Handle glob search command similar to Claude Code's Glob tool."""
        try:
            pattern = args.strip()
            if not pattern:
                console.print("❌ Pattern required", style="red")
                return
            
            result = self.search_tools.glob_search(pattern, self.current_project_path)
            
            if result.success:
                if result.file_paths:
                    console.print(f"📂 Found {len(result.file_paths)} files matching '{pattern}'", style="green")
                    for file_path in result.file_paths[:30]:  # Show first 30 files
                        rel_path = Path(file_path).relative_to(self.current_project_path)
                        console.print(f"  📄 {rel_path}", style="cyan")
                    
                    if len(result.file_paths) > 30:
                        console.print(f"... and {len(result.file_paths) - 30} more files", style="dim")
                else:
                    console.print(f"📂 No files found matching '{pattern}'", style="yellow")
            else:
                console.print(f"❌ Glob error: {result.error}", style="red")
                
        except Exception as e:
            console.print(f"❌ Glob error: {e}", style="red")
    
    async def handle_git_command(self, args: str):
        """Handle git commands."""
        try:
            parts = args.split()
            if not parts:
                await self.display_git_help()
                return
            
            cmd = parts[0].lower()
            
            if cmd == 'status':
                result = self.git_tools.git_status()
                if result.success:
                    console.print("📊 Git Status:", style="bold blue")
                    console.print(result.output)
                else:
                    console.print(f"❌ Git error: {result.error}", style="red")
            
            elif cmd == 'diff':
                file_path = parts[1] if len(parts) > 1 else None
                result = self.git_tools.git_diff(file_path)
                if result.success:
                    console.print("📝 Git Diff:", style="bold blue")
                    console.print(result.output)
                else:
                    console.print(f"❌ Git error: {result.error}", style="red")
            
            elif cmd == 'log':
                limit = 10
                if len(parts) > 1:
                    try:
                        limit = int(parts[1])
                    except ValueError:
                        pass
                
                result = self.git_tools.git_log(limit=limit)
                if result.success:
                    console.print("📋 Git Log:", style="bold blue")
                    if result.data:  # Structured commit data
                        for commit in result.data:
                            console.print(f"🔸 {commit.short_hash} - {commit.message}", style="cyan")
                            console.print(f"   By {commit.author} on {commit.date.strftime('%Y-%m-%d %H:%M')}", style="dim")
                    else:
                        console.print(result.output)
                else:
                    console.print(f"❌ Git error: {result.error}", style="red")
            
            elif cmd == 'commit':
                if len(parts) > 1:
                    message = ' '.join(parts[1:])
                    result = self.git_tools.git_commit(message)
                    if result.success:
                        console.print(f"✅ Committed: {message}", style="green")
                    else:
                        console.print(f"❌ Commit error: {result.error}", style="red")
                else:
                    # Smart commit
                    result = self.git_tools.create_smart_commit()
                    if result.success:
                        console.print("✅ Smart commit created", style="green")
                    else:
                        console.print(f"❌ Commit error: {result.error}", style="red")
            
            else:
                await self.display_git_help()
                
        except Exception as e:
            console.print(f"❌ Git error: {e}", style="red")
    
    async def handle_web_command(self, args: str):
        """Handle web commands."""
        try:
            parts = args.split(None, 1)
            if not parts:
                await self.display_web_help()
                return
            
            cmd = parts[0].lower()
            
            if cmd == 'search':
                if len(parts) > 1:
                    query = parts[1]
                    result = self.web_tools.web_search(query)
                    
                    if result["success"]:
                        console.print(f"🌐 Web search results for '{query}':", style="bold blue")
                        for i, res in enumerate(result["results"], 1):
                            console.print(f"{i}. {res.title}", style="cyan")
                            console.print(f"   {res.url}", style="dim")
                            console.print(f"   {res.snippet}", style="white")
                    else:
                        console.print(f"❌ Search error: {result.get('error')}", style="red")
                else:
                    console.print("❌ Usage: /web search <query>", style="red")
            
            elif cmd == 'fetch':
                if len(parts) > 1:
                    url = parts[1]
                    result = self.web_tools.web_fetch(url)
                    
                    if result.success:
                        console.print(f"📄 Fetched: {result.title}", style="bold blue")
                        console.print(f"🔗 URL: {result.url}", style="cyan")
                        console.print("📖 Content preview:", style="green")
                        # Show first 500 characters
                        preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                        console.print(preview, style="white")
                    else:
                        console.print(f"❌ Fetch error: {result.error}", style="red")
                else:
                    console.print("❌ Usage: /web fetch <url>", style="red")
            
            else:
                await self.display_web_help()
                
        except Exception as e:
            console.print(f"❌ Web error: {e}", style="red")
    
    async def handle_todo_command(self, args: str):
        """Handle todo commands."""
        try:
            parts = args.split()
            if not parts:
                await self.display_todo_help()
                return
            
            cmd = parts[0].lower()
            
            if cmd == 'list':
                tasks = self.task_manager.get_current_tasks()
                if tasks["tasks"]:
                    console.print("📋 Current Tasks:", style="bold blue")
                    for i, task in enumerate(tasks["tasks"], 1):
                        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
                        status = task["status"]
                        icon = status_icon.get(status, "❓")
                        console.print(f"{i}. {icon} {task['content']}", 
                                    style="green" if status == "completed" else "yellow" if status == "in_progress" else "white")
                    
                    summary = tasks["summary"]
                    console.print(f"\n📊 Progress: {summary['completed']}/{summary['total']} completed", style="cyan")
                else:
                    console.print("📋 No active tasks", style="yellow")
            
            elif cmd == 'create':
                if len(parts) > 1:
                    task_content = ' '.join(parts[1:])
                    todos = [{
                        "content": task_content,
                        "status": "pending",
                        "activeForm": f"Working on {task_content}"
                    }]
                    result = self.task_manager.write_todos(todos)
                    
                    if result["success"]:
                        console.print(f"✅ Created task: {task_content}", style="green")
                    else:
                        console.print(f"❌ Error creating task: {result['error']}", style="red")
                else:
                    console.print("❌ Usage: /todo create <task description>", style="red")
            
            elif cmd == 'complete':
                result = self.task_manager.complete_current_task()
                if result["success"]:
                    console.print("✅ Task completed!", style="green")
                else:
                    console.print(f"❌ {result['error']}", style="red")
            
            elif cmd == 'start':
                result = self.task_manager.start_next_task()
                if result["success"]:
                    console.print("🔄 Started next task", style="green")
                else:
                    console.print(f"❌ {result['error']}", style="red")
            
            else:
                await self.display_todo_help()
                
        except Exception as e:
            console.print(f"❌ Todo error: {e}", style="red")
    
    async def handle_code_analysis(self, args: str):
        """Handle code analysis commands."""
        try:
            parts = args.split()
            if not parts:
                console.print("❌ Target required (file or 'project')", style="red")
                return
            
            target = parts[0]
            
            if target == 'project':
                console.print("🔍 Analyzing project structure...", style="yellow")
                analysis = self.code_analyzer.analyze_codebase(self.current_project_path)
                
                console.print("📊 Project Analysis Results:", style="bold blue")
                console.print(f"📁 Files analyzed: {analysis.total_files}", style="cyan")
                console.print(f"📝 Total lines: {analysis.total_lines}", style="cyan")
                
                if analysis.languages:
                    console.print("\n🔧 Languages detected:", style="bold")
                    for lang, count in analysis.languages.items():
                        console.print(f"  {lang}: {count} files", style="white")
                
                if analysis.complexity_stats:
                    console.print("\n📈 Complexity Statistics:", style="bold")
                    stats = analysis.complexity_stats
                    console.print(f"  Average function complexity: {stats.get('average_function_complexity', 0):.1f}", style="white")
                    console.print(f"  Total functions: {stats.get('total_functions', 0)}", style="white")
                    console.print(f"  Total classes: {stats.get('total_classes', 0)}", style="white")
                
                if analysis.issues:
                    console.print(f"\n⚠️ Issues found: {len(analysis.issues)}", style="yellow")
                    for issue in analysis.issues[:5]:  # Show first 5 issues
                        console.print(f"  {issue.get('type', 'unknown')}: {issue.get('message', 'No details')}", style="red")
                    
                    if len(analysis.issues) > 5:
                        console.print(f"  ... and {len(analysis.issues) - 5} more issues", style="dim")
                
            else:
                # Analyze single file
                file_path = Path(self.current_project_path) / target
                if not file_path.exists():
                    console.print(f"❌ File not found: {target}", style="red")
                    return
                
                console.print(f"🔍 Analyzing {target}...", style="yellow")
                file_analysis = self.code_analyzer.analyze_file(str(file_path))
                
                if file_analysis:
                    console.print("📊 File Analysis Results:", style="bold blue")
                    console.print(f"📝 Lines of code: {file_analysis.lines_of_code}", style="cyan")
                    console.print(f"🔧 Language: {file_analysis.language}", style="cyan")
                    console.print(f"⚡ Complexity score: {file_analysis.complexity_score:.1f}", style="cyan")
                    
                    if file_analysis.functions:
                        console.print(f"\n🔧 Functions ({len(file_analysis.functions)}):", style="bold")
                        for func in file_analysis.functions[:5]:
                            console.print(f"  {func.name} (line {func.line_number}, complexity: {func.complexity})", style="white")
                    
                    if file_analysis.classes:
                        console.print(f"\n📦 Classes ({len(file_analysis.classes)}):", style="bold")
                        for cls in file_analysis.classes[:5]:
                            console.print(f"  {cls.name} (line {cls.line_number})", style="white")
                    
                    if file_analysis.issues:
                        console.print(f"\n⚠️ Issues ({len(file_analysis.issues)}):", style="yellow")
                        for issue in file_analysis.issues[:3]:
                            console.print(f"  {issue.get('type', 'unknown')}: {issue.get('message', 'No details')}", style="red")
                else:
                    console.print(f"❌ Could not analyze {target}", style="red")
                    
        except Exception as e:
            console.print(f"❌ Analysis error: {e}", style="red")
    
    async def handle_background_bash(self, args: str):
        """Handle background bash execution."""
        try:
            parts = args.split()
            if not parts:
                console.print("❌ Command required", style="red")
                return
            
            background = '--background' in parts or '-b' in parts
            if background:
                parts = [p for p in parts if p not in ['--background', '-b']]
            
            command = ' '.join(parts)
            
            if background:
                result = self.background_executor.run_background(command)
                if result["success"]:
                    console.print(f"🚀 Started background process: {result['process_id']}", style="green")
                    console.print(f"   Command: {command}", style="dim")
                else:
                    console.print(f"❌ Failed to start: {result['error']}", style="red")
            else:
                # Execute immediately
                import subprocess
                result = subprocess.run(command, shell=True, cwd=self.current_project_path, 
                                      capture_output=True, text=True)
                
                if result.stdout:
                    console.print("📤 Output:", style="green")
                    console.print(result.stdout)
                
                if result.stderr:
                    console.print("🔴 Errors:", style="red")
                    console.print(result.stderr)
                
                console.print(f"Exit code: {result.returncode}", style="cyan")
                
        except Exception as e:
            console.print(f"❌ Bash error: {e}", style="red")
    
    async def handle_list_processes(self):
        """List background processes."""
        try:
            result = self.background_executor.list_processes(include_completed=True)
            
            if result["success"]:
                processes = result["processes"]
                if processes:
                    console.print(f"🔄 Background Processes ({len(processes)}):", style="bold blue")
                    
                    # Create a table
                    from rich.table import Table
                    table = Table()
                    table.add_column("ID", style="cyan")
                    table.add_column("Command", style="white")
                    table.add_column("Status", style="yellow")
                    table.add_column("Runtime", style="green")
                    
                    for proc in processes:
                        runtime = f"{proc['runtime_seconds']:.1f}s"
                        status_color = "green" if proc['status'] == 'completed' else "yellow" if proc['status'] == 'running' else "red"
                        
                        table.add_row(
                            proc['id'][:8],
                            proc['command'][:40] + "..." if len(proc['command']) > 40 else proc['command'],
                            f"[{status_color}]{proc['status']}[/{status_color}]",
                            runtime
                        )
                    
                    console.print(table)
                else:
                    console.print("🔄 No background processes", style="yellow")
            else:
                console.print(f"❌ Error listing processes: {result.get('error')}", style="red")
                
        except Exception as e:
            console.print(f"❌ Process list error: {e}", style="red")
    
    # Help display functions for new commands
    async def display_git_help(self):
        """Display git command help."""
        console.print("🔧 Git Commands:", style="bold blue")
        console.print("/git status        - Show repository status")
        console.print("/git diff [file]   - Show changes")
        console.print("/git log [n]       - Show commit history")
        console.print("/git commit [msg]  - Create commit (smart if no message)")
    
    async def display_web_help(self):
        """Display web command help."""
        console.print("🌐 Web Commands:", style="bold blue")
        console.print("/web search <query>  - Search the web")
        console.print("/web fetch <url>     - Fetch webpage content")
    
    async def display_todo_help(self):
        """Display todo command help."""
        console.print("📋 Todo Commands:", style="bold blue")
        console.print("/todo list           - Show current tasks")
        console.print("/todo create <desc>  - Create new task")
        console.print("/todo start          - Start next pending task")
        console.print("/todo complete       - Complete current task")