#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "click>=8.1",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""One-shot positional hex migration: Okabe-Ito / variant-D → imprint.

Walks every existing impl file under ``plots/*/implementations/{python,r,julia}/``,
keeps only those whose metadata YAML has BOTH ``preview_url_light`` and
``preview_url_dark``, and rewrites old palette hex literals in place using
a positional slot-to-slot mapping. Idempotent: files that already contain
only imprint hex are left untouched.

This is intentionally NOT integrated with the regen module — it's a
self-contained one-time fix that bypasses the AI review cycle to unify
the homepage palette quickly.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table


REPO_ROOT = Path(__file__).resolve().parent.parent

# Positional slot mappings. Order = slot index in the old palette.
# Keys are lowercased so the regex match (also lowercased) hits them.
OKABE_TO_IMPRINT: dict[str, str] = {
    "#009e73": "#009E73",
    "#d55e00": "#C475FD",
    "#0072b2": "#4467A3",
    "#cc79a7": "#BD8233",
    "#e69f00": "#AE3030",
    "#56b4e9": "#2ABCCD",
    "#f0e442": "#954477",
}

VARIANT_D_TO_IMPRINT: dict[str, str] = {
    "#009e73": "#009E73",
    "#9418db": "#C475FD",
    "#b71d27": "#AE3030",
    "#16b8f3": "#4467A3",
    "#99b314": "#99B314",
    "#d359a7": "#954477",
    "#ba843e": "#BD8233",
}

# Combined map. Both palettes share #009E73, and Okabe doesn't include the
# variant-D hex codes (and vice versa), so they merge cleanly.
COMBINED: dict[str, str] = {**OKABE_TO_IMPRINT, **VARIANT_D_TO_IMPRINT}

# Hex codes we expect to find — lowercased, with leading '#'.
OLD_HEXES: set[str] = {k for k in COMBINED if COMBINED[k].lower() != k}

# Same mapping expressed as RGB triples, for rgba(r,g,b,a) literals. The hex
# regex above doesn't reach inline rgba() colors, but those are common in
# plotly/bokeh/altair for semi-transparent fills. Whitespace inside the rgba
# tuple is tolerated via a regex pattern rather than literal substring match.
def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


RGB_MAP: dict[tuple[int, int, int], tuple[int, int, int]] = {
    _hex_to_rgb(old): _hex_to_rgb(new) for old, new in COMBINED.items() if old.lower() != new.lower()
}

# Library names by language (subdir = language).
LIBRARIES_BY_LANGUAGE: dict[str, list[str]] = {
    "python": ["matplotlib", "seaborn", "plotnine", "plotly", "bokeh", "altair", "pygal", "highcharts", "letsplot"],
    "r": ["ggplot2"],
    "julia": ["makie"],
}
FILE_EXT_BY_LANGUAGE: dict[str, str] = {"python": ".py", "r": ".R", "julia": ".jl"}


@dataclass
class Stats:
    changed: int = 0
    skipped_already_imprint: int = 0
    skipped_no_dark: int = 0
    skipped_no_metadata: int = 0
    warnings: list[str] = field(default_factory=list)
    changed_files: list[Path] = field(default_factory=list)


# Match any #RRGGBB literal (3-byte form). The substitution callback decides
# whether to replace based on the lowercased value.
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")


def _substitute(text: str) -> tuple[str, int]:
    """Apply combined positional map. Returns (new_text, replacement_count)."""
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        original = match.group(0)
        lower = original.lower()
        new = COMBINED.get(lower)
        if new is None or new == original:
            return original
        # Only count a real change (don't count #009E73 → #009E73 no-ops).
        if new.lower() != lower:
            count += 1
            return new
        # Same hex but with different case — normalize case anyway, but don't
        # count as a substantive change.
        return new if new != original else original

    new_text = HEX_RE.sub(repl, text)
    new_text, rgba_count = _substitute_rgba(new_text)
    return new_text, count + rgba_count


# rgba(r, g, b, a) — r/g/b ints, a flexible. Tolerates any whitespace between
# the components and preserves the alpha + closing paren verbatim.
RGBA_RE = re.compile(r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,([^)]+)\)")


def _substitute_rgba(text: str) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        alpha = match.group(4)
        new_rgb = RGB_MAP.get((r, g, b))
        if new_rgb is None:
            return match.group(0)
        count += 1
        nr, ng, nb = new_rgb
        return f"rgba({nr}, {ng}, {nb},{alpha})"

    new_text = RGBA_RE.sub(repl, text)
    return new_text, count


def _rename_palette_constant(text: str) -> str:
    """Rename common old palette variable names to IMPRINT (Python, R, Julia).

    Whole-word ASCII boundary match. The regex is intentionally not
    AST-aware, so occurrences of OKABE_ITO / ANYPLOT_PALETTE inside
    comments or string literals are renamed too. That's fine for our
    one-shot use case (the surrounding comments are about to become
    stale anyway), but worth knowing for future reuse.
    """
    for old in ("OKABE_ITO", "ANYPLOT_PALETTE"):
        text = re.sub(rf"\b{old}\b", "IMPRINT", text)
    return text


def _metadata_path(spec_dir: Path, language: str, library: str) -> Path:
    return spec_dir / "metadata" / language / f"{library}.yaml"


def _impl_path(spec_dir: Path, language: str, library: str) -> Path:
    return spec_dir / "implementations" / language / f"{library}{FILE_EXT_BY_LANGUAGE[language]}"


def _has_dual_theme(meta_path: Path) -> bool:
    """True iff metadata YAML has both preview_url_light AND preview_url_dark non-empty."""
    if not meta_path.is_file():
        return False
    try:
        data = yaml.safe_load(meta_path.read_text()) or {}
    except yaml.YAMLError:
        return False
    return bool(data.get("preview_url_light")) and bool(data.get("preview_url_dark"))


def _process_file(
    impl_path: Path,
    meta_path: Path,
    *,
    dry_run: bool,
    stats: Stats,
) -> None:
    if not _has_dual_theme(meta_path):
        # No dark variant on record → skip per scope rule.
        if not meta_path.is_file():
            stats.skipped_no_metadata += 1
        else:
            stats.skipped_no_dark += 1
        return

    original = impl_path.read_text()
    lower = original.lower()

    has_old_hex = any(h in lower for h in OLD_HEXES)
    has_old_rgba = bool(RGBA_RE.search(original)) and any(
        f"rgba({r},{g},{b}" in lower.replace(" ", "") or f"rgba({r}, {g}, {b}" in original
        for r, g, b in RGB_MAP
    )
    if not (has_old_hex or has_old_rgba):
        stats.skipped_already_imprint += 1
        return

    # Detect mixed-palette case (file has hex from BOTH old palettes).
    okabe_only = OLD_HEXES & set(OKABE_TO_IMPRINT) - {"#009e73"}
    variant_only = OLD_HEXES & set(VARIANT_D_TO_IMPRINT) - {"#009e73", "#99b314"}
    has_okabe = any(h in lower for h in okabe_only)
    has_variant = any(h in lower for h in variant_only)
    if has_okabe and has_variant:
        stats.warnings.append(f"mixed palettes (Okabe + variant-D) in {impl_path.relative_to(REPO_ROOT)}")

    new_text, count = _substitute(original)
    new_text = _rename_palette_constant(new_text)

    if new_text == original:
        # Should not happen given has_old==True, but guard anyway.
        stats.skipped_already_imprint += 1
        return

    if not dry_run:
        impl_path.write_text(new_text)
    stats.changed += 1
    stats.changed_files.append(impl_path)


def _iter_targets(
    library_filter: str,
    spec_filter: str | None,
) -> list[tuple[Path, str, str]]:
    """Yield (spec_dir, language, library) for every existing impl matching filters."""
    plots_root = REPO_ROOT / "plots"
    if not plots_root.is_dir():
        raise click.ClickException(f"plots/ not found at {plots_root}")

    targets: list[tuple[Path, str, str]] = []
    spec_dirs = sorted(plots_root.iterdir())
    for spec_dir in spec_dirs:
        if not spec_dir.is_dir():
            continue
        if spec_filter and spec_dir.name != spec_filter:
            continue
        for language, libs in LIBRARIES_BY_LANGUAGE.items():
            for library in libs:
                if library_filter != "all" and library != library_filter:
                    continue
                impl = _impl_path(spec_dir, language, library)
                if impl.is_file():
                    targets.append((spec_dir, language, library))
    return targets


def _summarize(stats_by_lib: dict[str, Stats], console: Console, dry_run: bool) -> None:
    table = Table(title=("DRY RUN — no files written" if dry_run else "Migration applied"))
    table.add_column("Library", style="bold")
    table.add_column("Changed", justify="right", style="green")
    table.add_column("Already imprint", justify="right", style="cyan")
    table.add_column("No dark variant", justify="right", style="yellow")
    table.add_column("No metadata", justify="right", style="red")

    totals = Counter()
    for lib in sorted(stats_by_lib):
        s = stats_by_lib[lib]
        table.add_row(
            lib,
            str(s.changed),
            str(s.skipped_already_imprint),
            str(s.skipped_no_dark),
            str(s.skipped_no_metadata),
        )
        totals["changed"] += s.changed
        totals["skipped_already_imprint"] += s.skipped_already_imprint
        totals["skipped_no_dark"] += s.skipped_no_dark
        totals["skipped_no_metadata"] += s.skipped_no_metadata
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{totals['changed']}[/bold]",
        str(totals["skipped_already_imprint"]),
        str(totals["skipped_no_dark"]),
        str(totals["skipped_no_metadata"]),
    )
    console.print(table)

    warns = [w for s in stats_by_lib.values() for w in s.warnings]
    if warns:
        console.print(f"\n[yellow]Warnings ({len(warns)}):[/yellow]")
        for w in warns[:20]:
            console.print(f"  • {w}")
        if len(warns) > 20:
            console.print(f"  … and {len(warns) - 20} more")


@click.command()
@click.option(
    "--library",
    default="all",
    help="Restrict to one library (matplotlib, seaborn, ..., ggplot2, makie) or 'all'.",
)
@click.option("--spec", default=None, help="Restrict to one spec id (for testing).")
@click.option("--dry-run", is_flag=True, help="Report what would change; do not write files.")
@click.option("--list-changed", is_flag=True, help="After summary, list every changed file path (full report).")
def main(library: str, spec: str | None, dry_run: bool, list_changed: bool) -> None:
    """Migrate Okabe-Ito / variant-D hex codes to imprint, in place."""
    console = Console(stderr=True)

    valid_libs = {lib for libs in LIBRARIES_BY_LANGUAGE.values() for lib in libs} | {"all"}
    if library not in valid_libs:
        raise click.ClickException(f"Unknown library: {library}. Valid: {sorted(valid_libs)}")

    targets = _iter_targets(library, spec)
    if not targets:
        console.print(f"[red]No targets matched library={library} spec={spec}[/red]")
        sys.exit(1)

    console.print(f"Scanning {len(targets)} impl files (library={library}, spec={spec or 'all'})…")

    stats_by_lib: dict[str, Stats] = defaultdict(Stats)
    for spec_dir, language, lib in targets:
        impl = _impl_path(spec_dir, language, lib)
        meta = _metadata_path(spec_dir, language, lib)
        _process_file(impl, meta, dry_run=dry_run, stats=stats_by_lib[lib])

    _summarize(stats_by_lib, console, dry_run=dry_run)

    if list_changed:
        all_changed = [p for s in stats_by_lib.values() for p in s.changed_files]
        for p in sorted(all_changed):
            print(p.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
