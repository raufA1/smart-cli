"""AI-powered code generation commands."""

import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
from pathlib import Path
import uuid

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.ai_client import MultiLLMClient, ChatMessage
from utils.agents import (
    MultiAgentWorkflow, AgentTask, AgentRole, 
    CodeGeneratorAgent
)
from utils.config import ConfigManager
from utils.cache import create_cache

console = Console()
generate_app = typer.Typer()


async def _get_ai_workflow():
    """Get AI workflow instance."""
    config = ConfigManager()
    
    # Check if API key is configured
    api_key = (
        config.get_config('openrouter_api_key') or
        config.get_config('anthropic_api_key') or
        config.get_config('openai_api_key')
    )
    
    if not api_key:
        console.print("❌ No AI API key configured. Please set up your API key first:", style="red")
        console.print("   smart-cli config --set openrouter_api_key --value YOUR_KEY", style="yellow")
        raise typer.Exit(1)
    
    # Initialize AI client and workflow
    llm_client = MultiLLMClient(config)
    openrouter_client = await llm_client.get_client("openrouter")
    
    workflow = MultiAgentWorkflow(openrouter_client)
    
    return workflow, openrouter_client


@generate_app.command()
def function(
    name: str = typer.Argument(..., help="Function name"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Function description"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    temperature: Optional[float] = typer.Option(None, "--temp", "-t", help="Temperature (0.0-2.0)"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cached responses"),
):
    """Generate a function using AI."""
    
    if not description:
        description = Prompt.ask("Enter function description")
    
    console.print(f"🤖 Generating {language} function: {name}", style="blue")
    console.print(f"📝 Description: {description}", style="dim")
    
    # Run async function generation
    generated_code = asyncio.run(_generate_function_async(
        name=name,
        language=language,
        description=description,
        model=model,
        temperature=temperature,
        use_cache=use_cache
    ))
    
    if not generated_code:
        console.print("❌ Failed to generate function", style="red")
        raise typer.Exit(1)
    
    # Display generated code
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {language} function: {name}"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to file?"):
        if not output:
            extension = _get_file_extension(language)
            output = Prompt.ask("Enter output file path", default=f"{name}.{extension}")
        
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
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    methods: Optional[str] = typer.Option(None, "--methods", help="Comma-separated method names"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cached responses"),
):
    """Generate a class definition using AI."""
    
    if not description:
        description = Prompt.ask("Enter class description")
    
    if methods:
        method_list = [m.strip() for m in methods.split(",")]
        description += f"\n\nRequired methods: {', '.join(method_list)}"
    
    console.print(f"🤖 Generating {language} class: {name}", style="blue")
    console.print(f"📝 Description: {description}", style="dim")
    
    # Run async class generation
    generated_code = asyncio.run(_generate_class_async(
        name=name,
        language=language,
        description=description,
        model=model,
        use_cache=use_cache
    ))
    
    if not generated_code:
        console.print("❌ Failed to generate class", style="red")
        raise typer.Exit(1)
    
    # Display generated code
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {language} class: {name}"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to file?"):
        if not output:
            extension = _get_file_extension(language)
            output = Prompt.ask("Enter output file path", default=f"{name.lower()}.{extension}")
        
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
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    database: Optional[str] = typer.Option(None, "--db", help="Database type (postgresql, sqlite, mongodb)"),
    auth: bool = typer.Option(False, "--auth", help="Include authentication"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cached responses"),
):
    """Generate API boilerplate code using AI."""
    
    if not endpoints:
        endpoints = Prompt.ask("Enter endpoint names (comma-separated)", default="users,health")
    
    endpoint_list = [ep.strip() for ep in endpoints.split(",")]
    
    console.print(f"🤖 Generating {framework} API: {name}", style="blue")
    console.print(f"📝 Endpoints: {', '.join(endpoint_list)}", style="dim")
    
    # Build description
    description = f"Create a {framework} API named '{name}' with the following endpoints: {', '.join(endpoint_list)}."
    
    if database:
        description += f" Use {database} database."
    
    if auth:
        description += " Include JWT authentication and authorization."
    
    description += " Follow best practices for security, error handling, and documentation."
    
    # Run async API generation
    generated_code = asyncio.run(_generate_api_async(
        name=name,
        framework=framework,
        description=description,
        endpoints=endpoint_list,
        model=model,
        use_cache=use_cache
    ))
    
    if not generated_code:
        console.print("❌ Failed to generate API", style="red")
        raise typer.Exit(1)
    
    # Display generated code
    language = _get_language_for_framework(framework)
    syntax = Syntax(generated_code, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Generated {framework} API: {name}"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to directory?"):
        if not output:
            output = Prompt.ask("Enter output directory", default=f"{name}_api")
        
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main file
        extension = _get_file_extension(language)
        main_file = output_dir / f"main.{extension}"
        main_file.write_text(generated_code)
        
        # Generate additional files
        _generate_api_extras(output_dir, framework, database, auth)
        
        console.print(f"✅ API saved to {output_dir}/", style="green")


@generate_app.command()
def prompt(
    prompt_text: str = typer.Argument(..., help="Custom prompt for AI"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    temperature: Optional[float] = typer.Option(None, "--temp", "-t", help="Temperature (0.0-2.0)"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Programming language for syntax highlighting"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cached responses"),
):
    """Generate content using a custom prompt."""
    
    console.print(f"🤖 Processing custom prompt...", style="blue")
    console.print(f"📝 Prompt: {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}", style="dim")
    
    # Run async prompt generation
    generated_content = asyncio.run(_generate_custom_prompt_async(
        prompt_text=prompt_text,
        model=model,
        temperature=temperature,
        use_cache=use_cache
    ))
    
    if not generated_content:
        console.print("❌ Failed to generate content", style="red")
        raise typer.Exit(1)
    
    # Display generated content
    if language:
        syntax = Syntax(generated_content, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Generated Content"))
    else:
        console.print(Panel(generated_content, title="Generated Content"))
    
    # Ask if user wants to save
    if output or Confirm.ask("Save to file?"):
        if not output:
            extension = _get_file_extension(language) if language else "txt"
            output = Prompt.ask("Enter output file path", default=f"generated.{extension}")
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_content)
        
        console.print(f"✅ Content saved to {output_path}", style="green")


async def _generate_function_async(
    name: str,
    language: str,
    description: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    use_cache: bool = True
) -> Optional[str]:
    """Generate function using AI workflow."""
    
    # Check cache first
    if use_cache:
        cache = create_cache()
        cache_key = f"function:{language}:{name}:{hash(description)}"
        cached_result = await cache.get(cache_key, namespace="code_generation")
        
        if cached_result:
            console.print("💾 Using cached result", style="dim")
            return cached_result
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating function with AI...", total=None)
            
            # Get AI workflow
            workflow, ai_client = await _get_ai_workflow()
            
            # Create agent task
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=AgentRole.CODE_GENERATOR,
                description=description,
                context={
                    'language': language,
                    'function_name': name,
                    'type': 'function',
                    'model': model,
                    'temperature': temperature,
                }
            )
            
            # Execute workflow
            results = await workflow.execute_workflow([agent_task])
            
            # Get result
            result = results.get(agent_task.task_id)
            
            if result and result.success:
                progress.update(task, description="Function generated successfully!")
                
                # Cache result
                if use_cache:
                    cache = create_cache()
                    await cache.set(cache_key, result.content, namespace="code_generation")
                
                # Show usage stats
                usage_stats = ai_client.get_usage_stats()
                console.print(f"📊 Tokens used: {result.tokens_used}, Estimated cost: ${result.cost_estimate:.4f}", style="dim")
                
                return result.content
            
            else:
                error_msg = result.content if result else "Unknown error"
                console.print(f"❌ Generation failed: {error_msg}", style="red")
                return None
                
    except Exception as e:
        console.print(f"❌ Error during generation: {str(e)}", style="red")
        return None


async def _generate_class_async(
    name: str,
    language: str,
    description: str,
    model: Optional[str] = None,
    use_cache: bool = True
) -> Optional[str]:
    """Generate class using AI workflow."""
    
    # Similar to function generation but for classes
    if use_cache:
        cache = create_cache()
        cache_key = f"class:{language}:{name}:{hash(description)}"
        cached_result = await cache.get(cache_key, namespace="code_generation")
        
        if cached_result:
            console.print("💾 Using cached result", style="dim")
            return cached_result
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating class with AI...", total=None)
            
            workflow, ai_client = await _get_ai_workflow()
            
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=AgentRole.CODE_GENERATOR,
                description=description,
                context={
                    'language': language,
                    'class_name': name,
                    'type': 'class',
                    'model': model,
                }
            )
            
            results = await workflow.execute_workflow([agent_task])
            result = results.get(agent_task.task_id)
            
            if result and result.success:
                progress.update(task, description="Class generated successfully!")
                
                if use_cache:
                    cache = create_cache()
                    await cache.set(cache_key, result.content, namespace="code_generation")
                
                console.print(f"📊 Tokens used: {result.tokens_used}, Estimated cost: ${result.cost_estimate:.4f}", style="dim")
                return result.content
            
            else:
                error_msg = result.content if result else "Unknown error"
                console.print(f"❌ Generation failed: {error_msg}", style="red")
                return None
                
    except Exception as e:
        console.print(f"❌ Error during generation: {str(e)}", style="red")
        return None


async def _generate_api_async(
    name: str,
    framework: str,
    description: str,
    endpoints: list,
    model: Optional[str] = None,
    use_cache: bool = True
) -> Optional[str]:
    """Generate API using AI workflow."""
    
    if use_cache:
        cache = create_cache()
        cache_key = f"api:{framework}:{name}:{hash(description)}"
        cached_result = await cache.get(cache_key, namespace="code_generation")
        
        if cached_result:
            console.print("💾 Using cached result", style="dim")
            return cached_result
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating API with AI...", total=None)
            
            workflow, ai_client = await _get_ai_workflow()
            
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=AgentRole.CODE_GENERATOR,
                description=description,
                context={
                    'framework': framework,
                    'api_name': name,
                    'endpoints': endpoints,
                    'type': 'api',
                    'model': model,
                }
            )
            
            results = await workflow.execute_workflow([agent_task])
            result = results.get(agent_task.task_id)
            
            if result and result.success:
                progress.update(task, description="API generated successfully!")
                
                if use_cache:
                    cache = create_cache()
                    await cache.set(cache_key, result.content, namespace="code_generation")
                
                console.print(f"📊 Tokens used: {result.tokens_used}, Estimated cost: ${result.cost_estimate:.4f}", style="dim")
                return result.content
            
            else:
                error_msg = result.content if result else "Unknown error"
                console.print(f"❌ Generation failed: {error_msg}", style="red")
                return None
                
    except Exception as e:
        console.print(f"❌ Error during generation: {str(e)}", style="red")
        return None


async def _generate_custom_prompt_async(
    prompt_text: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    use_cache: bool = True
) -> Optional[str]:
    """Generate content using custom prompt."""
    
    if use_cache:
        cache = create_cache()
        cache_key = f"prompt:{hash(prompt_text)}"
        cached_result = await cache.get(cache_key, namespace="custom_prompts")
        
        if cached_result:
            console.print("💾 Using cached result", style="dim")
            return cached_result
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Processing with AI...", total=None)
            
            workflow, ai_client = await _get_ai_workflow()
            
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=AgentRole.CODE_GENERATOR,  # Use code generator for custom prompts
                description=prompt_text,
                context={
                    'type': 'custom_prompt',
                    'model': model,
                    'temperature': temperature,
                }
            )
            
            results = await workflow.execute_workflow([agent_task])
            result = results.get(agent_task.task_id)
            
            if result and result.success:
                progress.update(task, description="Content generated successfully!")
                
                if use_cache:
                    cache = create_cache()
                    await cache.set(cache_key, result.content, namespace="custom_prompts")
                
                console.print(f"📊 Tokens used: {result.tokens_used}, Estimated cost: ${result.cost_estimate:.4f}", style="dim")
                return result.content
            
            else:
                error_msg = result.content if result else "Unknown error"
                console.print(f"❌ Generation failed: {error_msg}", style="red")
                return None
                
    except Exception as e:
        console.print(f"❌ Error during generation: {str(e)}", style="red")
        return None


def _generate_api_extras(output_dir: Path, framework: str, database: Optional[str], auth: bool):
    """Generate additional files for API project."""
    
    # Generate requirements/dependencies
    if framework in ["fastapi", "flask"]:
        requirements = []
        
        if framework == "fastapi":
            requirements.extend([
                "fastapi>=0.104.0",
                "uvicorn>=0.24.0",
                "python-multipart>=0.0.6",
            ])
        elif framework == "flask":
            requirements.extend([
                "Flask>=3.0.0",
                "Flask-CORS>=4.0.0",
            ])
        
        if database == "postgresql":
            requirements.append("psycopg2-binary>=2.9.0")
            requirements.append("SQLAlchemy>=2.0.0")
        elif database == "sqlite":
            requirements.append("SQLAlchemy>=2.0.0")
        elif database == "mongodb":
            requirements.append("pymongo>=4.0.0")
        
        if auth:
            requirements.extend([
                "python-jose[cryptography]>=3.3.0",
                "passlib[bcrypt]>=1.7.0",
            ])
        
        (output_dir / "requirements.txt").write_text("\n".join(requirements) + "\n")
    
    # Generate README
    readme_content = f"""# {output_dir.name}

Generated API using Smart CLI.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# For FastAPI
uvicorn main:app --reload

# For Flask
python main.py
```

## API Documentation

Visit http://localhost:8000/docs (FastAPI) for interactive API documentation.
"""
    
    (output_dir / "README.md").write_text(readme_content)


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
        "php": "php",
        "ruby": "rb",
        "swift": "swift",
        "kotlin": "kt",
    }
    return extensions.get(language.lower(), "txt")


def _get_language_for_framework(framework: str) -> str:
    """Get programming language for framework."""
    mappings = {
        "fastapi": "python",
        "flask": "python",
        "django": "python",
        "express": "javascript",
        "nestjs": "typescript",
        "spring": "java",
        "gin": "go",
        "actix": "rust",
    }
    return mappings.get(framework.lower(), "python")


if __name__ == "__main__":
    generate_app()