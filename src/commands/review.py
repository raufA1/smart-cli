"""Code review and analysis commands."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from typing import Optional
from pathlib import Path
import ast
import re

console = Console()
review_app = typer.Typer()


@review_app.command()
def code(
    file_path: str = typer.Argument(..., help="Path to code file"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Programming language"),
    focus: str = typer.Option("general", "--focus", "-f", help="Review focus (security, performance, style, general)"),
):
    """Review and analyze code file."""
    
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"❌ File not found: {file_path}", style="red")
        raise typer.Exit(1)
    
    if not language:
        language = _detect_language(path)
    
    console.print(f"🔍 Reviewing {language} file: {path.name}", style="blue")
    console.print(f"📋 Focus: {focus}", style="dim")
    
    # Read file content
    try:
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        console.print("❌ Unable to read file (binary file?)", style="red")
        raise typer.Exit(1)
    
    # Perform analysis based on language and focus
    if language == "python":
        analysis = _analyze_python_code(content, focus)
    elif language in ["javascript", "typescript"]:
        analysis = _analyze_js_code(content, focus)
    else:
        analysis = _analyze_generic_code(content, focus)
    
    # Display results
    _display_analysis_results(content, language, analysis)


@review_app.command()
def project(
    directory: str = typer.Argument(".", help="Project directory"),
    focus: str = typer.Option("general", "--focus", "-f", help="Review focus"),
    include_tests: bool = typer.Option(False, "--tests", help="Include test files"),
):
    """Review entire project structure."""
    
    project_path = Path(directory)
    
    if not project_path.exists():
        console.print(f"❌ Directory not found: {directory}", style="red")
        raise typer.Exit(1)
    
    console.print(f"🔍 Reviewing project: {project_path.name}", style="blue")
    
    # Analyze project structure
    analysis = _analyze_project_structure(project_path, include_tests)
    
    # Display project overview
    _display_project_analysis(analysis)
    
    # Analyze individual files
    code_files = _find_code_files(project_path, include_tests)
    
    if not code_files:
        console.print("⚠️  No code files found in project", style="yellow")
        return
    
    console.print(f"\n📁 Found {len(code_files)} code files", style="blue")
    
    # Quick analysis of each file
    for file_path in code_files[:10]:  # Limit to first 10 files
        try:
            content = file_path.read_text(encoding='utf-8')
            language = _detect_language(file_path)
            
            if language == "python":
                file_analysis = _analyze_python_code(content, focus)
            else:
                file_analysis = _analyze_generic_code(content, focus)
            
            _display_file_summary(file_path, file_analysis)
            
        except Exception as e:
            console.print(f"⚠️  Could not analyze {file_path}: {e}", style="yellow")
    
    if len(code_files) > 10:
        console.print(f"\n... and {len(code_files) - 10} more files", style="dim")


def _analyze_python_code(content: str, focus: str) -> dict:
    """Analyze Python code."""
    analysis = {
        "issues": [],
        "suggestions": [],
        "metrics": {},
        "security": [],
        "performance": []
    }
    
    try:
        # Parse AST for deeper analysis
        tree = ast.parse(content)
        
        # Count various constructs
        analysis["metrics"] = {
            "lines": len(content.splitlines()),
            "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
            "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
            "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
        }
        
        # Check for common issues
        if focus in ["security", "general"]:
            analysis["security"] = _check_python_security(content, tree)
        
        if focus in ["performance", "general"]:
            analysis["performance"] = _check_python_performance(content, tree)
        
        if focus in ["style", "general"]:
            analysis["issues"].extend(_check_python_style(content))
        
    except SyntaxError as e:
        analysis["issues"].append(f"Syntax Error: {e}")
    
    return analysis


def _analyze_js_code(content: str, focus: str) -> dict:
    """Analyze JavaScript/TypeScript code."""
    analysis = {
        "issues": [],
        "suggestions": [],
        "metrics": {
            "lines": len(content.splitlines()),
            "functions": len(re.findall(r'\bfunction\s+\w+|=>\s*{|\w+\s*:\s*function', content)),
            "classes": len(re.findall(r'\bclass\s+\w+', content)),
        },
        "security": [],
        "performance": []
    }
    
    if focus in ["security", "general"]:
        analysis["security"] = _check_js_security(content)
    
    if focus in ["performance", "general"]:
        analysis["performance"] = _check_js_performance(content)
    
    return analysis


def _analyze_generic_code(content: str, focus: str) -> dict:
    """Generic code analysis."""
    lines = content.splitlines()
    
    return {
        "issues": [],
        "suggestions": [],
        "metrics": {
            "lines": len(lines),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "comment_lines": len([l for l in lines if l.strip().startswith(('#', '//', '/*'))]),
        },
        "security": [],
        "performance": []
    }


def _check_python_security(content: str, tree: ast.AST) -> list:
    """Check for Python security issues."""
    issues = []
    
    # Check for eval/exec usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec']:
                issues.append(f"Security: Use of {node.func.id}() at line {node.lineno}")
    
    # Check for hardcoded credentials
    if re.search(r'password\s*=\s*["\'][^"\']*["\']', content, re.IGNORECASE):
        issues.append("Security: Possible hardcoded password found")
    
    if re.search(r'api[_-]?key\s*=\s*["\'][^"\']*["\']', content, re.IGNORECASE):
        issues.append("Security: Possible hardcoded API key found")
    
    return issues


def _check_python_performance(content: str, tree: ast.AST) -> list:
    """Check for Python performance issues."""
    issues = []
    
    # Check for list concatenation in loops
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for child in ast.walk(node):
                if (isinstance(child, ast.AugAssign) and 
                    isinstance(child.op, ast.Add)):
                    issues.append(f"Performance: List concatenation in loop at line {child.lineno}")
    
    return issues


def _check_python_style(content: str) -> list:
    """Check Python style issues."""
    issues = []
    lines = content.splitlines()
    
    for i, line in enumerate(lines, 1):
        # Check line length
        if len(line) > 88:
            issues.append(f"Style: Line {i} exceeds 88 characters")
        
        # Check for unused imports (basic check)
        if line.strip().startswith('import ') and 'import' in line:
            module = line.split('import ')[1].split()[0].split('.')[0]
            if module not in content:
                issues.append(f"Style: Possibly unused import at line {i}")
    
    return issues


def _check_js_security(content: str) -> list:
    """Check JavaScript security issues."""
    issues = []
    
    # Check for eval usage
    if 'eval(' in content:
        issues.append("Security: Use of eval() found")
    
    # Check for innerHTML usage
    if 'innerHTML' in content:
        issues.append("Security: Use of innerHTML (potential XSS)")
    
    return issues


def _check_js_performance(content: str) -> list:
    """Check JavaScript performance issues."""
    issues = []
    
    # Check for document.getElementById in loops
    if re.search(r'for.*document\.getElementById', content, re.DOTALL):
        issues.append("Performance: DOM query in loop detected")
    
    return issues


def _analyze_project_structure(project_path: Path, include_tests: bool) -> dict:
    """Analyze project structure."""
    analysis = {
        "total_files": 0,
        "code_files": 0,
        "test_files": 0,
        "config_files": 0,
        "languages": set(),
        "directories": [],
        "has_readme": False,
        "has_gitignore": False,
        "has_requirements": False,
    }
    
    for item in project_path.rglob("*"):
        if item.is_file():
            analysis["total_files"] += 1
            
            # Check for specific files
            if item.name.lower() in ["readme.md", "readme.rst", "readme.txt"]:
                analysis["has_readme"] = True
            elif item.name == ".gitignore":
                analysis["has_gitignore"] = True
            elif item.name in ["requirements.txt", "pyproject.toml", "package.json"]:
                analysis["has_requirements"] = True
            
            # Classify files
            if _is_code_file(item):
                analysis["code_files"] += 1
                language = _detect_language(item)
                analysis["languages"].add(language)
                
                if _is_test_file(item):
                    analysis["test_files"] += 1
            
            elif _is_config_file(item):
                analysis["config_files"] += 1
        
        elif item.is_dir() and not item.name.startswith('.'):
            analysis["directories"].append(item.name)
    
    return analysis


def _find_code_files(project_path: Path, include_tests: bool) -> list:
    """Find all code files in project."""
    code_files = []
    
    for item in project_path.rglob("*"):
        if item.is_file() and _is_code_file(item):
            if include_tests or not _is_test_file(item):
                code_files.append(item)
    
    return sorted(code_files)


def _is_code_file(path: Path) -> bool:
    """Check if file is a code file."""
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
                      '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
    return path.suffix.lower() in code_extensions


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    test_patterns = ['test_', '_test', 'test.', '.spec.', '.test.']
    return any(pattern in path.name.lower() for pattern in test_patterns)


def _is_config_file(path: Path) -> bool:
    """Check if file is a configuration file."""
    config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}
    config_names = {'dockerfile', 'makefile', '.gitignore', '.env'}
    
    return (path.suffix.lower() in config_extensions or 
            path.name.lower() in config_names)


def _detect_language(path: Path) -> str:
    """Detect programming language from file extension."""
    extension_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
    }
    
    return extension_map.get(path.suffix.lower(), 'unknown')


def _display_analysis_results(content: str, language: str, analysis: dict):
    """Display code analysis results."""
    
    # Show code metrics
    metrics_table = Table(title="Code Metrics")
    metrics_table.add_column("Metric", style="blue")
    metrics_table.add_column("Value", style="green")
    
    for metric, value in analysis["metrics"].items():
        metrics_table.add_row(metric.replace('_', ' ').title(), str(value))
    
    console.print(metrics_table)
    
    # Show issues
    if analysis["issues"]:
        console.print("\n🚨 Issues Found:", style="bold red")
        for issue in analysis["issues"]:
            console.print(f"  • {issue}", style="red")
    
    # Show security findings
    if analysis["security"]:
        console.print("\n🔒 Security Findings:", style="bold yellow")
        for finding in analysis["security"]:
            console.print(f"  • {finding}", style="yellow")
    
    # Show performance findings
    if analysis["performance"]:
        console.print("\n⚡ Performance Findings:", style="bold cyan")
        for finding in analysis["performance"]:
            console.print(f"  • {finding}", style="cyan")
    
    # Show suggestions
    if analysis["suggestions"]:
        console.print("\n💡 Suggestions:", style="bold green")
        for suggestion in analysis["suggestions"]:
            console.print(f"  • {suggestion}", style="green")
    
    if not any([analysis["issues"], analysis["security"], analysis["performance"]]):
        console.print("\n✅ No major issues found!", style="bold green")


def _display_project_analysis(analysis: dict):
    """Display project structure analysis."""
    
    # Project overview
    overview_table = Table(title="Project Overview")
    overview_table.add_column("Aspect", style="blue")
    overview_table.add_column("Value", style="green")
    
    overview_table.add_row("Total Files", str(analysis["total_files"]))
    overview_table.add_row("Code Files", str(analysis["code_files"]))
    overview_table.add_row("Test Files", str(analysis["test_files"]))
    overview_table.add_row("Config Files", str(analysis["config_files"]))
    overview_table.add_row("Languages", ", ".join(analysis["languages"]) if analysis["languages"] else "None")
    
    console.print(overview_table)
    
    # Project health indicators
    health_table = Table(title="Project Health")
    health_table.add_column("Indicator", style="blue")
    health_table.add_column("Status", style="green")
    
    health_table.add_row("README", "✅" if analysis["has_readme"] else "❌")
    health_table.add_row(".gitignore", "✅" if analysis["has_gitignore"] else "❌")
    health_table.add_row("Dependencies", "✅" if analysis["has_requirements"] else "❌")
    health_table.add_row("Tests", "✅" if analysis["test_files"] > 0 else "❌")
    
    console.print(health_table)


def _display_file_summary(file_path: Path, analysis: dict):
    """Display summary for individual file."""
    issues_count = len(analysis["issues"]) + len(analysis["security"]) + len(analysis["performance"])
    
    status = "✅" if issues_count == 0 else f"⚠️  {issues_count} issues"
    
    console.print(f"  📄 {file_path.name}: {status} ({analysis['metrics'].get('lines', 0)} lines)")


if __name__ == "__main__":
    review_app()