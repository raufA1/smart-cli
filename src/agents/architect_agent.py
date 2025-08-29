"""Intelligent System Architect Agent - AI-powered architecture design and system planning."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

from .base_agent import BaseAgent

console = Console()


class ArchitectAgent(BaseAgent):
    """Intelligent System Architect Agent - AI-powered expert for system architecture and design."""

    def __init__(self, ai_client=None):
        super().__init__(ai_client)
        self.agent_name = "System Architect Agent"
        self.agent_emoji = "🏗️"
        self.expertise_areas = [
            "System Architecture Design",
            "Scalability Planning",
            "Technology Stack Selection",
            "Design Pattern Implementation",
            "Integration Architecture",
            "Security Architecture",
            "Performance Architecture",
        ]

    async def execute(self, target: str, description: str) -> "AgentReport":
        """Execute intelligent architectural design and planning."""
        from .base_agent import AgentReport

        self.start_task(description)
        created_files = []
        modified_files = []
        errors = []
        warnings = []

        try:
            if not self.ai_client:
                warning_msg = (
                    "No AI client - providing basic architecture analysis only"
                )
                self.log_warning(warning_msg)
                warnings.append(warning_msg)
                return await self._basic_architecture_fallback(target, description)

            self.log_info("🏗️ Starting intelligent architectural analysis...")

            # Phase 1: Analyze current system state
            current_state = await self._analyze_current_architecture(target)

            # Phase 2: AI-powered architectural design
            architecture_design = await self._design_optimal_architecture(
                target, description, current_state
            )

            # Phase 3: Generate implementation roadmap
            implementation_plan = await self._create_implementation_roadmap(
                architecture_design, current_state
            )

            # Phase 4: Create architectural documentation
            documentation_files = await self._create_architecture_documentation(
                architecture_design, implementation_plan, target
            )
            created_files.extend(documentation_files)

            self.log_success(
                f"✅ Architectural design completed: {len(architecture_design.get('components', []))} components planned"
            )

            return self.create_task_result(
                success=True,
                task_description=description,
                created_files=created_files,
                modified_files=modified_files,
                errors=errors,
                warnings=warnings,
                output_data={
                    "target": target,
                    "task_type": "intelligent_architecture_design",
                    "current_state": current_state,
                    "architecture_design": architecture_design,
                    "implementation_plan": implementation_plan,
                },
                next_recommendations=implementation_plan.get(
                    "next_steps", ["Review architecture design"]
                ),
            )

        except Exception as e:
            error_msg = f"Architectural design failed: {str(e)}"
            self.log_error(error_msg)
            errors.append(error_msg)

            return self.create_task_result(
                success=False,
                task_description=description,
                errors=errors,
                output_data={"target": target, "exception": str(e)},
            )

    async def _analyze_current_architecture(self, target: str) -> Dict[str, Any]:
        """Analyze the current system architecture intelligently."""
        self.log_info("🔍 Analyzing current system architecture...")

        current_state = {
            "target_path": target,
            "architecture_type": "unknown",
            "components": [],
            "dependencies": [],
            "patterns": [],
            "strengths": [],
            "weaknesses": [],
            "complexity_score": 0,
        }

        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    # Single file analysis
                    current_state["scope"] = "single_file"
                    current_state["file_type"] = Path(target).suffix

                    # Analyze file content for patterns
                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    current_state["file_size"] = len(content)
                    current_state["patterns"] = self._identify_code_patterns(content)

                elif os.path.isdir(target):
                    # Directory/project analysis
                    current_state["scope"] = "project"
                    current_state["components"] = (
                        await self._identify_project_components(target)
                    )
                    current_state["dependencies"] = await self._analyze_dependencies(
                        target
                    )
                    current_state["architecture_type"] = (
                        await self._identify_architecture_pattern(target)
                    )
                    current_state["complexity_score"] = (
                        await self._calculate_complexity_score(target)
                    )

        except Exception as e:
            self.log_warning(f"Current state analysis error: {e}")

        return current_state

    def _identify_code_patterns(self, content: str) -> List[str]:
        """Identify design patterns and architectural patterns in code."""
        patterns = []

        # Check for common patterns
        if "class" in content and "def __init__" in content:
            patterns.append("Object-Oriented Design")
        if "async def" in content:
            patterns.append("Asynchronous Programming")
        if "import abc" in content or "ABC" in content:
            patterns.append("Abstract Base Classes")
        if "singleton" in content.lower():
            patterns.append("Singleton Pattern")
        if "factory" in content.lower():
            patterns.append("Factory Pattern")
        if "observer" in content.lower():
            patterns.append("Observer Pattern")
        if "decorator" in content or "@" in content:
            patterns.append("Decorator Pattern")

        return patterns

    async def _identify_project_components(
        self, project_path: str
    ) -> List[Dict[str, str]]:
        """Identify major components in the project."""
        components = []

        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_path)

                    # Categorize based on naming patterns and location
                    component_type = self._categorize_component(file, relative_path)
                    components.append(
                        {
                            "name": file,
                            "path": relative_path,
                            "type": component_type,
                            "size": os.path.getsize(file_path),
                        }
                    )

        return components

    def _categorize_component(self, filename: str, path: str) -> str:
        """Categorize component based on filename and path patterns."""
        filename_lower = filename.lower()
        path_lower = path.lower()

        if "test" in filename_lower or "test" in path_lower:
            return "test"
        elif filename_lower in ["main.py", "app.py", "__main__.py"]:
            return "entry_point"
        elif filename_lower in ["config.py", "settings.py"]:
            return "configuration"
        elif "model" in filename_lower or "models" in path_lower:
            return "data_model"
        elif "view" in filename_lower or "views" in path_lower:
            return "presentation"
        elif "controller" in filename_lower or "handlers" in path_lower:
            return "business_logic"
        elif "util" in filename_lower or "helper" in filename_lower:
            return "utility"
        elif "api" in filename_lower or "endpoint" in filename_lower:
            return "api_interface"
        elif "database" in filename_lower or "db" in filename_lower:
            return "data_access"
        else:
            return "core_logic"

    async def _analyze_dependencies(self, project_path: str) -> List[Dict[str, Any]]:
        """Analyze project dependencies intelligently."""
        dependencies = []

        # Check requirements.txt
        req_file = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dep_name = line.split("==")[0].split(">=")[0].split("<=")[0]
                            dependencies.append(
                                {
                                    "name": dep_name,
                                    "source": "requirements.txt",
                                    "type": "external",
                                }
                            )
            except Exception:
                pass

        # Check pyproject.toml
        pyproject_file = os.path.join(project_path, "pyproject.toml")
        if os.path.exists(pyproject_file):
            dependencies.append(
                {
                    "name": "pyproject.toml configuration",
                    "source": "pyproject.toml",
                    "type": "build_system",
                }
            )

        # Check package.json for Node.js projects
        package_file = os.path.join(project_path, "package.json")
        if os.path.exists(package_file):
            try:
                with open(package_file, "r") as f:
                    package_data = json.load(f)
                    for dep in package_data.get("dependencies", {}):
                        dependencies.append(
                            {
                                "name": dep,
                                "source": "package.json",
                                "type": "nodejs_dependency",
                            }
                        )
            except Exception:
                pass

        return dependencies

    async def _identify_architecture_pattern(self, project_path: str) -> str:
        """Identify the overall architecture pattern of the project."""
        components = await self._identify_project_components(project_path)
        component_types = [comp["type"] for comp in components]

        # Analyze patterns
        if (
            "data_model" in component_types
            and "presentation" in component_types
            and "business_logic" in component_types
        ):
            return "Model-View-Controller (MVC)"
        elif (
            "api_interface" in component_types
            and "business_logic" in component_types
            and "data_access" in component_types
        ):
            return "Layered Architecture"
        elif len([c for c in component_types if c == "core_logic"]) > 3:
            return "Modular Monolith"
        elif "api_interface" in component_types:
            return "Service-Oriented"
        else:
            return "Simple/Flat Structure"

    async def _calculate_complexity_score(self, project_path: str) -> int:
        """Calculate architecture complexity score (1-10)."""
        components = await self._identify_project_components(project_path)
        dependencies = await self._analyze_dependencies(project_path)

        # Base score
        score = 1

        # Component count factor
        component_count = len(components)
        if component_count > 20:
            score += 3
        elif component_count > 10:
            score += 2
        elif component_count > 5:
            score += 1

        # Dependency factor
        dep_count = len(dependencies)
        if dep_count > 15:
            score += 2
        elif dep_count > 8:
            score += 1

        # Directory depth factor
        max_depth = 0
        for root, dirs, files in os.walk(project_path):
            depth = root[len(project_path) :].count(os.sep)
            max_depth = max(max_depth, depth)

        if max_depth > 4:
            score += 2
        elif max_depth > 2:
            score += 1

        return min(score, 10)  # Cap at 10

    async def _design_optimal_architecture(
        self, target: str, description: str, current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Design optimal architecture using AI intelligence."""
        self.log_info("🤖 Designing optimal architecture with AI...")

        architecture_prompt = f"""
You are a senior system architect with expertise in designing scalable, maintainable software systems.

DESIGN REQUEST: {description}
TARGET: {target}

CURRENT SYSTEM STATE:
- Architecture Type: {current_state.get('architecture_type', 'Unknown')}
- Components: {len(current_state.get('components', []))} files
- Dependencies: {len(current_state.get('dependencies', []))} external deps
- Complexity Score: {current_state.get('complexity_score', 0)}/10
- Identified Patterns: {', '.join(current_state.get('patterns', []))}

Please design an optimal architecture that addresses the request while considering the current state:

1. SYSTEM ARCHITECTURE:
   - Recommend the best architectural pattern (MVC, Microservices, Layered, etc.)
   - Define major system components and their responsibilities
   - Specify component interactions and data flow

2. TECHNOLOGY STACK:
   - Recommend appropriate technologies for each layer
   - Consider performance, scalability, and maintainability
   - Suggest modern alternatives where beneficial

3. DESIGN PATTERNS:
   - Identify design patterns that should be implemented
   - Specify where each pattern provides value
   - Consider SOLID principles and clean architecture

4. SCALABILITY STRATEGY:
   - Plan for horizontal and vertical scaling
   - Identify potential bottlenecks
   - Suggest caching and optimization strategies

5. SECURITY ARCHITECTURE:
   - Define authentication and authorization strategy
   - Identify security layers and controls
   - Consider data protection and privacy requirements

6. DEPLOYMENT ARCHITECTURE:
   - Recommend deployment patterns (containerization, serverless, etc.)
   - Consider CI/CD pipeline requirements
   - Plan for different environments (dev, staging, prod)

Provide detailed, implementable recommendations formatted as structured JSON.
"""

        try:
            response = await self.ai_client.generate_response(architecture_prompt)
            if response and response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {"raw_design": response.content}
            else:
                return {"error": "No architecture design generated"}

        except Exception as e:
            self.log_warning(f"AI architecture design error: {e}")
            return {"error": str(e)}

    async def _create_implementation_roadmap(
        self, architecture_design: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed implementation roadmap."""
        self.log_info("🗺️ Creating implementation roadmap...")

        roadmap_prompt = f"""
Based on the architectural design and current system state, create a detailed implementation roadmap:

ARCHITECTURAL DESIGN:
{json.dumps(architecture_design, indent=2)}

CURRENT STATE:
{json.dumps(current_state, indent=2)}

Please provide:

1. IMPLEMENTATION PHASES:
   - Phase 1: Immediate actions (Week 1-2)
   - Phase 2: Core development (Week 3-6)
   - Phase 3: Integration & testing (Week 7-8)
   - Phase 4: Optimization & deployment (Week 9-10)

2. TASK BREAKDOWN:
   - Specific tasks for each phase
   - Dependencies between tasks
   - Estimated effort for each task

3. RISK MITIGATION:
   - Identified risks and challenges
   - Mitigation strategies
   - Contingency plans

4. SUCCESS METRICS:
   - Key performance indicators
   - Quality gates
   - Acceptance criteria

5. RESOURCE REQUIREMENTS:
   - Required skills and expertise
   - Development tools and environments
   - External dependencies

Format as structured JSON with clear prioritization and timelines.
"""

        try:
            response = await self.ai_client.generate_response(roadmap_prompt)
            if response and response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {
                        "phases": ["Analysis", "Design", "Implementation", "Testing"],
                        "next_steps": ["Start with Phase 1 tasks"],
                    }
            else:
                return {"error": "Could not generate roadmap"}

        except Exception as e:
            self.log_warning(f"Roadmap generation error: {e}")
            return {"error": str(e)}

    async def _create_architecture_documentation(
        self,
        architecture_design: Dict[str, Any],
        implementation_plan: Dict[str, Any],
        target: str,
    ) -> List[str]:
        """Create comprehensive architecture documentation."""
        self.log_info("📚 Creating architecture documentation...")

        created_files = []

        try:
            # 1. Architecture Overview Document
            overview_file = f"architecture_overview_{self.get_timestamp()}.md"
            overview_content = f"""# System Architecture Overview

## Target: {target}
## Generated: {self.get_timestamp()}
## Architect: Smart CLI Intelligent Architect Agent

---

## Architecture Design

{json.dumps(architecture_design, indent=2)}

---

## Implementation Roadmap

{json.dumps(implementation_plan, indent=2)}

---

*Generated by Smart CLI Intelligent Architect Agent*
"""

            with open(overview_file, "w", encoding="utf-8") as f:
                f.write(overview_content)
            created_files.append(overview_file)

            # 2. Technical Specifications
            tech_specs_file = f"technical_specifications_{self.get_timestamp()}.md"
            tech_specs_content = f"""# Technical Specifications

## System Components
{self._format_components(architecture_design.get('components', []))}

## Technology Stack
{self._format_tech_stack(architecture_design.get('technology_stack', {}))}

## Design Patterns
{self._format_design_patterns(architecture_design.get('design_patterns', []))}

## Security Requirements
{self._format_security_reqs(architecture_design.get('security_architecture', {}))}
"""

            with open(tech_specs_file, "w", encoding="utf-8") as f:
                f.write(tech_specs_content)
            created_files.append(tech_specs_file)

            self.log_success(f"Created {len(created_files)} architecture documents")

        except Exception as e:
            self.log_warning(f"Documentation creation error: {e}")

        return created_files

    def _format_components(self, components: List[Dict[str, Any]]) -> str:
        """Format components for documentation."""
        if not components:
            return "No components defined."

        formatted = ""
        for comp in components:
            formatted += f"- **{comp.get('name', 'Unknown')}**: {comp.get('description', 'No description')}\n"
        return formatted

    def _format_tech_stack(self, tech_stack: Dict[str, Any]) -> str:
        """Format technology stack for documentation."""
        if not tech_stack:
            return "No technology stack defined."

        formatted = ""
        for layer, technologies in tech_stack.items():
            formatted += f"- **{layer.title()}**: {', '.join(technologies) if isinstance(technologies, list) else technologies}\n"
        return formatted

    def _format_design_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format design patterns for documentation."""
        if not patterns:
            return "No specific design patterns recommended."

        formatted = ""
        for pattern in patterns:
            formatted += f"- **{pattern.get('name', 'Unknown')}**: {pattern.get('usage', 'No usage specified')}\n"
        return formatted

    def _format_security_reqs(self, security: Dict[str, Any]) -> str:
        """Format security requirements for documentation."""
        if not security:
            return "No specific security requirements defined."

        formatted = ""
        for requirement, details in security.items():
            formatted += f"- **{requirement.replace('_', ' ').title()}**: {details}\n"
        return formatted

    async def _basic_architecture_fallback(
        self, target: str, description: str
    ) -> "AgentReport":
        """Basic architecture analysis when AI client is not available."""
        from .base_agent import AgentReport

        self.log_info("Performing basic architecture analysis (no AI client)...")

        warnings = []
        output_data = {}

        try:
            # Basic analysis of project structure
            if os.path.exists(target):
                if os.path.isdir(target):
                    components = await self._identify_project_components(target)
                    dependencies = await self._analyze_dependencies(target)

                    output_data = {
                        "component_count": len(components),
                        "dependency_count": len(dependencies),
                        "architecture_type": await self._identify_architecture_pattern(
                            target
                        ),
                        "recommendations": [
                            "Set up AI client for intelligent architecture design",
                            "Review component organization",
                            "Consider dependency optimization",
                        ],
                    }

                self.log_success("Basic architecture analysis completed")
                return self.create_task_result(
                    success=True,
                    task_description=description,
                    warnings=warnings,
                    output_data=output_data,
                    next_recommendations=[
                        "Configure AI client for full architectural analysis"
                    ],
                )
            else:
                return self.create_task_result(
                    success=False,
                    task_description=description,
                    errors=[f"Target not found: {target}"],
                )

        except Exception as e:
            return self.create_task_result(
                success=False,
                task_description=description,
                errors=[f"Basic architecture analysis failed: {e}"],
            )

    def get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
