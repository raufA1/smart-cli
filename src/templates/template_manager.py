"""Template Manager - Handles code template generation and management."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Template:
    """Template data structure."""
    name: str
    description: str
    category: str
    files: Dict[str, str]  # filename -> content
    variables: Dict[str, str]  # variable_name -> default_value
    dependencies: List[str]  # required packages


class TemplateManager:
    """Manages code templates for Smart CLI."""
    
    def __init__(self):
        self.templates = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in templates."""
        from .code_templates import (
            PythonTemplate,
            WebScraperTemplate,
            APITemplate,
            CLITemplate,
            DatabaseTemplate,
            TestTemplate
        )
        
        template_classes = [
            PythonTemplate,
            WebScraperTemplate,
            APITemplate,
            CLITemplate,
            DatabaseTemplate,
            TestTemplate
        ]
        
        for template_class in template_classes:
            template = template_class()
            self.templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[Template]:
        """Get template by name."""
        return self.templates.get(name)
    
    def list_templates(self, category: Optional[str] = None) -> List[Template]:
        """List all templates or templates by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def get_categories(self) -> List[str]:
        """Get all template categories."""
        categories = set(t.category for t in self.templates.values())
        return sorted(list(categories))
    
    def generate_from_template(
        self, 
        template_name: str, 
        variables: Dict[str, Any], 
        output_dir: str = "."
    ) -> List[str]:
        """Generate files from template with variables."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        created_files = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Merge template variables with user variables
        all_variables = {**template.variables, **variables}
        
        # Generate each file
        for filename, content in template.files.items():
            # Replace variables in filename
            actual_filename = self._replace_variables(filename, all_variables)
            
            # Replace variables in content
            actual_content = self._replace_variables(content, all_variables)
            
            # Write file
            file_path = output_path / actual_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(actual_content)
            
            created_files.append(str(file_path))
        
        return created_files
    
    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Replace template variables in text."""
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            text = text.replace(placeholder, str(var_value))
        return text
    
    def create_requirements_file(self, template_name: str, output_dir: str = ".") -> Optional[str]:
        """Create requirements.txt file for template."""
        template = self.get_template(template_name)
        if not template or not template.dependencies:
            return None
        
        requirements_path = Path(output_dir) / "requirements.txt"
        with open(requirements_path, 'w') as f:
            for dep in template.dependencies:
                f.write(f"{dep}\n")
        
        return str(requirements_path)
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed template information."""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "files": list(template.files.keys()),
            "variables": template.variables,
            "dependencies": template.dependencies
        }