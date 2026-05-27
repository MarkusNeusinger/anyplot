#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "click>=8.1",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""Stage B of the imprint migration: re-render light+dark images locally and
overwrite the GCS production bucket.

Targets are discovered from either git's working tree (``git diff --name-only HEAD``,
the default — useful right after running Stage A) or from a specific commit
(``--from-commit <sha>``, used after a squash-merge to re-render the files that
just landed on ``main``). For every (spec, language, library) target, this script:

1. Renders ``plot-light.png`` and ``plot-dark.png`` in ``.regen-preview/{library}/``
   by running the impl with ``ANYPLOT_THEME`` set to each theme.
2. Optimizes each PNG in place and emits responsive variants (400/800/1200 px,
   PNG + WebP) via ``core.images``.
3. Uploads the bundle to ``gs://anyplot-images/staging/{spec}/{language}/{library}/``.
4. Promotes staging → ``gs://anyplot-images/plots/{spec}/{language}/{library}/``
   with public-read ACL, then deletes staging.

Resumable via ``.migration-progress.json`` — Ctrl-C and re-run to continue from
where you stopped. Skips items already marked ``done``.

Self-contained: does NOT depend on the regen module, so it works for R and
Julia impls too (the regen module is Python-only).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


REPO_ROOT = Path(__file__).resolve().parent.parent
PROGRESS_FILE = REPO_ROOT / ".migration-progress.json"

# Use the project's venv directly. The script's own inline-deps venv (click,
# pyyaml, rich) does not have matplotlib/bokeh/etc., so `uv run python` would
# pick the wrong interpreter. The project venv is created via `uv sync --extra plotting`.
PROJECT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"

GCS_BUCKET = "anyplot-images"
CACHE_HEADER = "Cache-Control:public, max-age=604800"

FILE_EXT_BY_LANGUAGE: dict[str, str] = {"python": ".py", "r": ".R", "julia": ".jl"}

# Libraries that need a display server (Selenium-driven Chrome for PNG export).
SELENIUM_LIBS = {"bokeh", "highcharts"}


# ─────────────────────────────────────────────────────────────────────────────
# Path helpers
# ─────────────────────────────────────────────────────────────────────────────


def _impl_path(spec: str, language: str, library: str) -> Path:
    return REPO_ROOT / "plots" / spec / "implementations" / language / f"{library}{FILE_EXT_BY_LANGUAGE[language]}"


def _preview_dir(spec: str, language: str, library: str) -> Path:
    return REPO_ROOT / "plots" / spec / "implementations" / language / ".regen-preview" / library


def _staging_path(spec: str, language: str, library: str) -> str:
    return f"gs://{GCS_BUCKET}/staging/{spec}/{language}/{library}"


def _production_path(spec: str, language: str, library: str) -> str:
    return f"gs://{GCS_BUCKET}/plots/{spec}/{language}/{library}"


# ─────────────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PreFlight:
    python_ok: bool
    r_ok: bool
    julia_ok: bool
    chrome_ok: bool
    chromedriver_ok: bool
    gcloud_ok: bool
    notes: list[str]


def _check_command(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


PYTHON_LIB_IMPORTS: dict[str, str] = {
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotnine": "plotnine",
    "plotly": "plotly",
    "bokeh": "bokeh",
    "altair": "altair",
    "pygal": "pygal",
    "highcharts": "highcharts_core",
    "letsplot": "lets_plot",
}


def preflight(python_libs: set[str], needs_r: bool, needs_julia: bool, needs_selenium: bool) -> PreFlight:
    notes: list[str] = []

    if not PROJECT_PYTHON.is_file():
        python_ok = False
        notes.append(f"Project venv missing at {PROJECT_PYTHON} → run: uv sync --extra plotting")
    elif not python_libs:
        python_ok = True
    else:
        modules = sorted({PYTHON_LIB_IMPORTS[lib] for lib in python_libs if lib in PYTHON_LIB_IMPORTS})
        python_ok = _check_command([str(PROJECT_PYTHON), "-c", "import " + ", ".join(modules)])
        if not python_ok:
            notes.append(f"Project venv lacks one of: {', '.join(modules)} → run: uv sync --extra plotting")

    r_ok = _check_command(["R", "--version"]) if needs_r else True
    if needs_r and not r_ok:
        notes.append("R not installed → sudo apt-get install r-base r-base-dev, then install ggplot2 + ragg + tidyr + dplyr (see plan)")

    julia_ok = _check_command(["julia", "--version"]) if needs_julia else True
    if needs_julia and not julia_ok:
        notes.append("Julia not installed → download from julialang.org, then julia --project=. -e 'using Pkg; Pkg.instantiate()'")

    chrome_ok = True
    chromedriver_ok = True
    if needs_selenium:
        chrome_ok = _check_command(["google-chrome", "--version"]) or _check_command(["chromium", "--version"])
        chromedriver_ok = _check_command(["chromedriver", "--version"])
        if not chrome_ok:
            notes.append("Chrome/Chromium missing (needed for bokeh + highcharts PNG export)")
        if not chromedriver_ok:
            notes.append("chromedriver missing (needed for bokeh + highcharts PNG export)")

    gcloud_ok = _check_command(["gcloud", "auth", "list", "--format=value(account)"])
    if not gcloud_ok:
        notes.append("gcloud not authenticated → gcloud auth login")

    gsutil_ok = _check_command(["gsutil", "version"])
    if not gsutil_ok:
        gcloud_ok = False
        notes.append("gsutil not on PATH → install via 'gcloud components install gsutil'")

    return PreFlight(
        python_ok=python_ok,
        r_ok=r_ok,
        julia_ok=julia_ok,
        chrome_ok=chrome_ok,
        chromedriver_ok=chromedriver_ok,
        gcloud_ok=gcloud_ok,
        notes=notes,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────


def _render_one_theme(impl: Path, preview: Path, language: str, theme: str) -> None:
    env = os.environ.copy()
    env["ANYPLOT_THEME"] = theme
    env["MPLBACKEND"] = "Agg"

    if language == "python":
        cmd = [str(PROJECT_PYTHON), "-P", str(impl.resolve())]
    elif language == "r":
        cmd = ["Rscript", str(impl.resolve())]
    elif language == "julia":
        cmd = ["julia", f"--project={REPO_ROOT}", str(impl.resolve())]
    else:
        raise ValueError(f"Unsupported language: {language}")

    # xvfb-run gives bokeh/highcharts a display when Chrome is headless-only.
    try:
        subprocess.run(["xvfb-run", *cmd], cwd=preview, env=env, check=True, capture_output=True, timeout=180)
    except FileNotFoundError:
        subprocess.run(cmd, cwd=preview, env=env, check=True, capture_output=True, timeout=180)


def render(spec: str, language: str, library: str) -> tuple[Path, Path]:
    impl = _impl_path(spec, language, library)
    if not impl.is_file():
        raise FileNotFoundError(f"impl not found: {impl}")

    preview = _preview_dir(spec, language, library)
    if preview.exists():
        shutil.rmtree(preview)
    preview.mkdir(parents=True)

    for theme in ("light", "dark"):
        _render_one_theme(impl, preview, language, theme)

    light_png = preview / "plot-light.png"
    dark_png = preview / "plot-dark.png"
    if not light_png.is_file() or not dark_png.is_file():
        raise RuntimeError(f"render incomplete in {preview} — missing light or dark PNG")
    return light_png, dark_png


# ─────────────────────────────────────────────────────────────────────────────
# Optimize + responsive variants
# ─────────────────────────────────────────────────────────────────────────────


def _process_image(png: Path) -> None:
    subprocess.run(
        [str(PROJECT_PYTHON), "-m", "core.images", "process", str(png), str(png)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [str(PROJECT_PYTHON), "-m", "core.images", "responsive", str(png), str(png.parent) + "/"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GCS upload + promote
# ─────────────────────────────────────────────────────────────────────────────


def _gsutil(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gsutil", *args], check=check, capture_output=True, text=True)


def upload_to_staging(preview: Path, staging: str) -> None:
    targets: list[Path] = []
    for pat in ("plot-light*.png", "plot-light*.webp", "plot-dark*.png", "plot-dark*.webp"):
        targets.extend(sorted(preview.glob(pat)))
    if not targets:
        raise FileNotFoundError(f"no rendered images in {preview}")
    _gsutil(["-m", "-h", CACHE_HEADER, "cp", *(str(p) for p in targets), f"{staging}/"])
    _gsutil(["-m", "acl", "ch", "-u", "AllUsers:R", f"{staging}/plot-light*", f"{staging}/plot-dark*"], check=False)

    for theme in ("light", "dark"):
        html = preview / f"plot-{theme}.html"
        if html.is_file():
            _gsutil(["-h", CACHE_HEADER, "cp", str(html), f"{staging}/plot-{theme}.html"])
            _gsutil(["acl", "ch", "-u", "AllUsers:R", f"{staging}/plot-{theme}.html"], check=False)


def promote_to_production(staging: str, production: str) -> None:
    # Copy then make public; finally clean up staging.
    _gsutil(["-m", "-h", CACHE_HEADER, "cp", "-r", f"{staging}/*", f"{production}/"])
    _gsutil(["-m", "acl", "ch", "-r", "-u", "AllUsers:R", f"{production}/"], check=False)
    _gsutil(["-m", "rm", "-r", f"{staging}/"], check=False)


# ─────────────────────────────────────────────────────────────────────────────
# Progress persistence
# ─────────────────────────────────────────────────────────────────────────────


def _load_progress() -> dict[str, str]:
    if PROGRESS_FILE.is_file():
        return json.loads(PROGRESS_FILE.read_text())
    return {}


def _save_progress(progress: dict[str, str]) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, sort_keys=True))


def _key(spec: str, language: str, library: str) -> str:
    return f"{spec}/{language}/{library}"


# ─────────────────────────────────────────────────────────────────────────────
# Target discovery — files that were just changed by Stage A
# ─────────────────────────────────────────────────────────────────────────────


def _parse_changed_files(stdout: str, library_filter: str) -> list[tuple[str, str, str]]:
    targets: list[tuple[str, str, str]] = []
    for line in stdout.splitlines():
        # Expected: plots/{spec}/implementations/{language}/{library}.{ext}
        parts = line.split("/")
        if len(parts) != 5 or parts[0] != "plots" or parts[2] != "implementations":
            continue
        spec = parts[1]
        language = parts[3]
        if language not in FILE_EXT_BY_LANGUAGE:
            continue
        library = Path(parts[4]).stem
        if library_filter != "all" and library != library_filter:
            continue
        targets.append((spec, language, library))
    return targets


def _discover_targets_from_git(library_filter: str) -> list[tuple[str, str, str]]:
    """Find (spec, language, library) from git's working tree — files modified vs HEAD."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return _parse_changed_files(out.stdout, library_filter)


def _discover_targets_from_commit(commit: str, library_filter: str) -> list[tuple[str, str, str]]:
    """Find (spec, language, library) from a specific commit's file list (squash-merge friendly)."""
    out = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", commit],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return _parse_changed_files(out.stdout, library_filter)


# ─────────────────────────────────────────────────────────────────────────────
# Per-target driver
# ─────────────────────────────────────────────────────────────────────────────


def process_one(spec: str, language: str, library: str, *, dry_run: bool, console: Console) -> str:
    """Returns one of: done | error: <msg> | skipped (dry-run)."""
    preview = _preview_dir(spec, language, library)

    try:
        light, dark = render(spec, language, library)
    except Exception as e:
        return f"error: render failed: {type(e).__name__}: {e}"

    if dry_run:
        console.print(f"  [dim]dry-run[/dim] rendered {light.relative_to(REPO_ROOT)} + {dark.relative_to(REPO_ROOT)}")
        return "skipped (dry-run)"

    try:
        _process_image(light)
        _process_image(dark)
    except subprocess.CalledProcessError as e:
        return f"error: image processing failed: {e}"

    staging = _staging_path(spec, language, library)
    production = _production_path(spec, language, library)
    try:
        upload_to_staging(preview, staging)
        promote_to_production(staging, production)
    except subprocess.CalledProcessError as e:
        return f"error: GCS upload failed: {e}"

    # Clean preview dir to save disk over a 1000+ file run.
    shutil.rmtree(preview, ignore_errors=True)
    return "done"


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


@click.command()
@click.option(
    "--library",
    default="all",
    help="Process one library or 'all'. Filters discovered targets.",
)
@click.option("--spec", default=None, help="Restrict to one spec (for testing).")
@click.option(
    "--check-only",
    is_flag=True,
    help="Run pre-flight checks and exit. Does not render or upload.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Render locally but do NOT optimize, upload, or promote.",
)
@click.option(
    "--skip-on-error",
    is_flag=True,
    help="Continue past per-target failures instead of stopping.",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Skip items already marked 'done' in .migration-progress.json.",
)
@click.option(
    "--from-commit",
    default=None,
    help="Discover targets from a specific commit (e.g. a squash-merge SHA) instead of the working tree.",
)
def main(library: str, spec: str | None, check_only: bool, dry_run: bool, skip_on_error: bool, resume: bool, from_commit: str | None) -> None:
    """Re-render and upload light/dark images for migrated impls."""
    console = Console()

    # Discover targets first so we know which langs to pre-flight.
    if from_commit:
        targets = _discover_targets_from_commit(from_commit, library)
    else:
        targets = _discover_targets_from_git(library)
    if spec:
        targets = [t for t in targets if t[0] == spec]

    if not targets and not check_only:
        console.print("[yellow]No modified impl files in working tree.[/yellow] "
                      "Apply Stage A first (or pass --spec for one-off testing).")
        if not spec:
            sys.exit(1)
        # If --spec given, fall through with a synthetic target.
        # Spec given but not changed → run a single target inferred from library filter.
        if library != "all":
            for lang, libs in (("python", ["matplotlib", "seaborn", "plotnine", "plotly", "bokeh", "altair", "pygal", "highcharts", "letsplot"]),
                                ("r", ["ggplot2"]),
                                ("julia", ["makie"])):
                if library in libs:
                    targets = [(spec, lang, library)]
                    break

    needs_r = any(t[1] == "r" for t in targets)
    needs_julia = any(t[1] == "julia" for t in targets)
    needs_selenium = any(t[2] in SELENIUM_LIBS for t in targets)
    python_libs = {t[2] for t in targets if t[1] == "python"}

    pf = preflight(python_libs=python_libs, needs_r=needs_r, needs_julia=needs_julia, needs_selenium=needs_selenium)
    if pf.notes:
        console.print("[bold]Pre-flight checks:[/bold]")
        for n in pf.notes:
            console.print(f"  [red]✗[/red] {n}")
        if check_only or not (pf.python_ok and pf.r_ok and pf.julia_ok and pf.gcloud_ok):
            console.print()
            console.print("[red]Fix the pre-flight issues above before continuing.[/red]")
            sys.exit(2 if not check_only else 0)
    else:
        console.print("[green]All pre-flight checks passed.[/green]")
        if check_only:
            sys.exit(0)

    progress_data = _load_progress() if resume else {}
    progress_data.setdefault("__started__", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    console.print(f"\nProcessing {len(targets)} target(s) "
                  f"(library={library}, spec={spec or 'all'}, dry_run={dry_run})")

    failures: list[tuple[str, str]] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as bar:
        task = bar.add_task("Migrating", total=len(targets))
        for spec_id, language, lib in targets:
            key = _key(spec_id, language, lib)
            if resume and progress_data.get(key) == "done":
                bar.advance(task)
                continue
            bar.update(task, description=f"Migrating {key}")
            result = process_one(spec_id, language, lib, dry_run=dry_run, console=console)
            progress_data[key] = result
            _save_progress(progress_data)
            if result.startswith("error"):
                failures.append((key, result))
                if not skip_on_error:
                    console.print(f"\n[red]Aborting on first error: {key} → {result}[/red]")
                    console.print("Re-run with --skip-on-error to continue past failures.")
                    sys.exit(1)
            bar.advance(task)

    console.print(f"\n[bold]Done.[/bold] {len(targets) - len(failures)} succeeded, {len(failures)} failed.")
    if failures:
        console.print("[yellow]Failures:[/yellow]")
        for k, msg in failures[:20]:
            console.print(f"  • {k}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
