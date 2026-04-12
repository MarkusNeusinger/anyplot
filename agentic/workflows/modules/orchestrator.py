"""Shared orchestrator utilities for multi-phase workflows."""

import json
import os
import subprocess


# Path to workflow scripts directory (parent of modules/)
WORKFLOWS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_phase(script: str, args: list[str], console, phase_name: str, capture_stdout: bool = False) -> tuple[int, str]:
    """Run a workflow phase script via uv.

    Args:
        script: Script filename (e.g., "plan.py")
        args: CLI arguments for the script
        console: Rich console for output
        phase_name: Display name for the phase
        capture_stdout: If True, capture stdout for piping state between phases

    Returns:
        Tuple of (return_code, stdout_output)
    """
    script_path = os.path.join(WORKFLOWS_DIR, script)
    cmd = ["uv", "run", script_path] + args

    console.print(f"[dim]$ {' '.join(cmd)}[/dim]\n")

    if capture_stdout:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=None,  # Let stderr pass through to console
            text=True,
        )
        return result.returncode, result.stdout
    else:
        result = subprocess.run(cmd)
        return result.returncode, ""


def extract_run_id(stdout: str) -> str | None:
    """Extract run_id from piped JSON state output."""
    try:
        data = json.loads(stdout.strip())
        return data.get("run_id")
    except (json.JSONDecodeError, ValueError):
        return None
