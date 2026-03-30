#!/usr/bin/env python3
"""Remove preview_thumb field from all metadata YAML files.

This is a one-time cleanup script. The preview_thumb field is no longer
needed because responsive image variants are derived from preview_url
by convention (issue #5191).

Usage:
    python scripts/remove_preview_thumb_from_yaml.py [--dry-run]
"""

import re
import sys
from pathlib import Path


PLOTS_DIR = Path(__file__).parent.parent / "plots"
PATTERN = re.compile(r"^preview_thumb:.*\n", re.MULTILINE)


def main(dry_run: bool = False):
    metadata_files = sorted(PLOTS_DIR.glob("*/metadata/*.yaml"))
    print(f"Found {len(metadata_files)} metadata YAML files")

    modified = 0
    skipped = 0

    for path in metadata_files:
        content = path.read_text()
        if "preview_thumb:" not in content:
            skipped += 1
            continue

        new_content = PATTERN.sub("", content)
        if new_content != content:
            if dry_run:
                print(f"  Would update: {path.relative_to(PLOTS_DIR.parent)}")
            else:
                path.write_text(new_content)
            modified += 1

    action = "Would modify" if dry_run else "Modified"
    print(f"\n{action}: {modified}, Skipped (no preview_thumb): {skipped}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
