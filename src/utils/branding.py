"""Smart CLI Branding utilities for consistent visual presentation."""

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Smart CLI ASCII Logo
SMART_CLI_LOGO_ASCII = """
███████╗███╗   ███╗ █████╗ ██████╗ ████████╗     ██████╗██╗     ██╗
██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║     ██║
███████╗██╔████╔██║███████║██████╔╝   ██║       ██║     ██║     ██║  
╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║       ██║     ██║     ██║
███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║       ╚██████╗███████╗██║
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝        ╚═════╝╚══════╝╚═╝
"""

# Compact version for smaller displays
SMART_CLI_LOGO_COMPACT = """
 ███╗   ███╗ █████╗ ██████╗ ████████╗     ██████╗██╗     ██╗
 ████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██║     ██║
 ██╔████╔██║███████║██████╔╝   ██║       ██║     ██║     ██║  
 ██║╚██╔╝██║██╔══██║██╔══██╗   ██║       ██║     ██║     ██║
 ██║ ╚═╝ ██║██║  ██║██║  ██║   ██║       ╚██████╗███████╗██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝        ╚═════╝╚══════╝╚═╝
"""

# Simple icon representations
SMART_CLI_ICON_UNICODE = "🤖"
SMART_CLI_ICON_ASCII = "[S]"
SMART_CLI_ICON_TERMINAL = "█▀█"

def get_logo_path(size="256"):
    """Get path to Smart CLI logo icon."""
    current_dir = Path(__file__).parent.parent.parent
    logo_path = current_dir / "smart-cli-logo" / "icons" / f"icon-{size}.png"
    return str(logo_path) if logo_path.exists() else None

def display_welcome_banner(console: Console = None, compact=False):
    """Display Smart CLI welcome banner with actual logo."""
    if console is None:
        console = Console()
    
    # Try to display actual PNG logo in terminal (if supported)
    logo_displayed = display_terminal_logo(console)
    
    if not logo_displayed:
        # Fallback to ASCII logo
        logo = SMART_CLI_LOGO_COMPACT if compact or console.size.width < 80 else SMART_CLI_LOGO_ASCII
        banner_text = Text()
        banner_text.append(logo, style="bold cyan")
        banner_text.append("\\n")
    else:
        banner_text = Text("\\n")
    
    banner_text.append("🚀 Enterprise AI-Powered CLI Platform", style="bold yellow")
    banner_text.append("\\n")
    banner_text.append("Version 1.0.0", style="dim white")
    
    panel = Panel(
        banner_text,
        title="[bold blue]Smart CLI[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)

def display_terminal_logo(console: Console, size="32") -> bool:
    """Try to display PNG logo in terminal if supported."""
    try:
        # Import terminal image libraries if available
        from PIL import Image
        import sys
        
        logo_path = get_logo_path(size)
        if not logo_path or not os.path.exists(logo_path):
            return False
        
        # Check if terminal supports images (iTerm2, Kitty, etc.)
        term = os.environ.get('TERM_PROGRAM', '').lower()
        if term in ['iterm.app', 'kitty']:
            try:
                # For iTerm2 - display image using iTerm2 image protocol
                if term == 'iterm.app':
                    display_iterm2_image(logo_path, console)
                    return True
                # For Kitty - display image using Kitty image protocol  
                elif term == 'kitty':
                    display_kitty_image(logo_path, console)
                    return True
            except Exception:
                pass
        
        return False
        
    except ImportError:
        return False

def display_iterm2_image(image_path: str, console: Console):
    """Display image in iTerm2 terminal."""
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # iTerm2 image display protocol
    console.print(f"\\033]1337;File=inline=1:{image_data}\\007")

def display_kitty_image(image_path: str, console: Console):  
    """Display image in Kitty terminal."""
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Kitty image display protocol
    console.print(f"\\033_Gf=100,a=T,m=1;{image_data}\\033\\\\")

def show_icon_in_help(size="20") -> str:
    """Get icon reference for CLI help text."""
    logo_path = get_logo_path(size)
    if logo_path and os.path.exists(logo_path):
        return f"📁 Logo: {logo_path}"
    return "🤖 Smart CLI"

def get_branded_prompt(mode="smart"):
    """Get branded CLI prompt."""
    icons = {
        "smart": "🤖",
        "code": "💻", 
        "analysis": "🔍",
        "architect": "🏗️",
        "learning": "📚",
        "fast": "⚡",
        "orchestrator": "🎭"
    }
    
    icon = icons.get(mode, "🤖")
    return f"{icon} Smart CLI ({mode})"

def format_section_header(title: str, icon: str = "🔧") -> str:
    """Format a section header with branding."""
    return f"{icon} [bold cyan]{title}[/bold cyan]"

def format_success_message(message: str) -> str:
    """Format success message with branding."""
    return f"✅ [bold green]{message}[/bold green]"

def format_error_message(message: str) -> str:
    """Format error message with branding."""
    return f"❌ [bold red]{message}[/bold red]"

def format_info_message(message: str) -> str:
    """Format info message with branding.""" 
    return f"ℹ️  [blue]{message}[/blue]"

def format_warning_message(message: str) -> str:
    """Format warning message with branding."""
    return f"⚠️  [yellow]{message}[/yellow]"

# Brand colors for consistent theming
BRAND_COLORS = {
    "primary": "blue",
    "secondary": "cyan", 
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "blue",
    "accent": "magenta"
}

def get_brand_style(element_type: str) -> str:
    """Get consistent brand styling for UI elements."""
    styles = {
        "header": "bold cyan",
        "title": "bold blue", 
        "success": "bold green",
        "error": "bold red",
        "warning": "yellow",
        "info": "blue",
        "dim": "dim white",
        "code": "bold white on black"
    }
    return styles.get(element_type, "white")