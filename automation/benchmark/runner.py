"""Render benchmark implementations and validate their output.

v1 supports Python libraries only — they run with the same interpreter that
runs the benchmark, so a plain ``uv pip install -e ".[lib-<library>]"`` is
the whole runtime. R / Julia / JavaScript need their own runtimes plus the
browser render harness; they reuse the existing setup actions when the
benchmark grows past Python.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


THEMES = ("light", "dark")

# Same targets and tolerance as the post-render canvas gate in impl-review.
CANVAS_TARGETS = ((3200, 1800), (2400, 2400))
CANVAS_TOLERANCE_PX = 16


@dataclass
class RenderResult:
    """Outcome of rendering one implementation in both themes."""

    success: bool
    error: str | None = None
    canvas_ok: bool | None = None
    images: dict[str, Path] = field(default_factory=dict)


# The render subprocess executes LLM-generated code, so it must NOT inherit
# the caller's environment (in CI that includes the GCP/WIF credentials and
# GitHub token). Only these harmless variables pass through; HOME is remapped
# to a scratch directory so ~/.config (gcloud credentials, tool configs) is
# out of reach too.
_RENDER_ENV_ALLOWLIST = ("PATH", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP")


def render_env(theme: str, home: Path) -> dict[str, str]:
    """Minimal, credential-free environment for running generated code."""
    env = {key: value for key in _RENDER_ENV_ALLOWLIST if (value := os.environ.get(key)) is not None}
    env["HOME"] = str(home)
    env["ANYPLOT_THEME"] = theme
    env["MPLBACKEND"] = "Agg"
    return env


def run_python_implementation(code_file: Path, workdir: Path, timeout: int = 300) -> RenderResult:
    """Run ``code_file`` once per theme inside ``workdir``.

    Success requires both runs to exit 0 and both theme PNGs to exist.
    ``canvas_ok`` records (but does not fail on) the canvas-dimension gate —
    the benchmark wants to *measure* how often models hit the contract.
    """
    images: dict[str, Path] = {}
    scratch_home = workdir / ".render-home"
    scratch_home.mkdir(exist_ok=True)
    for theme in THEMES:
        env = render_env(theme, home=scratch_home)
        try:
            # -I (isolated mode): ignore PYTHON* env vars, user site-packages,
            # and the script directory on sys.path — defense in depth on top of
            # the env allowlist, since this runs LLM-generated code. The venv's
            # site-packages still resolve via pyvenv.cfg next to the executable.
            completed = subprocess.run(
                [sys.executable, "-I", str(code_file)],
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(success=False, error=f"{theme} render timed out after {timeout}s", images=images)

        if completed.returncode != 0:
            error = (completed.stderr or completed.stdout or "").strip()[-4000:]
            return RenderResult(
                success=False, error=f"{theme} render exited {completed.returncode}:\n{error}", images=images
            )

        png = workdir / f"plot-{theme}.png"
        if not png.is_file():
            return RenderResult(
                success=False, error=f"{theme} render exited 0 but wrote no plot-{theme}.png", images=images
            )
        images[theme] = png

    return RenderResult(success=True, canvas_ok=check_canvas(images["light"]), images=images)


def check_canvas(png_path: Path) -> bool:
    """True when the PNG is within tolerance of a canonical canvas size."""
    from PIL import Image

    with Image.open(png_path) as image:
        width, height = image.size
    return any(
        abs(width - target_w) <= CANVAS_TOLERANCE_PX and abs(height - target_h) <= CANVAS_TOLERANCE_PX
        for target_w, target_h in CANVAS_TARGETS
    )
