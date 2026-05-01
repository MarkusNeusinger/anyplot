# Application Validation Test Suite

Execute comprehensive validation tests for both frontend and backend components, returning results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the application before they impact users or developers. By running this comprehensive test suite, you can:
- Detect syntax errors, type mismatches, and import failures
- Identify broken tests or security vulnerabilities
- Verify build processes and dependencies
- Ensure the application is in a healthy state

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
  - Your ENTIRE response must be the JSON array. Start with [ and end with ]. No other text.
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- If a test fails, stop processing and return results gathered so far
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
- Some tests may have dependencies (e.g., server must be stopped for port availability)
- Test execution order is important - dependencies should be validated first
- All file paths are relative to the project root
- Always run `pwd` and `cd` before each test to ensure you're operating in the correct directory for the given test

## Codebase Structure

For the full project layout, conventions, and tech stack, see `agentic/docs/project-guide.md`. You usually do not need
to read it for this command — the test commands below are self-contained.

## Test Execution Sequence

### Backend Tests

1. **Code Formatting Check**
   - Preparation Command: None
   - Command: `uv run ruff format --check .`
   - test_name: "code_formatting"
   - test_purpose: "Validates that Python code follows consistent formatting standards"

2. **Backend Code Quality Check**
   - Preparation Command: None
   - Command: `uv run ruff check .`
   - test_name: "backend_linting"
   - test_purpose: "Validates Python code quality, identifies unused imports, style violations, and potential bugs"

3. **Python Syntax Check**
   - Preparation Command: None
   - Command: `uv run python -m py_compile api/**/*.py core/**/*.py`
   - test_name: "python_syntax_check"
   - test_purpose: "Validates Python syntax by compiling source files to bytecode, catching syntax errors like missing colons, invalid indentation, or malformed statements"

4. **All Backend Tests**
   - Preparation Command: None
   - Command: `uv run pytest tests/ -v --tb=short`
   - test_name: "all_backend_tests"
   - test_purpose: "Validates all backend functionality including API endpoints, business logic, and data processing"

### Frontend Tests (if app/ exists)

5. **Frontend Build**
   - Preparation Command: Check if `app/` directory exists
   - Command: `cd app && yarn build`
   - test_name: "frontend_build"
   - test_purpose: "Validates the complete frontend build process including bundling, asset optimization, and production compilation"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output

```json
[
  {
    "test_name": "backend_linting",
    "passed": false,
    "execution_command": "uv run ruff check .",
    "test_purpose": "Validates Python code quality, identifies unused imports, style violations, and potential bugs",
    "error": "api/main.py:15:1: F401 `os` imported but unused"
  },
  {
    "test_name": "code_formatting",
    "passed": true,
    "execution_command": "uv run ruff format --check .",
    "test_purpose": "Validates that Python code follows consistent formatting standards"
  }
]
```
