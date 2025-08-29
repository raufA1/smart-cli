"""Code Modifier Agent - Handles code modification and improvement."""

import os
import re

from .base_agent import BaseAgent


class ModifierAgent(BaseAgent):
    """Code Modifier Agent for code modification and enhancement."""

    def __init__(self, ai_client=None, config_manager=None):
        super().__init__(ai_client, config_manager)
        self.agent_name = "Code Modifier Agent"
        self.agent_emoji = "🔧"

    async def execute(self, target: str, description: str) -> "AgentReport":
        """Execute code modification and return structured result."""
        from .base_agent import AgentReport

        self.start_task(description)
        created_files = []
        modified_files = []
        errors = []
        warnings = []

        try:
            if not self.ai_client:
                warning_msg = "No AI client available for code generation"
                self.log_warning(warning_msg)
                warnings.append(warning_msg)

                # Still try to analyze the task for recommendations
                recommendations = [
                    "Configure AI client for full functionality",
                    "Manual code review recommended",
                    f"Check target: {target}",
                ]

                return self.create_task_result(
                    success=True,  # Partial success - task acknowledged
                    task_description=description,
                    warnings=warnings,
                    next_recommendations=recommendations,
                )

            # Enhanced: Check if this is a fix/debug task
            if any(
                word in description.lower()
                for word in ["fix", "debug", "correct", "repair", "düzəlt"]
            ):
                success, files, task_errors = await self._fix_code_errors(
                    target, description
                )
                if files:
                    created_files.extend(files)
                if task_errors:
                    errors.extend(task_errors)
            else:
                success, files, task_errors = await self._generate_new_code(
                    target, description
                )
                if files:
                    created_files.extend(files)
                if task_errors:
                    errors.extend(task_errors)

            # Log the result
            if success:
                self.log_success(f"Code modification completed. Files: {created_files}")
            else:
                self.log_error(f"Code modification failed. Errors: {errors}")

            return self.create_task_result(
                success=success,
                task_description=description,
                created_files=created_files,
                modified_files=modified_files,
                errors=errors,
                warnings=warnings,
                output_data={"target": target, "task_type": "code_modification"},
                next_recommendations=(
                    ["Test generated code", "Review for quality"]
                    if success
                    else ["Check errors and retry"]
                ),
            )

        except Exception as e:
            error_msg = f"Code generation failed: {e}"
            self.log_error(error_msg)
            errors.append(error_msg)

            return self.create_task_result(
                success=False,
                task_description=description,
                errors=errors,
                output_data={"target": target, "exception": str(e)},
            )

    async def _fix_code_errors(
        self, target: str, description: str
    ) -> tuple[bool, list, list]:
        """Fix existing code with specific errors."""
        # Extract specific file from description
        import re

        file_match = re.search(r"\b(\w+\.py)\b", description)
        if file_match:
            target_file = file_match.group(1)
            if os.path.exists(target_file):
                target = target_file

        if not os.path.exists(target) or os.path.isdir(target):
            error_msg = f"Cannot fix - target file not found: {target}"
            self.log_warning(error_msg)
            return False, [], [error_msg]

        # Read the broken code
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            broken_code = f.read()

        # Create enhanced fix prompt
        fix_prompt = f"""
TASK: Fix the following Python code that has syntax and logic errors.

BROKEN CODE:
```python
{broken_code}
```

REQUIREMENTS:
1. Fix ALL syntax errors (missing colons, parentheses, indentation)
2. Fix logic errors (type mismatches, undefined variables)
3. Maintain the original functionality intent
4. Add proper error handling where needed
5. Make the code production-ready

IMPORTANT: Only return the COMPLETE FIXED CODE, nothing else.
Format as clean Python code without markdown blocks.
"""

        self.log_info(f"Fixing code errors in {target}")
        response = await self.ai_client.generate_response(fix_prompt)

        if response and response.content:
            # Clean the response - remove markdown if present
            fixed_code = response.content.strip()
            if fixed_code.startswith("```"):
                lines = fixed_code.split("\n")
                fixed_code = "\n".join(lines[1:-1])  # Remove first and last lines

            # Create fixed version
            fixed_filename = target.replace(".py", "_fixed.py")
            with open(fixed_filename, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            self.log_success(f"Fixed code saved as: {fixed_filename}")

            created_files = [fixed_filename]
            modified_files = []

            # Also update the original if it's clearly broken
            if "syntax" in description.lower():
                with open(target, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                self.log_success(f"Updated original file: {target}")
                modified_files.append(target)

            return True, created_files + modified_files, []
        else:
            error_msg = "No response from AI for code fixing"
            self.log_warning(error_msg)
            return False, [], [error_msg]

    async def _generate_new_code(
        self, target: str, description: str
    ) -> tuple[bool, list, list]:
        """Generate new code - enhanced for complex multi-file projects."""

        # First check if Architect Agent has created a project structure
        architecture_files = self._find_architecture_files()
        
        # Check if this is a complex multi-component project
        if self._is_complex_project(description) or architecture_files:
            if architecture_files:
                self.log_info("Found architecture files - using structured approach")
                return await self._generate_from_architecture(description, architecture_files)
            else:
                return await self._generate_multi_file_project(description)
        else:
            return await self._generate_single_file(description, target)

    def _is_complex_project(self, description: str) -> bool:
        """Determine if request requires multi-file project structure."""
        complexity_indicators = [
            "system",
            "scraper",
            "web scraper",
            "complete",
            "with",
            "database",
            "proxy rotation",
            "user agent",
            "configuration",
            "command line",
            "multiple",
            "components",
            "modules",
            "CLI",
            "export",
            "storage",
        ]

        desc_lower = description.lower()
        indicator_count = sum(
            1 for indicator in complexity_indicators if indicator in desc_lower
        )

        # If 3+ complexity indicators, treat as multi-file project
        return indicator_count >= 3

    async def _generate_multi_file_project(
        self, description: str
    ) -> tuple[bool, list, list]:
        """Generate complete multi-file project structure."""

        # Enhanced prompt for complex projects with proper directory structure
        project_prompt = f"""
Create a complete Python project based on: "{description}"

Generate a professional, modular project structure with PROPER DIRECTORY ORGANIZATION.

IMPORTANT: Always use a well-organized directory structure like this:

PROJECT STRUCTURE:
- src/ (source code)
- tests/ (test files)
- requirements.txt (dependencies)
- README.md (project documentation)
- .env.example (environment template)

Provide multiple files in this EXACT format with proper paths:

FILE: src/main.py
```python
# Main entry point
```

FILE: src/scraper.py
```python
# Scraping functionality
```

FILE: src/config.py
```python
# Configuration management
```

FILE: tests/test_scraper.py
```python
# Unit tests
```

FILE: requirements.txt
```
# Dependencies
```

FILE: README.md
```markdown
# Project documentation
```

PROJECT REQUIREMENTS:
1. Create src/ directory for all source code
2. Create tests/ directory for all test files  
3. Main entry point at src/main.py
4. Configuration files in src/
5. Requirements.txt in root
6. README.md with setup instructions
7. Professional structure like real projects

For a web scraper system, use this structure:
- src/main.py (CLI entry point)
- src/scraper.py (core scraping logic)
- src/database.py (database operations)
- src/config.py (configuration)
- src/utils.py (utilities)
- tests/test_scraper.py (tests)
- requirements.txt (dependencies)
- README.md (documentation)

CRITICAL: Always use proper directory structure with src/ and tests/ folders!
"""

        self.log_info("Generating multi-file project with proper structure using AI...")
        response = await self.ai_client.generate_response(project_prompt)

        if response and response.content:
            return await self._parse_multi_file_response(response.content)
        else:
            error_msg = "No response from AI for multi-file project"
            self.log_warning(error_msg)
            return False, [], [error_msg]

    async def _parse_multi_file_response(self, content: str) -> tuple[bool, list, list]:
        """Parse AI response containing multiple files."""
        created_files = []
        errors = []

        # Split response into individual files
        file_blocks = content.split("FILE: ")

        for block in file_blocks[1:]:  # Skip empty first element
            try:
                # Extract filename and code
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

                if code_start == -1:
                    # No code block found, treat everything after filename as content
                    code_content = "\n".join(lines[1:])
                else:
                    code_content = "\n".join(lines[code_start:code_end])

                if code_content.strip():
                    # Create directory if needed
                    directory = os.path.dirname(filename)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                        self.log_info(f"Created directory: {directory}")

                    # Write file
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(code_content.strip())

                    created_files.append(filename)
                    self.log_success(f"Generated project file: {filename}")

            except Exception as e:
                error_msg = f"Failed to create file from block: {str(e)}"
                self.log_warning(error_msg)
                errors.append(error_msg)

        success = len(created_files) > 0
        return success, created_files, errors

    async def _generate_single_file(
        self, description: str, target: str
    ) -> tuple[bool, list, list]:
        """Generate single file (original functionality)."""
        code_type = self._determine_code_type(description, target)

        # Generate code using AI
        prompt = f"""
Based on the description: "{description}"
Target: "{target}"
Code Type: {code_type}

Please generate complete, working {code_type} code.

Requirements:
1. Generate professional, production-ready code
2. Include proper error handling and logging  
3. Use best practices and clear documentation
4. Make the code modular and maintainable

Generate complete file content that can be saved directly to a file.
Format your response as:

FILENAME: filename.py
CODE:
```python
# your code here
```

Only provide the code block, no explanations outside of the code.
"""

        self.log_info(f"Generating {code_type} code using AI...")
        response = await self.ai_client.generate_response(prompt)

        if response and response.content:
            # Extract filename and code from AI response
            files_created = []
            filename = None
            code_content = None

            # Try to parse FILENAME: and CODE: format
            lines = response.content.split("\n")
            current_section = None
            code_lines = []

            for line in lines:
                if line.startswith("FILENAME:"):
                    filename = line.replace("FILENAME:", "").strip()
                elif line.startswith("CODE:"):
                    current_section = "code"
                    code_lines = []
                elif current_section == "code":
                    if line.startswith("```"):
                        if code_lines:  # End of code block
                            code_content = "\n".join(code_lines)
                            break
                        continue  # Skip opening ```
                    else:
                        code_lines.append(line)

            # Fallback: extract any code block
            if not code_content:
                import re

                code_blocks = re.findall(
                    r"```(?:python)?\s*(.*?)```", response.content, re.DOTALL
                )
                if code_blocks:
                    code_content = code_blocks[0].strip()

            # Determine filename if not extracted
            if not filename:
                if "calculator" in description.lower():
                    filename = "calculator.py"
                elif "main" in description.lower() or target == ".":
                    filename = "main.py"
                else:
                    # Extract filename from description
                    words = description.lower().split()
                    if any(word.endswith("py") for word in words):
                        filename = next(word for word in words if word.endswith("py"))
                    else:
                        filename = (
                            target
                            if target.endswith(".py")
                            else f"{target.replace(' ', '_')}.py"
                        )

                    # Ensure .py extension
                    if not filename.endswith(".py"):
                        filename += ".py"

            if code_content:
                # Ensure directory exists
                import os

                directory = os.path.dirname(filename)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    self.log_info(f"Created directory: {directory}")

                # Write to file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(code_content)

                files_created.append(filename)
                self.log_success(f"Generated code file: {filename}")
                return True, files_created, []
            else:
                error_msg = "No code content extracted from AI response"
                self.log_warning(error_msg)
                return False, [], [error_msg]
        else:
            error_msg = "No response from AI"
            self.log_warning(error_msg)
            return False, [], [error_msg]

    def _find_architecture_files(self) -> list:
        """Find architecture files created by Architect Agent."""
        import glob
        
        architecture_files = []
        
        # Look for architecture overview files
        architecture_patterns = [
            "architecture_overview_*.md",
            "technical_specifications_*.md"
        ]
        
        for pattern in architecture_patterns:
            files = glob.glob(pattern)
            architecture_files.extend(files)
        
        return architecture_files
    
    async def _generate_from_architecture(
        self, description: str, architecture_files: list
    ) -> tuple[bool, list, list]:
        """Generate code based on existing architecture files."""
        
        self.log_info("Reading architecture specifications...")
        
        # Read architecture content
        architecture_content = ""
        for arch_file in architecture_files:
            try:
                with open(arch_file, 'r', encoding='utf-8', errors='ignore') as f:
                    architecture_content += f"\n\n=== {arch_file} ===\n"
                    architecture_content += f.read()
            except Exception as e:
                self.log_warning(f"Could not read {arch_file}: {e}")
        
        # Enhanced prompt using architecture specifications
        structured_prompt = f"""
Create a complete Python project based on:
DESCRIPTION: "{description}"

EXISTING ARCHITECTURE SPECIFICATIONS:
{architecture_content}

IMPORTANT: Follow the architecture specifications and create a proper project structure:

Use this EXACT format with proper directory structure:

FILE: src/main.py
```python
# Main entry point following architecture
```

FILE: src/scraper.py  
```python
# Core scraping logic as specified
```

[Continue with all files as specified in architecture...]

PROJECT REQUIREMENTS:
1. Follow the architecture specifications exactly
2. Create proper src/ and tests/ directory structure  
3. Implement all components mentioned in architecture
4. Use the technology stack recommended in architecture
5. Follow the design patterns specified
6. Include proper error handling and logging
7. Create comprehensive tests

CRITICAL: Use the architecture documents to determine:
- Exact file structure and names
- Component responsibilities  
- Technology choices
- Design patterns to implement

Generate ALL files needed for a complete working system following the architecture!
"""

        self.log_info("Generating structured project from architecture specs...")
        response = await self.ai_client.generate_response(structured_prompt)

        if response and response.content:
            return await self._parse_multi_file_response(response.content)
        else:
            error_msg = "No response from AI for architecture-based generation"
            self.log_warning(error_msg)
            return False, [], [error_msg]

    def _determine_code_type(self, description: str, target: str) -> str:
        """Determine what type of code to generate based on description."""
        desc_lower = description.lower()

        if "calculator" in desc_lower:
            return "calculator application"
        elif "api" in desc_lower or "endpoint" in desc_lower:
            return "API service"
        elif "web" in desc_lower or "html" in desc_lower:
            return "web application"
        elif "test" in desc_lower:
            return "test suite"
        elif "database" in desc_lower or "db" in desc_lower:
            return "database module"
        elif "cli" in desc_lower or "command" in desc_lower:
            return "CLI application"
        elif "bot" in desc_lower:
            return "bot application"
        elif "scraper" in desc_lower or "crawler" in desc_lower:
            return "web scraper"
        else:
            return "Python application"
