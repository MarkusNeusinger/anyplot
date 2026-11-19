"""The tracked source files of the agents package, for tests that read every module.

A tree walk (`Path.rglob`) would enter `agents/evals/.cases/`, the git-ignored directory of the promoted feedback
cases, which holds visitors' data, and list its entries; `git ls-files` names the tracked files alone.
"""

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def tracked_python_files(top: str = "agents") -> list[Path]:
    """Every tracked `.py` file under `top`, relative to the repository root, as absolute paths."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{top}/*.py"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout
    files = [REPO_ROOT / name for name in listed.decode("utf-8").split("\0") if name]
    assert files, f"git ls-files named no Python file under {top}/"
    return files
