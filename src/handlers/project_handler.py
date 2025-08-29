"""Project Generation Handler for Smart CLI."""

import re

from rich.console import Console

from .base_handler import BaseHandler

console = Console()


class ProjectHandler(BaseHandler):
    """Handler for project generation and scaffolding requests."""

    @property
    def keywords(self) -> list[str]:
        """Keywords that trigger project operations."""
        return [
            "create",
            "generate",
            "scaffold",
            "new project",
            "make project",
            "yarat",
            "yeni layihə",
            "project",
            "app",
            "application",
            "fastapi",
            "react",
            "express",
            "django",
            "flutter",
            "vue",
        ]

    async def handle(self, user_input: str) -> bool:
        """Handle project generation and scaffolding requests."""
        if not self.matches_input(user_input):
            return False

        self.log_debug(f"Processing project generation: {user_input}")
        await self._process_project_generation(user_input)
        return True

    async def _process_project_generation(self, request: str):
        """Process project generation requests."""
        lower_request = request.lower()

        # Show available templates
        if any(
            word in lower_request for word in ["list", "templates", "available", "show"]
        ):
            self.smart_cli.project_generator._display_available_templates()
            return

        # Extract template and project name
        template_name = self._extract_template_name(lower_request)
        project_name = self._extract_project_name(request)

        # Default names
        if not template_name:
            template_name = self._determine_default_template(lower_request)

        if not project_name:
            project_name = f"smart-cli-{template_name}-project"

        # Clean project name
        project_name = re.sub(r"[^a-zA-Z0-9\\-_]", "-", project_name).lower()

        # Create project
        await self._create_project(template_name, project_name)

    def _extract_template_name(self, lower_request: str) -> str:
        """Extract template name from request."""
        template_mapping = {
            "fastapi": "fastapi",
            "react": "react-ts",
            "typescript react": "react-ts",
            "express": "express-api",
            "node": "express-api",
            "nodejs": "express-api",
            "django": "django",
            "flask": "flask",
            "vue": "vue",
            "flutter": "flutter",
        }

        for keyword, template in template_mapping.items():
            if keyword in lower_request:
                return template

        return None

    def _extract_project_name(self, request: str) -> str:
        """Extract project name from request."""
        # Try to find quoted project name
        quoted_match = re.search(r'["\']([^"\']+)["\']', request)
        if quoted_match:
            return quoted_match.group(1)

        # Try to find project name after "called" or "named"
        for word in ["called", "named", "adlandı"]:
            if word in request.lower():
                parts = request.split(word, 1)
                if len(parts) > 1:
                    project_name = parts[1].strip().split()[0]
                    return project_name

        return None

    def _determine_default_template(self, lower_request: str) -> str:
        """Determine default template based on request context."""
        if "api" in lower_request:
            return "fastapi"
        elif "web" in lower_request or "frontend" in lower_request:
            return "react-ts"
        else:
            return "fastapi"  # Default

    async def _create_project(self, template_name: str, project_name: str):
        """Create project with the specified template."""
        templates = self.smart_cli.project_generator.list_templates()

        if template_name in templates:
            self.ui_manager.display_success(
                f"Creating {template_name} project: {project_name}"
            )

            success = await self.smart_cli.project_generator.create_project(
                template_name, project_name
            )

            if not success:
                self.ui_manager.display_error("Project creation failed")
        else:
            self.ui_manager.display_error(
                f"Available templates: {', '.join(templates)}"
            )
