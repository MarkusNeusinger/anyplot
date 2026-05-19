"""Local style-variant experimentation tool.

A/B-test plot style variants (canvas size, fonts, palette, ...) on real
spec/library combos. Mimics the production renderer
(``agentic/workflows/modules/regen/render.py``) so visual results are
trustworthy.

Outputs land under ``/tmp/anyplot-style-experiments/<timestamp>/`` by default.
The script sets ``cwd`` to the run directory so anything an implementation
writes via relative paths goes there, and the pre/post ``git status`` check
on ``plots/`` flags any artifacts that leaked in beside the source (some
impls resolve paths from ``__file__``). It can detect, but not prevent, that.

Usage::

    uv run python scripts/style-experiment.py \
        --spec scatter-basic --spec dendrogram-basic \
        --library matplotlib --library plotly \
        --variant baseline --variant smaller_canvas --variant bigger_fonts \
        --theme both \
        --open

Run with ``--help`` for the full option list.

Patches are applied **in place** to the implementation source file and
restored on exit (success, exception, or signal). This is required because
some implementations (highcharts) resolve ``Path(__file__).parents[3]`` to
find shared assets - copying the file to a temp dir would break those.
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from html import escape as h
from pathlib import Path
from typing import Any
from urllib.parse import quote as urlquote

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VARIANTS_FILE = REPO_ROOT / "scripts" / "style-variants.yaml"
DEFAULT_OUTPUT_ROOT = Path("/tmp/anyplot-style-experiments")
RENDER_TIMEOUT_SEC = 300


@dataclass
class Patch:
    find: str | None = None
    regex: str | None = None
    replace: str = ""

    def apply(self, text: str) -> tuple[str, int]:
        if self.regex is not None:
            new, n = re.subn(self.regex, self.replace, text)
            return new, n
        if self.find is not None:
            n = text.count(self.find)
            return text.replace(self.find, self.replace), n
        raise ValueError("Patch must have either 'find' or 'regex'")


@dataclass
class Variant:
    name: str
    description: str
    patches_by_lib: dict[str, list[Patch]] = field(default_factory=dict)

    def patches_for(self, library: str) -> list[Patch]:
        return self.patches_by_lib.get("*", []) + self.patches_by_lib.get(library, [])


@dataclass
class RunRecord:
    spec: str
    library: str
    variant: str
    theme: str
    success: bool
    png_path: str | None
    html_path: str | None
    error: str | None
    duration_sec: float
    patches_applied: int


def load_variants(path: Path, names: list[str]) -> list[Variant]:
    if not path.is_file():
        sys.exit(f"Variants file not found: {path}")
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        sys.exit(
            f"Variants file is empty or not a YAML mapping: {path} "
            f"(got {type(data).__name__})"
        )
    catalog = data.get("variants") or {}
    if not isinstance(catalog, dict):
        sys.exit(
            f"'variants' key in {path} must be a mapping "
            f"(got {type(catalog).__name__})"
        )
    missing = [n for n in names if n not in catalog]
    if missing:
        sys.exit(
            f"Unknown variant(s): {', '.join(missing)}. "
            f"Available: {', '.join(catalog.keys())}"
        )
    out: list[Variant] = []
    for name in names:
        entry = catalog[name]
        patches_raw = entry.get("patches") or {}
        patches_by_lib: dict[str, list[Patch]] = {}
        for lib, plist in patches_raw.items():
            patches_by_lib[lib] = [Patch(**p) for p in (plist or [])]
        out.append(Variant(
            name=name,
            description=entry.get("description", ""),
            patches_by_lib=patches_by_lib,
        ))
    return out


def apply_patches(text: str, patches: list[Patch]) -> tuple[str, int]:
    total = 0
    for p in patches:
        text, n = p.apply(text)
        total += n
    return text, total


_pending_restores: dict[Path, str] = {}
_restores_lock = threading.Lock()


def _restore_all() -> None:
    with _restores_lock:
        items = list(_pending_restores.items())
    for path, original in items:
        try:
            path.write_text(original)
        except Exception as exc:
            print(f"[style-experiment] WARNING: failed to restore {path}: {exc}; "
                  f"will retry on next cleanup hook",
                  file=sys.stderr)
            continue
        with _restores_lock:
            _pending_restores.pop(path, None)


def _signal_handler(signum: int, frame: Any) -> None:
    _restore_all()
    sys.exit(128 + signum)


atexit.register(_restore_all)
_signals_to_trap = [
    s for s in (
        getattr(signal, "SIGINT", None),
        getattr(signal, "SIGTERM", None),
        getattr(signal, "SIGHUP", None),
    ) if s is not None
]
for _sig in _signals_to_trap:
    try:
        signal.signal(_sig, _signal_handler)
    except (ValueError, OSError):
        pass


@contextmanager
def patched_in_place(impl_path: Path, patches: list[Patch]):
    original = impl_path.read_text()
    if not patches:
        yield 0
        return
    patched, n_applied = apply_patches(original, patches)
    with _restores_lock:
        _pending_restores[impl_path] = original
    try:
        impl_path.write_text(patched)
        yield n_applied
    finally:
        impl_path.write_text(original)
        with _restores_lock:
            _pending_restores.pop(impl_path, None)


def render_one_theme(impl_path: Path, run_dir: Path, theme: str) -> None:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["ANYPLOT_THEME"] = theme
    cmd = ["uv", "run", "python", "-P", str(impl_path)]
    log = run_dir / f"run-{theme}.log"
    with log.open("w") as f:
        f.write(f"$ ANYPLOT_THEME={theme} DISPLAY={env.get('DISPLAY', '')} {' '.join(cmd)}\n\n")
        # If DISPLAY is already set (shared Xvfb started by main), use it directly.
        # Otherwise fall back to per-render xvfb-run -a, then native (no X).
        if env.get("DISPLAY"):
            subprocess.run(
                cmd,
                cwd=run_dir, env=env, check=True,
                stdout=f, stderr=subprocess.STDOUT,
                timeout=RENDER_TIMEOUT_SEC,
            )
            return
        try:
            subprocess.run(
                ["xvfb-run", "-a"] + cmd,
                cwd=run_dir, env=env, check=True,
                stdout=f, stderr=subprocess.STDOUT,
                timeout=RENDER_TIMEOUT_SEC,
            )
        except FileNotFoundError:
            subprocess.run(
                cmd,
                cwd=run_dir, env=env, check=True,
                stdout=f, stderr=subprocess.STDOUT,
                timeout=RENDER_TIMEOUT_SEC,
            )


def start_shared_xvfb() -> tuple[subprocess.Popen, str] | tuple[None, None]:
    """Start a single Xvfb for the whole experiment. Returns (proc, ':N')."""
    if not shutil.which("Xvfb"):
        return None, None
    for n in range(99, 200):
        if Path(f"/tmp/.X{n}-lock").exists():
            continue
        proc = subprocess.Popen(
            ["Xvfb", f":{n}", "-screen", "0", "1920x1080x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(0.7)
        if proc.poll() is None and Path(f"/tmp/.X{n}-lock").exists():
            return proc, f":{n}"
        try:
            proc.terminate()
        except Exception:
            pass
    raise RuntimeError("No free Xvfb display in :99..:199")


def run_one_combination(
    spec: str, library: str, variant: Variant, themes: list[str], output_root: Path,
) -> list[RunRecord]:
    impl_path = REPO_ROOT / "plots" / spec / "implementations" / "python" / f"{library}.py"
    run_dir = output_root / "runs" / f"{spec}__{library}__{variant.name}"

    if not impl_path.is_file():
        return [RunRecord(
            spec=spec, library=library, variant=variant.name, theme=t,
            success=False, png_path=None, html_path=None,
            error=f"Implementation not found: {impl_path.relative_to(REPO_ROOT)}",
            duration_sec=0.0, patches_applied=0,
        ) for t in themes]

    run_dir.mkdir(parents=True, exist_ok=True)
    patches = variant.patches_for(library)
    records: list[RunRecord] = []

    with patched_in_place(impl_path, patches) as n_applied:
        if patches and n_applied == 0:
            print(f"  [warn] variant '{variant.name}' had patches for "
                  f"{library} but none matched the source")
        snapshot = run_dir / f"{library}.patched.py"
        snapshot.write_text(impl_path.read_text())

        for theme in themes:
            t0 = time.time()
            png = run_dir / f"plot-{theme}.png"
            html = run_dir / f"plot-{theme}.html"
            if png.exists():
                png.unlink()
            if html.exists():
                html.unlink()
            try:
                render_one_theme(impl_path, run_dir, theme)
                ok = png.is_file()
                records.append(RunRecord(
                    spec=spec, library=library, variant=variant.name, theme=theme,
                    success=ok,
                    png_path=str(png.relative_to(output_root)) if ok else None,
                    html_path=str(html.relative_to(output_root)) if html.is_file() else None,
                    error=None if ok else "PNG not produced",
                    duration_sec=round(time.time() - t0, 2),
                    patches_applied=n_applied,
                ))
            except subprocess.TimeoutExpired:
                records.append(RunRecord(
                    spec=spec, library=library, variant=variant.name, theme=theme,
                    success=False, png_path=None, html_path=None,
                    error=f"timeout after {RENDER_TIMEOUT_SEC}s",
                    duration_sec=round(time.time() - t0, 2),
                    patches_applied=n_applied,
                ))
            except subprocess.CalledProcessError as exc:
                log_excerpt = (run_dir / f"run-{theme}.log").read_text()[-500:]
                records.append(RunRecord(
                    spec=spec, library=library, variant=variant.name, theme=theme,
                    success=False, png_path=None, html_path=None,
                    error=f"exit {exc.returncode}; log tail: ...{log_excerpt}",
                    duration_sec=round(time.time() - t0, 2),
                    patches_applied=n_applied,
                ))
    return records


def write_manifest(output_root: Path, records: list[RunRecord], variants: list[Variant]) -> None:
    manifest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "variants": [
            {
                "name": v.name,
                "description": v.description,
                "patches_by_lib": {
                    lib: [asdict(p) for p in plist]
                    for lib, plist in v.patches_by_lib.items()
                },
            } for v in variants
        ],
        "runs": [asdict(r) for r in records],
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2))


def write_compare_html(
    output_root: Path, records: list[RunRecord], variants: list[Variant],
    specs: list[str], libraries: list[str], themes: list[str],
) -> None:
    by_key: dict[tuple[str, str, str, str], RunRecord] = {
        (r.spec, r.library, r.variant, r.theme): r for r in records
    }
    variant_names = [v.name for v in variants]
    variant_desc = {v.name: v.description for v in variants}

    html: list[str] = []
    html.append("""<!doctype html>
<html><head><meta charset="utf-8"><title>anyplot style experiment</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f5f3ec; color: #1a1a17; margin: 0; padding: 24px; }
  h1 { margin: 0 0 8px; font-size: 20px; }
  .meta { color: #6b6a63; font-size: 13px; margin-bottom: 24px; }
  .toolbar { position: sticky; top: 0; background: #f5f3ec; padding: 12px 0;
             border-bottom: 1px solid rgba(0,0,0,0.08); margin-bottom: 16px; z-index: 10; }
  .toolbar label { margin-right: 12px; font-size: 13px; }
  .group { background: #faf8f1; border: 1px solid rgba(0,0,0,0.06); border-radius: 8px;
           padding: 16px; margin-bottom: 24px; }
  .group h2 { margin: 0 0 12px; font-size: 16px; }
  table { border-collapse: collapse; }
  th, td { padding: 6px 8px; vertical-align: top; text-align: left;
           border-bottom: 1px solid rgba(0,0,0,0.06); }
  th { font-size: 12px; font-weight: 500; color: #4a4a44; }
  th small { display: block; font-weight: 400; color: #6b6a63; max-width: 280px; }
  .cell img { display: block; width: var(--thumb, 320px); height: auto;
              border: 1px solid rgba(0,0,0,0.08); }
  .cell.dark img { background: #1a1a17; }
  .cell .label { font-size: 11px; color: #6b6a63; margin-top: 4px; }
  .err { width: var(--thumb, 320px); padding: 8px; background: #fdf2f2;
         border: 1px solid #f5c2c7; border-radius: 4px;
         font-family: ui-monospace, Menlo, monospace; font-size: 11px;
         color: #842029; white-space: pre-wrap; word-break: break-word; }
  [data-theme="dark"] body { background: #121210; color: #f0efe8; }
</style></head><body>""")

    html.append("<h1>anyplot style experiment</h1>")
    html.append(f"<div class='meta'>{h(datetime.now().strftime('%Y-%m-%d %H:%M'))} &middot; "
                f"{len(specs)} spec(s) &times; {len(libraries)} library(ies) &times; "
                f"{len(variants)} variant(s) &times; {len(themes)} theme(s) "
                f"= {len(records)} render(s)</div>")
    html.append("""<div class="toolbar">
  <label>Thumbnail width:
    <select onchange="document.documentElement.style.setProperty('--thumb', this.value)">
      <option value="160px">160px (mobile thumbnail)</option>
      <option value="320px">320px (grid)</option>
      <option value="375px" selected>375px (iPhone viewport)</option>
      <option value="640px">640px (detail)</option>
      <option value="700px">700px (Plot-of-the-Day)</option>
      <option value="1200px">1200px (large)</option>
    </select>
  </label>
</div>""")

    for spec in specs:
        for lib in libraries:
            html.append(f"<div class='group'><h2>{h(spec)} &mdash; {h(lib)}</h2>")
            html.append("<table><thead><tr><th></th>")
            for vn in variant_names:
                html.append(f"<th>{h(vn)}<small>{h(variant_desc[vn])}</small></th>")
            html.append("</tr></thead><tbody>")
            for theme in themes:
                html.append(f"<tr><th>{h(theme)}</th>")
                for vn in variant_names:
                    rec = by_key.get((spec, lib, vn, theme))
                    html.append(f"<td class='cell {h(theme)}'>")
                    if rec is None:
                        html.append("<div class='err'>(no record)</div>")
                    elif rec.success and rec.png_path:
                        href = urlquote(rec.png_path, safe="/")
                        html.append(f"<a href='{href}' target='_blank'>"
                                    f"<img src='{href}' loading='lazy'></a>")
                        html.append(f"<div class='label'>{rec.duration_sec}s"
                                    + (f", {rec.patches_applied} patch(es)" if rec.patches_applied else "")
                                    + "</div>")
                    else:
                        err = h((rec.error or "unknown error")[:600])
                        html.append(f"<div class='err'>{err}</div>")
                    html.append("</td>")
                html.append("</tr>")
            html.append("</tbody></table></div>")

    html.append("</body></html>")
    (output_root / "compare.html").write_text("\n".join(html))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Local style-variant experimentation for anyplot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--spec", action="append", required=True, dest="specs",
                   help="Spec ID (repeatable or comma-separated)")
    p.add_argument("--library", action="append", required=True, dest="libraries",
                   help="Library name (repeatable or comma-separated)")
    p.add_argument("--variant", action="append", required=True, dest="variants",
                   help="Variant name from variants file (repeatable or comma-separated)")
    p.add_argument("--theme", choices=("light", "dark", "both"), default="both")
    p.add_argument("--variants-file", type=Path, default=DEFAULT_VARIANTS_FILE)
    p.add_argument("--output", type=Path, default=None,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_ROOT}/<timestamp>)")
    p.add_argument("--open", dest="open_browser", action="store_true",
                   help="Open compare.html in the default browser when done")
    p.add_argument("--parallel", type=int, default=1,
                   help="Parallel (spec, library) workers. Each worker runs variants "
                        "serially since they patch the same source file. Default 1.")
    return p.parse_args()


def expand_csv(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        out.extend(s.strip() for s in v.split(",") if s.strip())
    return out


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)

    specs = expand_csv(args.specs)
    libraries = expand_csv(args.libraries)
    variant_names = expand_csv(args.variants)
    themes = ["light", "dark"] if args.theme == "both" else [args.theme]

    variants = load_variants(args.variants_file, variant_names)

    output_root = args.output or (DEFAULT_OUTPUT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S"))
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "runs").mkdir(exist_ok=True)

    pre_dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "plots/"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout.strip()
    if pre_dirty:
        print("[style-experiment] WARNING: plots/ has uncommitted or untracked files before run:")
        print(pre_dirty)
        print("Patches will still be reverted via try/finally, but verify with `git status` after.\n")

    total = len(specs) * len(libraries) * len(variants) * len(themes)
    parallel = max(1, int(args.parallel))
    print(f"[style-experiment] {total} render(s) -> {output_root}")
    print(f"[style-experiment] specs={specs} libs={libraries} variants={variant_names} themes={themes}")
    print(f"[style-experiment] parallel workers={parallel} (one per spec,library pair)")

    # Single shared Xvfb avoids xvfb-run display-allocation races with parallel workers.
    xvfb_proc, xvfb_display = (None, None)
    if not os.environ.get("DISPLAY"):
        xvfb_proc, xvfb_display = start_shared_xvfb()
        if xvfb_display:
            os.environ["DISPLAY"] = xvfb_display
            print(f"[style-experiment] shared Xvfb on {xvfb_display} (pid {xvfb_proc.pid})")
            atexit.register(lambda: (xvfb_proc.terminate(), xvfb_proc.wait(timeout=3)) if xvfb_proc else None)

    # Auto-detect a real chromedriver for bokeh's export_png (Ubuntu's /usr/bin/chromedriver is a snap stub).
    # Selenium-manager downloads one to ~/.cache/selenium on first selenium.webdriver.Chrome() call.
    if not os.environ.get("BOKEH_CHROMEDRIVER_PATH"):
        cache = Path.home() / ".cache" / "selenium" / "chromedriver"
        candidates = sorted(cache.glob("*/[0-9]*/chromedriver")) if cache.is_dir() else []
        if candidates:
            os.environ["BOKEH_CHROMEDRIVER_PATH"] = str(candidates[-1])
            print(f"[style-experiment] BOKEH_CHROMEDRIVER_PATH={candidates[-1]}")
        else:
            print("[style-experiment] WARN: no selenium-managed chromedriver in cache; "
                  "bokeh's export_png may fail. Run any bokeh impl using selenium.webdriver.Chrome "
                  "once to populate ~/.cache/selenium, then retry.")
    print()

    work_units = [(spec, lib) for spec in specs for lib in libraries]
    print_lock = threading.Lock()
    all_records: list[RunRecord] = []
    records_lock = threading.Lock()
    counter = {"done": 0}
    total_units = len(work_units)

    def process_unit(spec_lib: tuple[str, str]) -> list[RunRecord]:
        spec, lib = spec_lib
        unit_records: list[RunRecord] = []
        for variant in variants:
            recs = run_one_combination(spec, lib, variant, themes, output_root)
            unit_records.extend(recs)
        with print_lock:
            counter["done"] += 1
            n_ok = sum(1 for r in unit_records if r.success)
            n_total = len(unit_records)
            tag = "OK" if n_ok == n_total else f"{n_ok}/{n_total} ok"
            print(f"[{counter['done']}/{total_units}] {spec} / {lib}: {tag}")
            for r in unit_records:
                if not r.success:
                    print(f"    FAIL  {r.variant} {r.theme}: {(r.error or '')[:100]}")
        return unit_records

    if parallel == 1:
        for unit in work_units:
            recs = process_unit(unit)
            all_records.extend(recs)
    else:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(process_unit, u): u for u in work_units}
            for fut in as_completed(futures):
                try:
                    recs = fut.result()
                except Exception as exc:
                    with print_lock:
                        print(f"[style-experiment] ERROR in {futures[fut]}: {exc}")
                    continue
                with records_lock:
                    all_records.extend(recs)

    write_manifest(output_root, all_records, variants)
    write_compare_html(output_root, all_records, variants, specs, libraries, themes)

    n_ok = sum(1 for r in all_records if r.success)
    print(f"\n[style-experiment] done: {n_ok}/{len(all_records)} succeeded")
    print(f"[style-experiment] compare: {output_root / 'compare.html'}")
    print(f"[style-experiment] manifest: {output_root / 'manifest.json'}")

    post_dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "plots/"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout.strip()
    if post_dirty and post_dirty != pre_dirty:
        print("\n[style-experiment] WARNING: plots/ is dirty after run (unrestored patches or stray artifacts):")
        print(post_dirty)
        print("Restore tracked files with `git checkout -- plots/` and inspect untracked entries before deleting.")
        return 2

    if args.open_browser:
        webbrowser.open((output_root / "compare.html").as_uri())

    return 0 if n_ok == len(all_records) else 1


if __name__ == "__main__":
    sys.exit(main())
