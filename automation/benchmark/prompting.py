"""Prompt assembly and response parsing for benchmark generation.

Every model gets exactly the same context the Claude pipeline reads for a
real implementation — base generation rules, the Imprint style guide, the
library-specific rules, and the spec — so quality scores stay comparable
across models. Unlike the agentic pipeline, benchmark generation is
single-shot: the model must answer with one self-contained code block.
"""

from __future__ import annotations

import re
from pathlib import Path


# The single-shot contract replaces the agentic workflow steps (run, self-check,
# commit) that impl-generate-claude.md drives interactively.
_OUTPUT_CONTRACT = """
## Output contract (benchmark mode — read carefully)

You are running in single-shot benchmark mode. There is no shell and no
second turn: your entire answer must be ONE fenced code block containing a
complete, self-contained {library} implementation in Python. The script will
be executed for you, once per theme, in a working directory it may write to.

Hard requirements:

1. Answer with exactly one ```python code block and nothing else — no prose
   before or after, no second block.
2. The script reads the theme from the environment:
   `theme = os.getenv("ANYPLOT_THEME", "light")` and renders that theme.
3. The script saves its output as `plot-{{theme}}.png` (i.e. `plot-light.png`
   or `plot-dark.png`) in the current working directory.
4. The saved PNG must be exactly 3200x1800 px (landscape) or 2400x2400 px
   (square) — follow the "Canvas" rules in the library section below.
5. Only use {library}, the Python standard library, and numpy / pandas /
   scipy / scikit-learn / statsmodels. No network access; do not read any
   local files — the PNG you save is the only file system interaction.
6. Keep the KISS structure: imports -> data -> plot -> save.
"""

_REPAIR_SECTION = """
## Previous attempt failed

Your previous implementation (below) failed to render. Fix the error and
answer again with ONE complete ```python code block following the same
output contract.

### Previous code

```python
{previous_code}
```

### Error output

```
{error_text}
```
"""


def build_generation_prompt(repo_root: Path, spec_id: str, library: str) -> tuple[str, str]:
    """Return ``(system, user)`` prompts for one (spec, library) pair.

    Raises ``FileNotFoundError`` if the spec or any prompt file is missing.
    """
    base_rules = _read(repo_root / "prompts" / "plot-generator.md")
    style_guide = _read(repo_root / "prompts" / "default-style-guide.md")
    library_rules = _read(repo_root / "prompts" / "library" / f"{library}.md")
    specification = _read(repo_root / "plots" / spec_id / "specification.md")

    system = (
        "You are an expert data-visualization engineer. You write clean, self-contained, "
        "gallery-quality plot scripts that follow the provided style rules exactly."
    )
    user = "\n\n---\n\n".join(
        [
            f"# Task\n\nImplement the plot specification below using **{library}** (Python).",
            f"# Base generation rules\n\n{base_rules}",
            f"# Style guide\n\n{style_guide}",
            f"# Library rules: {library}\n\n{library_rules}",
            f"# Specification: {spec_id}\n\n{specification}",
            _OUTPUT_CONTRACT.format(library=library),
        ]
    )
    return system, user


def build_repair_prompt(base_user_prompt: str, previous_code: str, error_text: str) -> str:
    """Append the failed attempt + error to the base prompt for a retry."""
    return (
        base_user_prompt
        + "\n\n---\n"
        + _REPAIR_SECTION.format(previous_code=previous_code.strip(), error_text=error_text.strip()[-4000:])
    )


def extract_code_block(text: str) -> str:
    """Extract the implementation code from a model response.

    Takes the longest fenced code block (models occasionally emit a short
    usage snippet next to the real implementation). Falls back to the raw
    text when there is no fence but the response already looks like code.
    """
    blocks = re.findall(r"```(?:[a-zA-Z0-9_+-]*)\n(.*?)```", text, flags=re.DOTALL)
    if blocks:
        return max(blocks, key=len).strip()

    stripped = text.strip()
    if "import " in stripped and "```" not in stripped:
        return stripped

    raise ValueError("No fenced code block found in model response")


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required prompt input missing: {path}")
    return path.read_text(encoding="utf-8").strip()
