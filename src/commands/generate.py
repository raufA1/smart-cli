"""Code generation commands."""

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel
from typing import Optional
from pathlib import Path

console = Console()
generate_app = typer.Typer()


@generate_app.command()
def function(
    name: str = typer.Argument(..., help="Function name"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Function description"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate a function using AI."""
    
    if not description:
        description = Prompt.ask("Enter function description")
    
    console.print(f"🤖 Generating {language} function: {name}", style="blue")
    console.print(f"📝 Description: {description}", style="dim")
    
    # For now, generate a basic template
    # Later this will be replaced with actual AI generation
    generated_code = _generate_function_template(name, language, description)
    
    # Display generated code
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {language} function"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to file?"):
        if not output:
            output = Prompt.ask("Enter output file path", default=f"{name}.{_get_file_extension(language)}")
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_code)
        
        console.print(f"✅ Function saved to {output_path}", style="green")


@generate_app.command()
def class_definition(
    name: str = typer.Argument(..., help="Class name"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Class description"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate a class definition using AI."""
    
    if not description:
        description = Prompt.ask("Enter class description")
    
    console.print(f"🤖 Generating {language} class: {name}", style="blue")
    console.print(f"📝 Description: {description}", style="dim")
    
    # Generate class template
    generated_code = _generate_class_template(name, language, description)
    
    # Display generated code
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {language} class"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to file?"):
        if not output:
            output = Prompt.ask("Enter output file path", default=f"{name.lower()}.{_get_file_extension(language)}")
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_code)
        
        console.print(f"✅ Class saved to {output_path}", style="green")


@generate_app.command()
def api(
    name: str = typer.Argument(..., help="API name"),
    framework: str = typer.Option("fastapi", "--framework", "-f", help="API framework (fastapi, flask, express)"),
    endpoints: Optional[str] = typer.Option(None, "--endpoints", "-e", help="Comma-separated endpoint names"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Generate API boilerplate code."""
    
    if not endpoints:
        endpoints = Prompt.ask("Enter endpoint names (comma-separated)", default="users,health")
    
    endpoint_list = [ep.strip() for ep in endpoints.split(",")]
    
    console.print(f"🤖 Generating {framework} API: {name}", style="blue")
    console.print(f"📝 Endpoints: {', '.join(endpoint_list)}", style="dim")
    
    # Generate API code
    generated_code = _generate_api_template(name, framework, endpoint_list)
    
    # Display generated code
    language = _get_language_for_framework(framework)
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {framework} API"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to directory?"):
        if not output:
            output = Prompt.ask("Enter output directory", default=f"{name}_api")
        
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        main_file = output_dir / f"main.{_get_file_extension(language)}"
        main_file.write_text(generated_code)
        
        # Generate requirements/package files
        _generate_api_dependencies(output_dir, framework)
        
        console.print(f"✅ API saved to {output_dir}/", style="green")


def _generate_function_template(name: str, language: str, description: str) -> str:
    """Generate function template based on language."""
    
    if language == "python":
        return f'''def {name}():
    """
    {description}
    
    Returns:
        str: Description of return value
    """
    # TODO: Implement function logic
    pass


# Example usage
if __name__ == "__main__":
    result = {name}()
    print(result)
'''
    
    elif language == "javascript":
        return f'''/**
 * {description}
 * @returns {{string}} Description of return value
 */
function {name}() {{
    // TODO: Implement function logic
    return "";
}}

// Example usage
console.log({name}());
'''
    
    elif language == "typescript":
        return f'''/**
 * {description}
 * @returns Description of return value
 */
function {name}(): string {{
    // TODO: Implement function logic
    return "";
}}

// Example usage
console.log({name}());
'''
    
    else:
        return f'// {language} function: {name}\n// {description}\n// TODO: Implement'


def _generate_class_template(name: str, language: str, description: str) -> str:
    """Generate class template based on language."""
    
    if language == "python":
        return f'''class {name}:
    """
    {description}
    """
    
    def __init__(self):
        """Initialize {name} instance."""
        pass
    
    def __str__(self) -> str:
        """String representation of {name}."""
        return f"{name}()"
    
    def __repr__(self) -> str:
        """Developer representation of {name}."""
        return self.__str__()


# Example usage
if __name__ == "__main__":
    instance = {name}()
    print(instance)
'''
    
    elif language == "javascript":
        return f'''/**
 * {description}
 */
class {name} {{
    constructor() {{
        // TODO: Initialize properties
    }}
    
    toString() {{
        return `{name}()`;
    }}
}}

// Example usage
const instance = new {name}();
console.log(instance.toString());
'''
    
    elif language == "typescript":
        return f'''/**
 * {description}
 */
class {name} {{
    constructor() {{
        // TODO: Initialize properties
    }}
    
    toString(): string {{
        return `{name}()`;
    }}
}}

// Example usage
const instance = new {name}();
console.log(instance.toString());
'''
    
    else:
        return f'// {language} class: {name}\n// {description}\n// TODO: Implement'


def _generate_api_template(name: str, framework: str, endpoints: list) -> str:
    """Generate API template based on framework."""
    
    if framework == "fastapi":
        routes = []
        for endpoint in endpoints:
            routes.append(f'''
@app.get("/{endpoint}")
async def get_{endpoint}():
    """Get {endpoint}."""
    return {{"message": "Hello from {endpoint}!"}}

@app.post("/{endpoint}")  
async def create_{endpoint}():
    """Create {endpoint}."""
    return {{"message": "{endpoint} created successfully"}}
''')
        
        return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{name} API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {name} API"}}

{"".join(routes)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    elif framework == "flask":
        routes = []
        for endpoint in endpoints:
            routes.append(f'''
@app.route('/{endpoint}', methods=['GET'])
def get_{endpoint}():
    """Get {endpoint}."""
    return {{"message": "Hello from {endpoint}!"}}

@app.route('/{endpoint}', methods=['POST'])
def create_{endpoint}():
    """Create {endpoint}."""
    return {{"message": "{endpoint} created successfully"}}
''')
        
        return f'''from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def root():
    """Root endpoint."""
    return {{"message": "Welcome to {name} API"}}

{"".join(routes)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
'''
    
    else:
        return f'// {framework} API: {name}\n// TODO: Implement API endpoints'


def _generate_api_dependencies(output_dir: Path, framework: str):
    """Generate dependency files for API project."""
    
    if framework == "fastapi":
        requirements = '''fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
'''
        (output_dir / "requirements.txt").write_text(requirements)
    
    elif framework == "flask":
        requirements = '''Flask>=3.0.0
Flask-CORS>=4.0.0
'''
        (output_dir / "requirements.txt").write_text(requirements)


def _get_file_extension(language: str) -> str:
    """Get file extension for language."""
    extensions = {
        "python": "py",
        "javascript": "js", 
        "typescript": "ts",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "go": "go",
        "rust": "rs",
    }
    return extensions.get(language, "txt")


def _get_language_for_framework(framework: str) -> str:
    """Get programming language for framework."""
    mappings = {
        "fastapi": "python",
        "flask": "python",
        "express": "javascript",
        "nestjs": "typescript",
    }
    return mappings.get(framework, "python")


if __name__ == "__main__":
    generate_app()