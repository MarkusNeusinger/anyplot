"""Render both light + dark themes for a single library implementation.

Replaces regen.md step 2d. Two responsibilities:

1.  Sidestep the **self-import collision**. Implementations are named after
    their library (e.g. `altair.py`), so running them as a script normally
    puts their directory on `sys.path[0]` and `import altair` resolves to
    the local file instead of the package. We avoid this by invoking
    `python -P <impl>` (Python ≥3.11): `-P` skips prepending the script's
    directory to `sys.path`, so `import altair` finds the installed
    package. The impl is run **in place** — we do not copy it — because
    several library implementations (highcharts, pygal, ...) resolve
    relative assets via `Path(__file__).parents[...]`. Copying changes
    `__file__` and breaks those.

2.  Run twice with `ANYPLOT_THEME=light` then `ANYPLOT_THEME=dark`, with
    cwd set to the preview directory so the artifacts (`plot-{theme}.png`,
    `plot-{theme}.html`) land in `.regen-preview/{library}/`. `impl-merge.yml`
    refuses to merge if either PNG is missing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenderResult:
    preview_dir: Path
    light_png: Path
    dark_png: Path
    light_html: Path | None
    dark_html: Path | None


def _preview_dir(spec_id: str, library: str) -> Path:
    return Path("plots") / spec_id / "implementations" / "python" / ".regen-preview" / library


def _impl_path(spec_id: str, library: str) -> Path:
    return Path("plots") / spec_id / "implementations" / "python" / f"{library}.py"


def _run_one_theme(impl_abs: Path, preview_dir: Path, theme: str) -> None:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["ANYPLOT_THEME"] = theme
    cmd = ["uv", "run", "python", "-P", str(impl_abs)]
    # Bokeh's export_png requires a browser. xvfb provides the display when
    # chromedriver isn't available (snap-shim on Ubuntu).
    try:
        subprocess.run(["xvfb-run"] + cmd, cwd=preview_dir, env=env, check=True)
    except FileNotFoundError:
        # xvfb-run not available (e.g. CI on macOS); fall back to bare run.
        subprocess.run(cmd, cwd=preview_dir, env=env, check=True)


def run_theme_renders(spec_id: str, library: str, max_retries: int = 3) -> RenderResult:
    """Produce `plot-{light,dark}.png` (and optional `.html`) under `.regen-preview/{library}/`.

    Always starts from a clean preview dir — stale artifacts from a prior
    attempt would otherwise satisfy the existence checks even if the current
    run failed to regenerate one of the themes.
    """
    impl = _impl_path(spec_id, library)
    if not impl.is_file():
        raise FileNotFoundError(f"Implementation file not found: {impl}")
    impl_abs = impl.resolve()

    preview = _preview_dir(spec_id, library)
    if preview.exists():
        shutil.rmtree(preview)
    preview.mkdir(parents=True)

    for theme in ("light", "dark"):
        for attempt in range(1, max_retries + 1):
            try:
                _run_one_theme(impl_abs, preview, theme)
                break
            except subprocess.CalledProcessError as exc:
                if attempt == max_retries:
                    raise RuntimeError(f"render failed for theme={theme} after {max_retries} attempts: {exc}") from exc

    light_png = preview / "plot-light.png"
    dark_png = preview / "plot-dark.png"
    if not light_png.is_file():
        raise RuntimeError(f"plot-light.png not produced in {preview}")
    if not dark_png.is_file():
        raise RuntimeError(f"plot-dark.png not produced in {preview}")

    light_html = preview / "plot-light.html"
    dark_html = preview / "plot-dark.html"
    return RenderResult(
        preview_dir=preview,
        light_png=light_png,
        dark_png=dark_png,
        light_html=light_html if light_html.is_file() else None,
        dark_html=dark_html if dark_html.is_file() else None,
    )
