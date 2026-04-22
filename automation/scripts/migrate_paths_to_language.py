#!/usr/bin/env python3
"""One-off migration: layer {language} into plots/ paths.

Moves:
    plots/{spec}/implementations/{library}.py
        → plots/{spec}/implementations/python/{library}.py

    plots/{spec}/metadata/{library}.yaml
        → plots/{spec}/metadata/python/{library}.yaml

Uses `git mv` so blame history is preserved. Safe to re-run (idempotent —
skips already-migrated directories).

Usage:
    uv run python automation/scripts/migrate_paths_to_language.py [--dry-run]

Phase B of the big plot migration. Should be run once, as a single commit.
Workflows (impl-generate.yml, impl-merge.yml, impl-repair.yml) and the
frontend must be updated in the same PR — this script does not touch them.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
PLOTS_DIR = REPO_ROOT / "plots"

# Only python exists today; extend this map when R/JavaScript/Julia arrive.
# Must match core.constants.LANGUAGE_FILE_EXTENSIONS.
LANGUAGE_FOR_EXTENSION: dict[str, str] = {".py": "python"}
KNOWN_LANGUAGE_DIRS: set[str] = set(LANGUAGE_FOR_EXTENSION.values())


def git_mv(src: Path, dst: Path, dry_run: bool) -> None:
    """Run `git mv src dst`, ensuring the destination parent exists."""
    rel_src = src.relative_to(REPO_ROOT)
    rel_dst = dst.relative_to(REPO_ROOT)
    if dry_run:
        print(f"  [dry-run] git mv {rel_src} {rel_dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "mv", str(rel_src), str(rel_dst)], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print(f"  ERROR: git mv failed for {rel_src} → {rel_dst}:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"git mv failed: {rel_src}")


def migrate_spec_dir(spec_dir: Path, dry_run: bool) -> tuple[int, int]:
    """Migrate one spec directory. Returns (impl_moved, metadata_moved)."""
    impl_moved = 0
    metadata_moved = 0

    implementations_dir = spec_dir / "implementations"
    metadata_dir = spec_dir / "metadata"

    # Implementations: move flat .py files into implementations/python/
    if implementations_dir.exists():
        for impl_file in sorted(implementations_dir.iterdir()):
            if not impl_file.is_file():
                continue
            ext = impl_file.suffix
            if ext not in LANGUAGE_FOR_EXTENSION:
                # Skip unknown-extension files (README, .pyc cache, etc.)
                continue
            language = LANGUAGE_FOR_EXTENSION[ext]
            dst = implementations_dir / language / impl_file.name
            if dst.exists():
                # Already migrated
                continue
            git_mv(impl_file, dst, dry_run)
            impl_moved += 1

    # Metadata: move flat .yaml files into metadata/python/
    if metadata_dir.exists():
        for meta_file in sorted(metadata_dir.iterdir()):
            if not meta_file.is_file() or meta_file.suffix not in {".yaml", ".yml"}:
                continue
            # Heuristic: files named like {library}.yaml are per-library metadata and belong
            # under python/. Any other yaml (none known today) would need human review.
            library_id = meta_file.stem
            if library_id.startswith("_"):
                continue
            dst = metadata_dir / "python" / meta_file.name
            if dst.exists():
                continue
            git_mv(meta_file, dst, dry_run)
            metadata_moved += 1

    return impl_moved, metadata_moved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would move without doing it.")
    args = parser.parse_args()

    if not PLOTS_DIR.exists():
        print(f"plots/ directory not found at {PLOTS_DIR}", file=sys.stderr)
        return 1

    specs = sorted(d for d in PLOTS_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))
    print(f"Scanning {len(specs)} specs under {PLOTS_DIR}")

    total_impl = 0
    total_meta = 0
    specs_touched = 0

    for spec_dir in specs:
        impl, meta = migrate_spec_dir(spec_dir, args.dry_run)
        if impl or meta:
            specs_touched += 1
            print(f"{spec_dir.name}: {impl} implementations, {meta} metadata files")
        total_impl += impl
        total_meta += meta

    print()
    print(f"Summary: {specs_touched}/{len(specs)} specs touched")
    print(f"  {total_impl} implementation files moved to implementations/python/")
    print(f"  {total_meta} metadata files moved to metadata/python/")
    if args.dry_run:
        print("Dry-run only — no changes made. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
