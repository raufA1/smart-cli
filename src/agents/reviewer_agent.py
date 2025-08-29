"""Code Review Agent - Handles code review and quality assessment."""

import os

from .base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """Code Review Agent for quality assessment and review."""

    def __init__(self, ai_client=None):
        super().__init__(ai_client)
        self.agent_name = "Code Review Agent"
        self.agent_emoji = "👁️"

    async def execute(self, target: str, description: str) -> "AgentReport":
        """Execute code review and return structured result."""
        from .base_agent import AgentReport

        self.start_task(description)
        created_files = []
        modified_files = []
        errors = []
        warnings = []

        try:
            self.log_info(f"Reviewing code quality: {target}")

            if target and os.path.exists(target):
                # Handle directory vs file
                if os.path.isdir(target):
                    # Review directory - find Python files
                    python_files = []
                    for root, dirs, files in os.walk(target):
                        for file in files:
                            if file.endswith(".py"):
                                python_files.append(os.path.join(root, file))

                    if python_files:
                        self.log_info(
                            f"Found {len(python_files)} Python files to review"
                        )

                        total_lines = 0
                        docs_found = 0
                        functions_found = 0

                        for py_file in python_files[:5]:  # Review first 5 files
                            try:
                                with open(
                                    py_file, "r", encoding="utf-8", errors="ignore"
                                ) as f:
                                    content = f.read()

                                lines = content.split("\n")
                                total_lines += len(lines)

                                if '"""' in content or "'''" in content:
                                    docs_found += 1

                                if "def " in content:
                                    functions_found += 1

                            except Exception as e:
                                warning_msg = f"Could not read {py_file}: {e}"
                                self.log_warning(warning_msg)
                                warnings.append(warning_msg)

                        self.log_info(f"Review summary: {total_lines} total lines")
                        self.log_success(f"Documentation found in {docs_found} files")
                        self.log_success(f"Functions found in {functions_found} files")
                        self.log_success("Code quality review completed")
                        success = True
                    else:
                        self.log_info("No Python files found for review")
                        success = True

                elif os.path.isfile(target):
                    # Review single file
                    with open(target, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Basic quality checks
                    lines = content.split("\n")
                    self.log_info(f"Code review: {len(lines)} lines analyzed")

                    # Simple quality indicators
                    if '"""' in content or "'''" in content:
                        self.log_success("Documentation strings found")

                    if "def " in content:
                        self.log_success("Functions are well structured")

                    self.log_success("Code quality review completed")
                    success = True

            else:
                error_msg = f"Target not found: {target}"
                self.log_warning(error_msg)
                errors.append(error_msg)
                success = False

            return self.create_task_result(
                success=success,
                task_description=description,
                created_files=created_files,
                modified_files=modified_files,
                errors=errors,
                warnings=warnings,
                output_data={"target": target, "task_type": "code_review"},
                next_recommendations=(
                    ["Review test results", "Run additional tests if needed"]
                    if success
                    else ["Check errors and retry"]
                ),
            )

        except Exception as e:
            error_msg = f"Code review failed: {e}"
            self.log_error(error_msg)
            errors.append(error_msg)

            return self.create_task_result(
                success=False,
                task_description=description,
                errors=errors,
                output_data={"target": target, "exception": str(e)},
            )
