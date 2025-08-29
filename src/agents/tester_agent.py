"""Intelligent Testing Agent - AI-powered comprehensive testing and validation."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .base_agent import BaseAgent


class TesterAgent(BaseAgent):
    """Intelligent Testing Agent - AI-powered expert for comprehensive testing strategies."""

    def __init__(self, ai_client=None, config_manager=None):
        super().__init__(ai_client, config_manager)
        self.agent_name = "Testing Agent"
        self.agent_emoji = "🧪"
        self.expertise_areas = [
            "Test Strategy Design",
            "Test Case Generation",
            "Test Automation",
            "Performance Testing",
            "Security Testing",
            "Integration Testing",
            "Quality Assurance",
        ]

    async def execute(self, target: str, description: str) -> "AgentReport":
        """Execute intelligent comprehensive testing and validation."""
        from .base_agent import AgentReport

        self.start_task(description)
        created_files = []
        modified_files = []
        errors = []
        warnings = []

        try:
            if not self.ai_client:
                warning_msg = "No AI client - performing basic testing only"
                self.log_warning(warning_msg)
                warnings.append(warning_msg)
                return await self._basic_testing_fallback(target, description)

            self.log_info("🧪 Starting intelligent testing analysis...")

            # Phase 1: Analyze code for testing requirements
            testing_analysis = await self._analyze_testing_requirements(
                target, description
            )

            # Phase 2: Design comprehensive test strategy
            test_strategy = await self._design_test_strategy(
                target, description, testing_analysis
            )

            # Phase 3: Generate test cases and test code
            test_implementation = await self._generate_test_implementation(
                test_strategy, testing_analysis
            )
            created_files.extend(test_implementation.get("created_files", []))

            # Phase 4: Execute tests and validate results
            test_results = await self._execute_and_validate_tests(
                test_implementation, target
            )

            # Phase 5: Create testing report
            report_file = await self._create_testing_report(
                test_strategy, test_results, target
            )
            if report_file:
                created_files.append(report_file)

            self.log_success(
                f"✅ Intelligent testing completed: {len(test_results.get('test_cases', []))} tests executed"
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
                    "task_type": "intelligent_testing",
                    "testing_analysis": testing_analysis,
                    "test_strategy": test_strategy,
                    "test_results": test_results,
                },
                next_recommendations=test_results.get(
                    "next_steps", ["Review test results"]
                ),
            )

        except Exception as e:
            error_msg = f"Intelligent testing failed: {str(e)}"
            self.log_error(error_msg)
            errors.append(error_msg)

            return self.create_task_result(
                success=False,
                task_description=description,
                errors=errors,
                output_data={"target": target, "exception": str(e)},
            )

    async def _analyze_testing_requirements(
        self, target: str, description: str
    ) -> Dict[str, Any]:
        """Analyze code to identify testing requirements using AI."""
        self.log_info("🔍 Analyzing testing requirements...")

        requirements = {
            "target_type": "unknown",
            "complexity_level": "medium",
            "testing_types_needed": [],
            "critical_functions": [],
            "dependencies": [],
            "risk_areas": [],
        }

        try:
            if os.path.exists(target):
                if os.path.isfile(target):
                    # Single file analysis
                    requirements["target_type"] = "single_file"
                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    requirements["file_extension"] = Path(target).suffix
                    requirements["line_count"] = content.count("\n") + 1
                    requirements["critical_functions"] = (
                        self._identify_critical_functions(content)
                    )
                    requirements["dependencies"] = self._identify_test_dependencies(
                        content
                    )

                elif os.path.isdir(target):
                    # Project analysis
                    requirements["target_type"] = "project"
                    requirements["project_structure"] = (
                        await self._analyze_project_structure(target)
                    )
                    requirements["testing_types_needed"] = (
                        await self._identify_required_testing_types(target)
                    )

        except Exception as e:
            self.log_warning(f"Testing requirements analysis error: {e}")

        return requirements

    def _identify_critical_functions(self, content: str) -> List[Dict[str, str]]:
        """Identify critical functions that need comprehensive testing."""
        functions = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") or line.strip().startswith("async def "):
                func_name = line.split("def ")[1].split("(")[0].strip()

                # Categorize function criticality
                criticality = "medium"
                if any(
                    keyword in func_name.lower()
                    for keyword in [
                        "main",
                        "init",
                        "create",
                        "delete",
                        "auth",
                        "login",
                        "pay",
                    ]
                ):
                    criticality = "high"
                elif any(
                    keyword in func_name.lower()
                    for keyword in ["helper", "util", "format", "log"]
                ):
                    criticality = "low"

                functions.append(
                    {
                        "name": func_name,
                        "line": i + 1,
                        "criticality": criticality,
                        "async": "async" in line,
                    }
                )

        return functions

    def _identify_test_dependencies(self, content: str) -> List[str]:
        """Identify dependencies that need mocking or special handling in tests."""
        dependencies = []

        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                # Extract external dependencies
                if "requests" in line:
                    dependencies.append("HTTP mocking needed")
                if "database" in line.lower() or "db" in line.lower():
                    dependencies.append("Database mocking needed")
                if "asyncio" in line:
                    dependencies.append("Async testing framework needed")
                if "json" in line:
                    dependencies.append("JSON validation testing needed")

        return dependencies

    async def _analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure for testing needs."""
        structure = {
            "python_files": [],
            "test_files": [],
            "config_files": [],
            "has_existing_tests": False,
        }

        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)

                if file.endswith(".py"):
                    if "test" in file.lower() or "test" in root.lower():
                        structure["test_files"].append(file_path)
                        structure["has_existing_tests"] = True
                    else:
                        structure["python_files"].append(file_path)

                elif file in ["requirements.txt", "pyproject.toml", "setup.py"]:
                    structure["config_files"].append(file_path)

        return structure

    async def _identify_required_testing_types(self, project_path: str) -> List[str]:
        """Identify what types of testing are needed for the project."""
        testing_types = ["unit_testing"]  # Always needed

        # Check for specific patterns that require additional testing
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()

                        if "async def" in content:
                            testing_types.append("async_testing")
                        if "database" in content.lower() or "db" in content.lower():
                            testing_types.append("integration_testing")
                        if "api" in content.lower() or "endpoint" in content.lower():
                            testing_types.append("api_testing")
                        if (
                            "performance" in content.lower()
                            or "benchmark" in content.lower()
                        ):
                            testing_types.append("performance_testing")

                    except Exception:
                        continue

        return list(set(testing_types))

    async def _design_test_strategy(
        self, target: str, description: str, testing_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Design comprehensive test strategy using AI intelligence."""
        self.log_info("🤖 Designing test strategy with AI...")

        strategy_prompt = f"""
You are a senior QA engineer and test architect with expertise in comprehensive testing strategies.

TESTING REQUEST: {description}
TARGET: {target}

TESTING ANALYSIS:
{json.dumps(testing_analysis, indent=2)}

Please design a comprehensive testing strategy:

1. TEST STRATEGY OVERVIEW:
   - Testing approach and methodology
   - Testing scope and objectives
   - Success criteria and acceptance tests

2. TEST TYPES AND COVERAGE:
   - Unit testing strategy
   - Integration testing plan
   - System testing approach
   - Performance testing requirements
   - Security testing considerations

3. TEST CASE DESIGN:
   - Critical test scenarios
   - Edge case identification
   - Error handling validation
   - Data validation tests

4. TEST AUTOMATION:
   - Automation framework recommendations
   - CI/CD integration strategy
   - Test execution pipeline

5. RISK-BASED TESTING:
   - High-risk areas identification
   - Critical path testing
   - Mitigation strategies

6. TEST DATA MANAGEMENT:
   - Test data requirements
   - Mock data strategies
   - Environment setup needs

Provide detailed, implementable testing strategy formatted as structured JSON.
"""

        try:
            response = await self.ai_client.generate_response(strategy_prompt)
            if response and response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {"raw_strategy": response.content}
            else:
                return {"error": "No test strategy generated"}

        except Exception as e:
            self.log_warning(f"AI test strategy design error: {e}")
            return {"error": str(e)}

    async def _generate_test_implementation(
        self, test_strategy: Dict[str, Any], testing_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actual test code and test cases using AI."""
        self.log_info("⚙️ Generating test implementation...")

        implementation_prompt = f"""
Based on the test strategy and analysis, generate comprehensive test code:

TEST STRATEGY:
{json.dumps(test_strategy, indent=2)}

TESTING ANALYSIS:
{json.dumps(testing_analysis, indent=2)}

Please generate:

1. TEST FILES:
   - Unit test files with comprehensive test cases
   - Integration test files
   - Configuration test files
   - Test utilities and helpers

2. TEST FRAMEWORKS:
   - Recommend appropriate testing frameworks (pytest, unittest, etc.)
   - Mock and fixture configurations
   - Test runners and setup

3. SPECIFIC TEST CASES:
   - Happy path tests
   - Edge case tests
   - Error handling tests
   - Performance tests

Format as multiple files with clear structure:

FILE: test_main.py
```python
# Test code here
```

FILE: test_utils.py
```python
# Test utilities here
```

Provide complete, executable test code.
"""

        try:
            response = await self.ai_client.generate_response(implementation_prompt)
            if response and response.content:
                return await self._parse_test_implementation(response.content)
            else:
                return {
                    "error": "No test implementation generated",
                    "created_files": [],
                }

        except Exception as e:
            self.log_warning(f"Test implementation generation error: {e}")
            return {"error": str(e), "created_files": []}

    async def _parse_test_implementation(self, content: str) -> Dict[str, Any]:
        """Parse AI response and create test files."""
        created_files = []

        # Split response into individual test files
        file_blocks = content.split("FILE: ")

        for block in file_blocks[1:]:  # Skip empty first element
            try:
                lines = block.strip().split("\n")
                if not lines:
                    continue

                filename = lines[0].strip()

                # Find code block
                code_start = -1
                code_end = -1

                for i, line in enumerate(lines):
                    if line.startswith("```"):
                        if code_start == -1:
                            code_start = i + 1
                        else:
                            code_end = i
                            break

                if code_start != -1:
                    if code_end == -1:
                        code_end = len(lines)

                    code_content = "\n".join(lines[code_start:code_end])

                    # Create test file
                    test_filename = (
                        f"test_{filename}"
                        if not filename.startswith("test_")
                        else filename
                    )
                    with open(test_filename, "w", encoding="utf-8") as f:
                        f.write(code_content)

                    created_files.append(test_filename)
                    self.log_success(f"Generated test file: {test_filename}")

            except Exception as e:
                self.log_warning(f"Failed to create test file from block: {e}")

        return {
            "created_files": created_files,
            "test_framework": "pytest",  # Default assumption
            "status": "generated",
        }

    async def _execute_and_validate_tests(
        self, test_implementation: Dict[str, Any], target: str
    ) -> Dict[str, Any]:
        """Execute generated tests and validate results."""
        self.log_info("🚀 Executing tests and validating results...")

        test_results = {
            "executed_tests": [],
            "passed_tests": 0,
            "failed_tests": 0,
            "test_coverage": "unknown",
            "execution_time": 0,
            "issues_found": [],
        }

        created_files = test_implementation.get("created_files", [])

        for test_file in created_files:
            try:
                self.log_info(f"Executing test file: {test_file}")

                # Try to run with pytest first, then unittest
                for test_runner in ["pytest", "python -m unittest"]:
                    try:
                        if test_runner == "pytest":
                            cmd = f"python -m pytest {test_file} -v"
                        else:
                            cmd = f"python -m unittest {test_file}"

                        process = await asyncio.create_subprocess_shell(
                            cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )

                        stdout, stderr = await process.communicate()

                        test_result = {
                            "file": test_file,
                            "runner": test_runner,
                            "return_code": process.returncode,
                            "stdout": stdout.decode() if stdout else "",
                            "stderr": stderr.decode() if stderr else "",
                        }

                        test_results["executed_tests"].append(test_result)

                        if process.returncode == 0:
                            test_results["passed_tests"] += 1
                            self.log_success(f"Test passed: {test_file}")
                        else:
                            test_results["failed_tests"] += 1
                            test_results["issues_found"].append(
                                f"Test failed: {test_file} - {stderr.decode()}"
                            )
                            self.log_warning(f"Test failed: {test_file}")

                        break  # If one runner works, don't try others

                    except Exception as runner_error:
                        self.log_warning(
                            f"Test runner {test_runner} failed: {runner_error}"
                        )
                        continue

            except Exception as e:
                test_results["issues_found"].append(
                    f"Could not execute {test_file}: {e}"
                )
                self.log_warning(f"Could not execute test file {test_file}: {e}")

        return test_results

    async def _create_testing_report(
        self, test_strategy: Dict[str, Any], test_results: Dict[str, Any], target: str
    ) -> str:
        """Create comprehensive testing report."""
        self.log_info("📄 Creating testing report...")

        try:
            report_filename = (
                f"testing_report_{Path(target).name}_{self.get_timestamp()}.md"
            )

            report_content = f"""# Comprehensive Testing Report

## Target: {target}
## Generated: {self.get_timestamp()}
## Tester: Smart CLI Intelligent Testing Agent

---

## Test Strategy Summary

{json.dumps(test_strategy, indent=2)}

---

## Test Execution Results

### Summary
- **Total Tests Executed**: {len(test_results.get('executed_tests', []))}
- **Passed Tests**: {test_results.get('passed_tests', 0)}
- **Failed Tests**: {test_results.get('failed_tests', 0)}
- **Success Rate**: {(test_results.get('passed_tests', 0) / max(len(test_results.get('executed_tests', [])), 1) * 100):.1f}%

### Test Results Details
{self._format_test_results(test_results.get('executed_tests', []))}

### Issues Found
{self._format_issues(test_results.get('issues_found', []))}

---

## Recommendations

### Next Steps
{self._format_next_steps(test_results)}

---

*Generated by Smart CLI Intelligent Testing Agent*
"""

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(report_content)

            self.log_success(f"Testing report created: {report_filename}")
            return report_filename

        except Exception as e:
            self.log_warning(f"Report creation error: {e}")
            return None

    def _format_test_results(self, executed_tests: List[Dict[str, Any]]) -> str:
        """Format test results for report."""
        if not executed_tests:
            return "No tests were executed."

        formatted = ""
        for test in executed_tests:
            status = "✅ PASSED" if test.get("return_code") == 0 else "❌ FAILED"
            formatted += f"- **{test.get('file', 'Unknown')}**: {status}\n"

        return formatted

    def _format_issues(self, issues: List[str]) -> str:
        """Format issues for report."""
        if not issues:
            return "No issues found."

        formatted = ""
        for issue in issues:
            formatted += f"- {issue}\n"

        return formatted

    def _format_next_steps(self, test_results: Dict[str, Any]) -> str:
        """Format next steps based on test results."""
        steps = []

        if test_results.get("failed_tests", 0) > 0:
            steps.append("Fix failing tests")

        if test_results.get("passed_tests", 0) == 0:
            steps.append("Review test implementation")

        steps.extend(
            [
                "Increase test coverage",
                "Add performance tests",
                "Implement continuous testing",
            ]
        )

        formatted = ""
        for step in steps:
            formatted += f"→ {step}\n"

        return formatted

    async def _basic_testing_fallback(
        self, target: str, description: str
    ) -> "AgentReport":
        """Basic testing when AI client is not available."""
        from .base_agent import AgentReport

        self.log_info("Performing basic testing validation (no AI client)...")

        errors = []
        warnings = []
        output_data = {}

        try:
            if os.path.exists(target):
                if target.endswith(".py"):
                    # Basic Python syntax check
                    process = await asyncio.create_subprocess_shell(
                        f"python3 -m py_compile {target}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()

                    if process.returncode == 0:
                        self.log_success("Basic syntax validation passed")
                        output_data["syntax_valid"] = True
                    else:
                        error_msg = f"Syntax validation failed: {stderr.decode()}"
                        errors.append(error_msg)
                        output_data["syntax_valid"] = False

                return self.create_task_result(
                    success=len(errors) == 0,
                    task_description=description,
                    errors=errors,
                    warnings=warnings,
                    output_data=output_data,
                    next_recommendations=["Set up AI client for comprehensive testing"],
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
                errors=[f"Basic testing failed: {e}"],
            )

    def get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
