"""Intelligent Code Analyzer Agent - AI-powered code analysis and understanding."""

import ast
import json
import os
import re
from pathlib import Path

from .base_agent import BaseAgent


class AnalyzerAgent(BaseAgent):
    """Intelligent Code Analyzer Agent - AI-powered expert for deep code analysis."""

    def __init__(self, ai_client=None, config_manager=None):
        super().__init__(ai_client, config_manager)
        self.agent_name = "Code Analyzer Agent"
        self.agent_emoji = "🔍"
        self.expertise_areas = [
            "Code Quality Assessment",
            "Architecture Analysis",
            "Security Vulnerability Detection",
            "Performance Bottleneck Identification",
            "Dependency Analysis",
            "Code Pattern Recognition",
            "Technical Debt Assessment",
        ]

    async def execute(self, target: str, description: str) -> "AgentReport":
        """Execute intelligent AI-powered code analysis."""
        from .base_agent import AgentReport

        self.start_task(description)
        created_files = []
        modified_files = []
        errors = []
        warnings = []

        try:
            if not self.ai_client:
                warning_msg = "No AI client - performing basic analysis only"
                self.log_warning(warning_msg)
                warnings.append(warning_msg)
                return await self._basic_analysis_fallback(target, description)

            self.log_info("🧠 Starting intelligent code analysis...")

            # Phase 1: Gather comprehensive project context
            project_context = await self._gather_project_context(target)

            # Phase 2: AI-powered deep analysis
            analysis_results = await self._perform_intelligent_analysis(
                target, description, project_context
            )

            # Phase 3: Generate actionable insights and recommendations
            insights = await self._generate_analysis_insights(
                analysis_results, project_context
            )

            # Phase 4: Create analysis report
            report_file = await self._create_analysis_report(insights, target)
            if report_file:
                created_files.append(report_file)

            self.log_success(
                f"✅ Intelligent analysis completed: {len(insights.get('recommendations', []))} recommendations"
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
                    "task_type": "intelligent_code_analysis",
                    "insights": insights,
                    "project_context": project_context,
                },
                next_recommendations=insights.get(
                    "next_steps", ["Review analysis report"]
                ),
            )

        except Exception as e:
            error_msg = f"Intelligent analysis failed: {str(e)}"
            self.log_error(error_msg)
            errors.append(error_msg)

            return self.create_task_result(
                success=False,
                task_description=description,
                errors=errors,
                output_data={"target": target, "exception": str(e)},
            )

    async def _gather_project_context(self, target: str) -> dict:
        """Gather comprehensive project context using AI analysis."""
        self.log_info("📊 Gathering project context...")

        context = {
            "target_path": target,
            "file_structure": {},
            "technologies": [],
            "project_type": "unknown",
            "complexity_level": "medium",
        }

        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    # Single file analysis
                    context["target_type"] = "file"
                    context["file_extension"] = Path(target).suffix

                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    context["file_size"] = len(content)
                    context["line_count"] = content.count("\n") + 1

                elif os.path.isdir(target):
                    # Directory structure analysis
                    context["target_type"] = "directory"
                    context["file_structure"] = await self._analyze_directory_structure(
                        target
                    )
                    context["technologies"] = await self._detect_technologies(target)
                    context["project_type"] = await self._identify_project_type(target)

        except Exception as e:
            self.log_warning(f"Context gathering error: {e}")

        return context

    async def _analyze_directory_structure(self, directory: str) -> dict:
        """Analyze directory structure intelligently."""
        structure = {
            "total_files": 0,
            "file_types": {},
            "directories": [],
            "important_files": [],
        }

        important_file_patterns = [
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            "docker-compose.yml",
            "README.md",
            "LICENSE",
            ".env",
            "config.py",
            "settings.py",
        ]

        for root, dirs, files in os.walk(directory):
            structure["directories"].extend(dirs)
            structure["total_files"] += len(files)

            for file in files:
                ext = Path(file).suffix
                if ext:
                    structure["file_types"][ext] = (
                        structure["file_types"].get(ext, 0) + 1
                    )

                if file in important_file_patterns:
                    structure["important_files"].append(os.path.join(root, file))

        return structure

    async def _detect_technologies(self, target: str) -> list:
        """Detect technologies used in the project."""
        technologies = []

        # Check for Python
        if self._has_files_with_extension(target, ".py"):
            technologies.append("Python")

        # Check for JavaScript/Node.js
        if self._has_files_with_extension(target, ".js") or os.path.exists(
            os.path.join(target, "package.json")
        ):
            technologies.append("JavaScript/Node.js")

        # Check for web technologies
        if self._has_files_with_extension(target, ".html"):
            technologies.append("HTML")
        if self._has_files_with_extension(target, ".css"):
            technologies.append("CSS")

        # Check for Docker
        if os.path.exists(os.path.join(target, "Dockerfile")):
            technologies.append("Docker")

        return technologies

    def _has_files_with_extension(self, directory: str, extension: str) -> bool:
        """Check if directory contains files with given extension."""
        for root, dirs, files in os.walk(directory):
            if any(file.endswith(extension) for file in files):
                return True
        return False

    async def _identify_project_type(self, target: str) -> str:
        """Identify the type of project using intelligent analysis."""
        # Check for specific project indicators
        if os.path.exists(os.path.join(target, "pyproject.toml")) or os.path.exists(
            os.path.join(target, "setup.py")
        ):
            return "Python Package"
        elif os.path.exists(os.path.join(target, "package.json")):
            return "Node.js Application"
        elif os.path.exists(os.path.join(target, "requirements.txt")):
            return "Python Application"
        elif self._has_files_with_extension(target, ".py"):
            return "Python Project"
        elif self._has_files_with_extension(target, ".js"):
            return "JavaScript Project"
        else:
            return "Mixed/Other"

    async def _perform_intelligent_analysis(
        self, target: str, description: str, context: dict
    ) -> dict:
        """Perform AI-powered intelligent analysis."""
        self.log_info("🤖 Performing AI-powered analysis...")

        # Create comprehensive analysis prompt
        analysis_prompt = f"""
You are an expert code analyst with deep expertise in software architecture, security, and performance.

ANALYSIS REQUEST: {description}
TARGET: {target}

PROJECT CONTEXT:
- Project Type: {context.get('project_type', 'Unknown')}
- Technologies: {', '.join(context.get('technologies', []))}
- File Count: {context.get('file_structure', {}).get('total_files', 'N/A')}

Please analyze this codebase and provide:

1. ARCHITECTURE ANALYSIS:
   - Overall architecture pattern assessment
   - Code organization and structure evaluation
   - Module dependencies and coupling analysis

2. CODE QUALITY ASSESSMENT:
   - Code maintainability score (1-10)
   - Readability and documentation quality
   - Best practices compliance

3. SECURITY ANALYSIS:
   - Potential security vulnerabilities
   - Data handling and validation issues
   - Authentication and authorization concerns

4. PERFORMANCE ANALYSIS:
   - Performance bottlenecks identification
   - Resource usage optimization opportunities
   - Scalability considerations

5. TECHNICAL DEBT:
   - Code smells and anti-patterns
   - Refactoring opportunities
   - Modernization recommendations

Provide detailed, actionable insights with specific examples and recommendations.
Format response as structured JSON with clear categories.
"""

        try:
            response = await self.ai_client.generate_response(analysis_prompt)
            if response and response.content:
                # Try to parse as JSON, fallback to text analysis
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {"raw_analysis": response.content}
            else:
                return {"error": "No response from AI analysis"}

        except Exception as e:
            self.log_warning(f"AI analysis error: {e}")
            return {"error": str(e)}

    async def _generate_analysis_insights(
        self, analysis_results: dict, context: dict
    ) -> dict:
        """Generate actionable insights from analysis results."""
        self.log_info("💡 Generating actionable insights...")

        insights_prompt = f"""
Based on the following code analysis results, generate specific, actionable insights:

ANALYSIS RESULTS:
{json.dumps(analysis_results, indent=2)}

PROJECT CONTEXT:
{json.dumps(context, indent=2)}

Please provide:

1. TOP 5 PRIORITY RECOMMENDATIONS:
   - Specific actions to take
   - Impact assessment (High/Medium/Low)
   - Implementation effort estimate

2. QUICK WINS:
   - Easy improvements with immediate impact
   - Automated fixes that can be applied

3. LONG-TERM STRATEGY:
   - Architectural improvements
   - Technology upgrades
   - Process optimizations

4. NEXT STEPS:
   - Immediate action items
   - Dependencies and prerequisites
   - Success metrics

Format as structured JSON with clear categorization.
"""

        try:
            response = await self.ai_client.generate_response(insights_prompt)
            if response and response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {
                        "recommendations": ["Review the analysis results"],
                        "quick_wins": ["Basic code cleanup"],
                        "next_steps": ["Implement priority recommendations"],
                    }
            else:
                return {"error": "Could not generate insights"}

        except Exception as e:
            self.log_warning(f"Insights generation error: {e}")
            return {"error": str(e)}

    async def _create_analysis_report(self, insights: dict, target: str) -> str:
        """Create a comprehensive analysis report file."""
        self.log_info("📄 Creating analysis report...")

        try:
            report_filename = (
                f"analysis_report_{Path(target).name}_{self.get_timestamp()}.md"
            )

            report_content = f"""# Code Analysis Report
            
## Target: {target}
## Generated: {self.get_timestamp()}
## Analyzer: Smart CLI Intelligent Analyzer Agent

---

## Executive Summary

{json.dumps(insights, indent=2)}

---

## Recommendations

### Priority Actions
{self._format_recommendations(insights.get('recommendations', []))}

### Quick Wins  
{self._format_quick_wins(insights.get('quick_wins', []))}

### Next Steps
{self._format_next_steps(insights.get('next_steps', []))}

---

*Generated by Smart CLI Intelligent Analyzer Agent*
"""

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(report_content)

            self.log_success(f"Analysis report created: {report_filename}")
            return report_filename

        except Exception as e:
            self.log_warning(f"Report creation error: {e}")
            return None

    def _format_recommendations(self, recommendations: list) -> str:
        """Format recommendations for report."""
        if not recommendations:
            return "No specific recommendations available."

        formatted = ""
        for i, rec in enumerate(recommendations, 1):
            formatted += f"{i}. {rec}\n"
        return formatted

    def _format_quick_wins(self, quick_wins: list) -> str:
        """Format quick wins for report."""
        if not quick_wins:
            return "No quick wins identified."

        formatted = ""
        for win in quick_wins:
            formatted += f"- {win}\n"
        return formatted

    def _format_next_steps(self, next_steps: list) -> str:
        """Format next steps for report."""
        if not next_steps:
            return "No specific next steps defined."

        formatted = ""
        for step in next_steps:
            formatted += f"→ {step}\n"
        return formatted

    async def _basic_analysis_fallback(
        self, target: str, description: str
    ) -> "AgentReport":
        """Basic analysis when AI client is not available."""
        from .base_agent import AgentReport

        self.log_info("Performing basic analysis (no AI client)...")

        errors = []
        warnings = []
        output_data = {}

        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    output_data = {
                        "file_size": len(content),
                        "line_count": content.count("\n") + 1,
                        "file_type": Path(target).suffix,
                    }

                elif os.path.isdir(target):
                    files = list(Path(target).rglob("*"))
                    output_data = {
                        "total_files": len([f for f in files if f.is_file()]),
                        "directories": len([f for f in files if f.is_dir()]),
                    }

                self.log_success("Basic analysis completed")
                return self.create_task_result(
                    success=True,
                    task_description=description,
                    warnings=warnings,
                    output_data=output_data,
                    next_recommendations=["Set up AI client for intelligent analysis"],
                )
            else:
                error_msg = f"Target not found: {target}"
                errors.append(error_msg)
                return self.create_task_result(
                    success=False, task_description=description, errors=errors
                )

        except Exception as e:
            error_msg = f"Basic analysis failed: {e}"
            errors.append(error_msg)
            return self.create_task_result(
                success=False, task_description=description, errors=errors
            )

    def get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
