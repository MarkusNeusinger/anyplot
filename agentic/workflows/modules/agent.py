"""Claude Code agent module for executing prompts programmatically."""

import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel


# Add project root to path for imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import settings directly from the module file to avoid core/__init__.py
# which has dependencies (PIL) not available in uv script environments

_config_path = os.path.join(_project_root, "core", "config.py")
_spec = importlib.util.spec_from_file_location("core_config", _config_path)
_core_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core_config)
settings = _core_config.settings


# Retry codes for Claude Code execution errors
class RetryCode(str, Enum):
    """Codes indicating different types of errors that may be retryable."""

    CLAUDE_CODE_ERROR = "claude_code_error"  # General Claude Code CLI error
    TIMEOUT_ERROR = "timeout_error"  # Command timed out
    EXECUTION_ERROR = "execution_error"  # Error during execution
    ERROR_DURING_EXECUTION = "error_during_execution"  # Agent encountered an error
    NONE = "none"  # No retry needed


class AgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration."""

    prompt: str
    run_id: str
    agent_name: str = "ops"
    model: Literal["small", "medium", "large"] = "large"
    cli: Literal["claude", "copilot", "gemini"] = "claude"
    dangerously_skip_permissions: bool = False
    output_file: str
    working_dir: Optional[str] = None
    timeout: Optional[int] = 1800  # seconds (default: 30 min)


class AgentPromptResponse(BaseModel):
    """Claude Code agent response."""

    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: RetryCode = RetryCode.NONE


class AgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request."""

    agent_name: str
    slash_command: str
    args: List[str]
    run_id: str
    model: Literal["small", "medium", "large"] = "large"
    cli: Literal["claude", "copilot", "gemini"] = "claude"
    working_dir: Optional[str] = None


class ClaudeCodeResultMessage(BaseModel):
    """Claude Code JSONL result message (last line)."""

    type: str
    subtype: str
    is_error: bool
    duration_ms: int
    duration_api_ms: int
    num_turns: int
    result: str
    session_id: str
    total_cost_usd: float


class TestResult(BaseModel):
    """Individual test result from test.md output."""

    test_name: str
    passed: bool
    execution_command: str
    test_purpose: str
    error: Optional[str] = None


class ReviewIssue(BaseModel):
    """Individual review issue from review.md output."""

    review_issue_number: int
    screenshot_path: str
    issue_description: str
    issue_resolution: str
    issue_severity: Literal["skippable", "tech_debt", "blocker"]


class ReviewResult(BaseModel):
    """Review result from review.md output."""

    success: bool
    review_summary: str
    review_issues: List[ReviewIssue] = []
    screenshots: List[str] = []


T = TypeVar("T", bound=BaseModel)


def parse_json(output: str, target_type: Type[T] = None) -> Any:
    """Parse JSON from LLM output, handling markdown code fences and surrounding text.

    Args:
        output: Raw LLM output that may contain JSON wrapped in markdown fences
            or surrounded by explanatory text.
        target_type: Optional Pydantic model class to validate against.

    Returns:
        Parsed JSON (dict/list), or validated Pydantic model if target_type provided.
    """
    cleaned = output.strip()

    # Strategy 1: Try direct parse
    try:
        parsed = json.loads(cleaned)
        if target_type is not None:
            if isinstance(parsed, list):
                return [target_type.model_validate(item) for item in parsed]
            return target_type.model_validate(parsed)
        return parsed
    except json.JSONDecodeError, ValueError:
        pass

    # Strategy 2: Strip markdown code fences
    if "```" in cleaned:
        # Find content between first ``` and last ```
        fence_start = cleaned.index("```")
        first_newline = cleaned.index("\n", fence_start) if "\n" in cleaned[fence_start:] else len(cleaned)
        fence_end = cleaned.rindex("```")
        if fence_end > fence_start:
            inner = cleaned[first_newline + 1 : fence_end].strip()
            try:
                parsed = json.loads(inner)
                if target_type is not None:
                    if isinstance(parsed, list):
                        return [target_type.model_validate(item) for item in parsed]
                    return target_type.model_validate(parsed)
                return parsed
            except json.JSONDecodeError, ValueError:
                pass

    # Strategy 3: Find first JSON array or object in output
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = cleaned.find(start_char)
        if start_idx == -1:
            continue
        # Find matching closing bracket by scanning from the end
        end_idx = cleaned.rfind(end_char)
        if end_idx <= start_idx:
            continue
        candidate = cleaned[start_idx : end_idx + 1]
        try:
            parsed = json.loads(candidate)
            if target_type is not None:
                if isinstance(parsed, list):
                    return [target_type.model_validate(item) for item in parsed]
                return target_type.model_validate(parsed)
            return parsed
        except json.JSONDecodeError, ValueError:
            continue

    raise json.JSONDecodeError("No valid JSON found in output", output, 0)


def get_safe_subprocess_env() -> Dict[str, str]:
    """Get filtered environment variables safe for subprocess execution.

    Returns platform-appropriate environment variables for subprocess execution.
    On Windows, maps Windows variables (USERPROFILE, USERNAME, COMSPEC) to
    their Unix equivalents (HOME, USER, SHELL) for compatibility.

    Returns:
        Dictionary containing only required environment variables
    """
    safe_env_vars = {
        # Anthropic Configuration (required)
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        # Claude Code Configuration
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": os.getenv("CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "true"),
        # Universal system variables
        "PATH": os.getenv("PATH"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PYTHONUNBUFFERED": "1",
        "PWD": os.getcwd(),
    }

    # Platform-specific environment variables
    if platform.system() == "Windows":
        # Windows: Map Windows variables to Unix names for CLI compatibility
        safe_env_vars["HOME"] = os.getenv("USERPROFILE")
        safe_env_vars["USER"] = os.getenv("USERNAME")
        safe_env_vars["SHELL"] = os.getenv("COMSPEC")
        # Keep Windows-specific ones for native compatibility
        safe_env_vars["USERPROFILE"] = os.getenv("USERPROFILE")
        safe_env_vars["USERNAME"] = os.getenv("USERNAME")
        safe_env_vars["COMSPEC"] = os.getenv("COMSPEC")
    else:
        # Unix/Linux/macOS
        safe_env_vars["HOME"] = os.getenv("HOME")
        safe_env_vars["USER"] = os.getenv("USER")
        safe_env_vars["SHELL"] = os.getenv("SHELL")
        safe_env_vars["TERM"] = os.getenv("TERM")
        safe_env_vars["LANG"] = os.getenv("LANG")
        safe_env_vars["LC_ALL"] = os.getenv("LC_ALL")

    # Filter out None values
    return {k: v for k, v in safe_env_vars.items() if v is not None}


# Load environment variables
load_dotenv()

# Get Claude Code CLI path from environment
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

# Output file name constants
OUTPUT_JSONL = "cli_raw_output.jsonl"
OUTPUT_JSON = "cli_raw_output.json"
FINAL_OBJECT_JSON = "cli_final_object.json"
SUMMARY_JSON = "cli_summary_output.json"


def generate_short_id() -> str:
    """Generate a short 8-character UUID for tracking."""
    return str(uuid.uuid4())[:8]


def get_cli_path(cli: str) -> str:
    """Get CLI executable path based on selected CLI tool.

    Args:
        cli: The CLI tool name ("claude", "copilot", or "gemini")

    Returns:
        The executable path from environment variable or default
    """
    env_vars = {
        "claude": ("CLAUDE_CODE_PATH", "claude"),
        "copilot": ("COPILOT_CLI_PATH", "copilot"),
        "gemini": ("GEMINI_CLI_PATH", "gemini"),
    }
    env_var, default = env_vars.get(cli, ("CLAUDE_CODE_PATH", "claude"))
    return os.getenv(env_var, default)


def build_cli_command(
    cli: str,
    cli_path: str,
    prompt: str,
    model: str,
    dangerously_skip_permissions: bool,
    mcp_config_path: Optional[str] = None,
) -> List[str]:
    """Build CLI-specific command arguments.

    Args:
        cli: The CLI tool name ("claude", "copilot", or "gemini")
        cli_path: Path to the CLI executable
        prompt: The prompt to execute
        model: Model name (only used for claude)
        dangerously_skip_permissions: Whether to skip permission checks
        mcp_config_path: Optional path to MCP config file

    Returns:
        List of command arguments
    """
    if cli == "claude":
        # Claude: -p <prompt>, --model, --output-format stream-json, --verbose
        cmd = [cli_path, "-p", prompt]
        cmd.extend(["--model", model])
        cmd.extend(["--output-format", "stream-json"])
        cmd.append("--verbose")
        if mcp_config_path:
            cmd.extend(["--mcp-config", mcp_config_path])
        if dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")

    elif cli == "copilot":
        # Copilot: -p <prompt>, --allow-all (for skip permissions)
        # No --model (uses default), no --verbose, no --output-format
        cmd = [cli_path, "-p", prompt]
        if mcp_config_path:
            cmd.extend(["--additional-mcp-config", mcp_config_path])
        if dangerously_skip_permissions:
            cmd.append("--allow-all")

    elif cli == "gemini":
        # Gemini: -p <prompt>
        # No --model, no skip permissions, no --verbose, no --output-format
        cmd = [cli_path, "-p", prompt]
        # Gemini has different MCP config handling - skip for now

    else:
        # Fallback to claude-style
        cmd = [cli_path, "-p", prompt]

    return cmd


def truncate_output(output: str, max_length: int = 500, suffix: str = "... (truncated)") -> str:
    """Truncate output to a reasonable length for display.

    Special handling for JSONL data - if the output appears to be JSONL,
    try to extract just the meaningful part.

    Args:
        output: The output string to truncate
        max_length: Maximum length before truncation (default: 500)
        suffix: Suffix to add when truncated (default: "... (truncated)")

    Returns:
        Truncated string if needed, original if shorter than max_length
    """
    # Check if this looks like JSONL data
    if output.startswith('{"type":') and '\n{"type":' in output:
        # This is likely JSONL output - try to extract the last meaningful message
        lines = output.strip().split("\n")
        for line in reversed(lines):
            try:
                data = json.loads(line)
                # Look for result message
                if data.get("type") == "result":
                    result = data.get("result", "")
                    if result:
                        return truncate_output(result, max_length, suffix)
                # Look for assistant message
                elif data.get("type") == "assistant" and data.get("message"):
                    content = data["message"].get("content", [])
                    if isinstance(content, list) and content:
                        text = content[0].get("text", "")
                        if text:
                            return truncate_output(text, max_length, suffix)
            except Exception:
                pass  # Malformed JSONL line, skip and try next
        # If we couldn't extract anything meaningful, just show that it's JSONL
        return f"[JSONL output with {len(lines)} messages]{suffix}"

    # Regular truncation logic
    if len(output) <= max_length:
        return output

    # Try to find a good break point (newline or space)
    truncate_at = max_length - len(suffix)

    # Look for newline near the truncation point
    newline_pos = output.rfind("\n", truncate_at - 50, truncate_at)
    if newline_pos > 0:
        return output[:newline_pos] + suffix

    # Look for space near the truncation point
    space_pos = output.rfind(" ", truncate_at - 20, truncate_at)
    if space_pos > 0:
        return output[:space_pos] + suffix

    # Just truncate at the limit
    return output[:truncate_at] + suffix


def check_cli_installed(cli: str = "claude") -> Optional[str]:
    """Check if CLI tool is installed. Return error message if not.

    Args:
        cli: The CLI tool name ("claude", "copilot", or "gemini")

    Returns:
        Error message if not installed, None if installed
    """
    cli_path = get_cli_path(cli)
    try:
        result = subprocess.run([cli_path, "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: CLI tool '{cli}' is not installed. Expected at: {cli_path}"
    except FileNotFoundError:
        return f"Error: CLI tool '{cli}' is not installed. Expected at: {cli_path}"
    return None


def parse_jsonl_output(output_file: str) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file and return all messages and the result message.

    Returns:
        Tuple of (all_messages, result_message) where result_message is None if not found
    """
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            # Read all lines and parse each as JSON
            messages = [json.loads(line) for line in f if line.strip()]

            # Find the result message (should be the last one)
            result_message = None
            for message in reversed(messages):
                if message.get("type") == "result":
                    result_message = message
                    break

            return messages, result_message
    except Exception:
        return [], None


def convert_jsonl_to_json(jsonl_file: str) -> str:
    """Convert JSONL file to JSON array file.

    Creates a cc_raw_output.json file in the same directory as the JSONL file,
    containing all messages as a JSON array.

    Returns:
        Path to the created JSON file
    """
    # Create JSON filename in the same directory
    output_dir = os.path.dirname(jsonl_file)
    json_file = os.path.join(output_dir, OUTPUT_JSON)

    # Parse the JSONL file
    messages, _ = parse_jsonl_output(jsonl_file)

    # Write as JSON array
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

    return json_file


def save_last_entry_as_raw_result(json_file: str) -> Optional[str]:
    """Save the last entry from a JSON array file as cc_final_object.json.

    Args:
        json_file: Path to the JSON array file

    Returns:
        Path to the created cc_final_object.json file, or None if error
    """
    try:
        # Read the JSON array
        with open(json_file, "r", encoding="utf-8") as f:
            messages = json.load(f)

        if not messages:
            return None

        # Get the last entry
        last_entry = messages[-1]

        # Create cc_final_object.json in the same directory
        output_dir = os.path.dirname(json_file)
        final_object_file = os.path.join(output_dir, FINAL_OBJECT_JSON)

        # Write the last entry
        with open(final_object_file, "w", encoding="utf-8") as f:
            json.dump(last_entry, f, indent=2, ensure_ascii=False)

        return final_object_file
    except Exception:
        # Silently fail - this is a nice-to-have feature
        return None


def get_claude_env() -> Dict[str, str]:
    """Get only the required environment variables for Claude Code execution.

    This is a wrapper around get_safe_subprocess_env() for
    backward compatibility. New code should use get_safe_subprocess_env() directly.

    Returns a dictionary containing only the necessary environment variables
    based on .env.sample configuration.
    """
    # Use the function defined above
    return get_safe_subprocess_env()


def save_prompt(prompt: str, run_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the appropriate logging directory."""
    # Extract slash command from prompt
    match = re.match(r"^(/\w+)", prompt)
    if not match:
        return

    slash_command = match.group(1)
    # Remove leading slash for filename
    command_name = slash_command[1:]

    # Create directory structure at project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompt_dir = os.path.join(project_root, "agentic", "runs", run_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)

    # Save prompt to file
    prompt_file = os.path.join(prompt_dir, f"{command_name}.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)


def prompt_claude_code_with_retry(
    request: AgentPromptRequest, max_retries: int = 3, retry_delays: List[int] = None
) -> AgentPromptResponse:
    """Execute Claude Code with retry logic for certain error types.

    Args:
        request: The prompt request configuration
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delays: List of delays in seconds between retries (default: [1, 3, 5])

    Returns:
        AgentPromptResponse with output and retry code
    """
    if retry_delays is None:
        retry_delays = [1, 3, 5]

    # Ensure we have enough delays for max_retries
    while len(retry_delays) < max_retries:
        retry_delays.append(retry_delays[-1] + 2)  # Add incrementing delays

    last_response = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if attempt > 0:
            # This is a retry
            delay = retry_delays[attempt - 1]
            time.sleep(delay)

        response = prompt_claude_code(request)
        last_response = response

        # Check if we should retry based on the retry code
        if response.success or response.retry_code == RetryCode.NONE:
            # Success or non-retryable error
            return response

        # Check if this is a retryable error
        if response.retry_code in [
            RetryCode.CLAUDE_CODE_ERROR,
            RetryCode.TIMEOUT_ERROR,
            RetryCode.EXECUTION_ERROR,
            RetryCode.ERROR_DURING_EXECUTION,
        ]:
            if attempt < max_retries:
                continue
            else:
                return response

    # Should not reach here, but return last response just in case
    return last_response


def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute Claude Code with the given prompt configuration."""

    # Get CLI path based on selected CLI tool
    cli_path = get_cli_path(request.cli)

    # Check if CLI tool is installed
    error_msg = check_cli_installed(request.cli)
    if error_msg:
        return AgentPromptResponse(
            output=error_msg,
            success=False,
            session_id=None,
            retry_code=RetryCode.NONE,  # Installation error is not retryable
        )

    # Save prompt before execution
    save_prompt(request.prompt, request.run_id, request.agent_name)

    # Create output directory if needed
    output_dir = os.path.dirname(request.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Check for MCP config in working directory
    mcp_config_path = None
    if request.working_dir:
        potential_mcp_path = os.path.join(request.working_dir, ".mcp.json")
        if os.path.exists(potential_mcp_path):
            mcp_config_path = potential_mcp_path

    # Resolve model tier to actual model name for the CLI
    actual_model = settings.resolve_model(request.cli, request.model)

    # Build CLI-specific command
    cmd = build_cli_command(
        cli=request.cli,
        cli_path=cli_path,
        prompt=request.prompt,
        model=actual_model,
        dangerously_skip_permissions=request.dangerously_skip_permissions,
        mcp_config_path=mcp_config_path,
    )

    # Set up environment
    # - Windows: Use full environment for all CLIs (Claude Code needs APPDATA, TEMP, etc.)
    # - Unix/Linux: Use filtered environment for Claude, full for other CLIs
    if platform.system() == "Windows":
        env = dict(os.environ)
    else:
        env = get_claude_env() if request.cli == "claude" else dict(os.environ)

    try:
        # Open output file for streaming
        with open(request.output_file, "w", encoding="utf-8") as output_f:
            # Execute Claude Code and stream output to file
            result = subprocess.run(
                cmd,
                stdout=output_f,  # Stream directly to file
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=request.working_dir,  # Use working_dir if provided
                timeout=request.timeout,
            )

        if result.returncode == 0:
            # For non-claude CLIs, output is plain text, not JSONL
            if request.cli != "claude":
                # Read plain text output
                with open(request.output_file, "r", encoding="utf-8") as f:
                    output_text = f.read().strip()
                return AgentPromptResponse(output=output_text, success=True, session_id=None, retry_code=RetryCode.NONE)

            # Parse the JSONL file (claude only)
            messages, result_message = parse_jsonl_output(request.output_file)

            # Convert JSONL to JSON array file
            json_file = convert_jsonl_to_json(request.output_file)

            # Save the last entry as raw_result.json
            save_last_entry_as_raw_result(json_file)

            if result_message:
                # Extract session_id from result message
                session_id = result_message.get("session_id")

                # Check if there was an error in the result
                is_error = result_message.get("is_error", False)
                subtype = result_message.get("subtype", "")

                # Handle error_during_execution case where there's no result field
                if subtype == "error_during_execution":
                    error_msg = "Error during execution: Agent encountered an error and did not return a result"
                    return AgentPromptResponse(
                        output=error_msg,
                        success=False,
                        session_id=session_id,
                        retry_code=RetryCode.ERROR_DURING_EXECUTION,
                    )

                result_text = result_message.get("result", "")

                # For error cases, truncate the output to prevent JSONL blobs
                if is_error and len(result_text) > 1000:
                    result_text = truncate_output(result_text, max_length=800)

                return AgentPromptResponse(
                    output=result_text,
                    success=not is_error,
                    session_id=session_id,
                    retry_code=RetryCode.NONE,  # No retry needed for successful or non-retryable errors
                )
            else:
                # No result message found, try to extract meaningful error
                error_msg = "No result message found in CLI output"

                # Try to get the last few lines of output for context
                try:
                    with open(request.output_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            # Get last 5 lines or less
                            last_lines = lines[-5:] if len(lines) > 5 else lines
                            # Try to parse each as JSON to find any error messages
                            for line in reversed(last_lines):
                                try:
                                    data = json.loads(line.strip())
                                    if data.get("type") == "assistant" and data.get("message"):
                                        # Extract text from assistant message
                                        content = data["message"].get("content", [])
                                        if isinstance(content, list) and content:
                                            text = content[0].get("text", "")
                                            if text:
                                                error_msg = f"CLI output: {text[:500]}"  # Truncate
                                                break
                                except Exception:
                                    pass  # Malformed JSONL line, skip
                except Exception:
                    pass  # Output file unreadable, fall through to default error

                return AgentPromptResponse(
                    output=truncate_output(error_msg, max_length=800),
                    success=False,
                    session_id=None,
                    retry_code=RetryCode.NONE,
                )
        else:
            # Error occurred - stderr is captured, stdout went to file
            stderr_msg = result.stderr.strip() if result.stderr else ""

            # For non-claude CLIs, just read plain text output
            if request.cli != "claude":
                stdout_msg = ""
                try:
                    if os.path.exists(request.output_file):
                        with open(request.output_file, "r", encoding="utf-8") as f:
                            stdout_msg = f.read().strip()[:500]  # Truncate
                except Exception:
                    pass  # Output file unreadable, use stderr only

                if stdout_msg and not stderr_msg:
                    error_msg = f"CLI error: {stdout_msg}"
                elif stderr_msg and not stdout_msg:
                    error_msg = f"CLI error: {stderr_msg}"
                elif stdout_msg and stderr_msg:
                    error_msg = f"CLI error: {stderr_msg}\nStdout: {stdout_msg}"
                else:
                    error_msg = f"CLI error: Command failed with exit code {result.returncode}"
            else:
                # Claude-specific JSONL parsing
                stdout_msg = ""
                error_from_jsonl = None
                try:
                    if os.path.exists(request.output_file):
                        # Parse JSONL to find error message
                        messages, result_message = parse_jsonl_output(request.output_file)

                        if result_message and result_message.get("is_error"):
                            # Found error in result message
                            error_from_jsonl = result_message.get("result", "Unknown error")
                        elif messages:
                            # Look for error in last few messages
                            for msg in reversed(messages[-5:]):
                                if msg.get("type") == "assistant" and msg.get("message", {}).get("content"):
                                    content = msg["message"]["content"]
                                    if isinstance(content, list) and content:
                                        text = content[0].get("text", "")
                                        if text and ("error" in text.lower() or "failed" in text.lower()):
                                            error_from_jsonl = text[:500]  # Truncate
                                            break

                        # If no structured error found, get last line only
                        if not error_from_jsonl:
                            with open(request.output_file, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                                if lines:
                                    # Just get the last line instead of entire file
                                    stdout_msg = lines[-1].strip()[:200]  # Truncate to 200 chars
                except Exception:
                    pass  # JSONL parsing failed, fall through to stderr-based error

                if error_from_jsonl:
                    error_msg = f"CLI error: {error_from_jsonl}"
                elif stdout_msg and not stderr_msg:
                    error_msg = f"CLI error: {stdout_msg}"
                elif stderr_msg and not stdout_msg:
                    error_msg = f"CLI error: {stderr_msg}"
                elif stdout_msg and stderr_msg:
                    error_msg = f"CLI error: {stderr_msg}\nStdout: {stdout_msg}"
                else:
                    error_msg = f"CLI error: Command failed with exit code {result.returncode}"

            # Always truncate error messages to prevent huge outputs
            return AgentPromptResponse(
                output=truncate_output(error_msg, max_length=800),
                success=False,
                session_id=None,
                retry_code=RetryCode.CLAUDE_CODE_ERROR,
            )

    except subprocess.TimeoutExpired:
        error_msg = "Error: CLI command timed out after 5 minutes"
        return AgentPromptResponse(output=error_msg, success=False, session_id=None, retry_code=RetryCode.TIMEOUT_ERROR)
    except Exception as e:
        error_msg = f"Error executing CLI: {e}"
        return AgentPromptResponse(
            output=error_msg, success=False, session_id=None, retry_code=RetryCode.EXECUTION_ERROR
        )


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments.

    Example:
        request = AgentTemplateRequest(
            agent_name="planner",
            slash_command="/implement",
            args=["plan.md"],
            run_id="abc12345",
            model="medium"  # Model tier (small/medium/large)
        )
        response = execute_template(request)
    """

    # Construct prompt from slash command and args
    prompt = f"{request.slash_command} {' '.join(request.args)}"

    # Create output directory with run_id at project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "agentic", "runs", request.run_id, request.agent_name)
    os.makedirs(output_dir, exist_ok=True)

    # Build output file path
    output_file = os.path.join(output_dir, OUTPUT_JSONL)

    # Create prompt request with specific parameters
    prompt_request = AgentPromptRequest(
        prompt=prompt,
        run_id=request.run_id,
        agent_name=request.agent_name,
        model=request.model,
        cli=request.cli,
        dangerously_skip_permissions=True,
        output_file=output_file,
        working_dir=request.working_dir,  # Pass through working_dir
    )

    # Execute with retry logic and return response (prompt_claude_code now handles all parsing)
    return prompt_claude_code_with_retry(prompt_request)
