"""Template system for Smart CLI - Code generation templates."""

from .template_manager import TemplateManager
from .code_templates import (
    PythonTemplate,
    WebScraperTemplate, 
    APITemplate,
    CLITemplate,
    DatabaseTemplate,
    TestTemplate
)

__all__ = [
    "TemplateManager",
    "PythonTemplate",
    "WebScraperTemplate",
    "APITemplate", 
    "CLITemplate",
    "DatabaseTemplate",
    "TestTemplate"
]