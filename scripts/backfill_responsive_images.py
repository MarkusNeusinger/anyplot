#!/usr/bin/env python3
"""Backfill responsive image variants for all existing plots in GCS.

For each plot.png in production GCS, generates 7 responsive variants:
  plot_1200.png, plot_1200.webp, plot_800.png, plot_800.webp,
  plot_400.png, plot_400.webp, plot.webp

Usage:
    python scripts/backfill_responsive_images.py [--dry-run] [--offset N] [--limit N] [--skip-existing]
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.images import create_responsive_variants


GCS_BUCKET = "gs://pyplots-images"
PRODUCTION_PREFIX = f"{GCS_BUCKET}/plots"


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def main():
    parser = argparse.ArgumentParser(description="Backfill responsive image variants in GCS")
    parser.add_argument("--dry-run", action="store_true", help="List images without processing")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N images")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N images (0 = all)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if plot_800.webp already exists")
    args = parser.parse_args()

    # List all plot.png files in GCS production
    print("Listing plot images in GCS...")
    result = run_cmd(["gsutil", "ls", f"{PRODUCTION_PREFIX}/**/plot.png"])
    plot_urls = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

    print(f"Found {len(plot_urls)} images total")

    # Apply offset and limit
    if args.offset:
        plot_urls = plot_urls[args.offset:]
        print(f"After offset={args.offset}: {len(plot_urls)} remaining")
    if args.limit:
        plot_urls = plot_urls[: args.limit]
        print(f"After limit={args.limit}: {len(plot_urls)} to process")

    if args.dry_run:
        print("\n[DRY RUN] Would generate responsive variants for:")
        for url in plot_urls[:20]:
            print(f"  {url}")
        if len(plot_urls) > 20:
            print(f"  ... and {len(plot_urls) - 20} more")
        return

    success = 0
    skipped = 0
    failed = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        for i, plot_url in enumerate(plot_urls, 1):
            # Extract path info: gs://pyplots-images/plots/area-basic/altair/plot.png
            gcs_dir = plot_url.rsplit("/plot.png", 1)[0]
            parts = plot_url.replace(f"{GCS_BUCKET}/", "").split("/")
            spec_id = parts[1]
            library = parts[2]

            print(f"[{i}/{len(plot_urls)}] {spec_id}/{library}...", end=" ", flush=True)

            # Optionally skip if variants already exist
            if args.skip_existing:
                check = run_cmd(["gsutil", "ls", f"{gcs_dir}/plot_800.webp"], check=False)
                if check.returncode == 0:
                    print("SKIP (exists)")
                    skipped += 1
                    continue

            try:
                # Download original
                local_plot = tmpdir / "plot.png"
                local_outdir = tmpdir / "out"
                local_outdir.mkdir(exist_ok=True)

                run_cmd(["gsutil", "cp", plot_url, str(local_plot)])

                # Generate responsive variants
                variants = create_responsive_variants(local_plot, local_outdir)

                # Upload all variants
                run_cmd([
                    "gsutil", "-m", "-h", "Cache-Control:public, max-age=604800",
                    "cp",
                    *[str(local_outdir / Path(v["path"]).name) for v in variants],
                    f"{gcs_dir}/",
                ])

                # Set public ACL
                run_cmd(
                    ["gsutil", "-m", "acl", "ch", "-u", "AllUsers:R", f"{gcs_dir}/plot*"],
                    check=False,
                )

                print(f"OK ({len(variants)} variants)")
                success += 1

                # Cleanup for next iteration
                for f in local_outdir.iterdir():
                    f.unlink()
                local_plot.unlink(missing_ok=True)

            except Exception as e:
                print(f"FAILED: {e}")
                failed += 1

    print(f"\nDone! Success: {success}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
