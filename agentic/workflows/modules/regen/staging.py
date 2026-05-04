"""Optimize + responsive-resize both theme renders, then upload to GCS staging.

Replaces regen.md step 2i. Mirrors the bundle that `impl-generate.yml`
uploads (`plot-light*.{png,webp}` + `plot-dark*.{png,webp}` + optional
`plot-{light,dark}.html`) and stages it under
`gs://anyplot-images/staging/{spec_id}/python/{library}/`.

ACL set failures (uniform-IAM buckets) are intentionally swallowed —
matches the behavior of the inline shell version and of `impl-generate.yml`.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path


logger = logging.getLogger(__name__)

_GCS_BUCKET = "anyplot-images"
_CACHE_HEADER = "Cache-Control:public, max-age=604800"


def _stage_path(spec_id: str, library: str) -> str:
    return f"gs://{_GCS_BUCKET}/staging/{spec_id}/python/{library}"


def _process_and_responsive(preview_dir: Path, theme: str) -> None:
    """Optimize the theme PNG in place + emit responsive variants."""
    plot_png = preview_dir / f"plot-{theme}.png"
    if not plot_png.is_file():
        raise FileNotFoundError(f"missing render: {plot_png}")
    subprocess.run(["uv", "run", "python", "-m", "core.images", "process", str(plot_png), str(plot_png)], check=True)
    subprocess.run(
        ["uv", "run", "python", "-m", "core.images", "responsive", str(plot_png), str(preview_dir) + "/"], check=True
    )


def _gsutil_cp_bundle(preview_dir: Path, staging_path: str) -> None:
    """Single multi-file gsutil cp. Globs are expanded by the shell, so we list explicitly."""
    targets = []
    for pattern in ("plot-light*.png", "plot-light*.webp", "plot-dark*.png", "plot-dark*.webp"):
        targets.extend(sorted(preview_dir.glob(pattern)))
    if not targets:
        raise FileNotFoundError(f"no theme images to upload in {preview_dir}")
    cmd = ["gsutil", "-m", "-h", _CACHE_HEADER, "cp"]
    cmd.extend(str(p) for p in targets)
    cmd.append(f"{staging_path}/")
    subprocess.run(cmd, check=True)


def _gsutil_make_public(staging_path: str) -> None:
    subprocess.run(
        ["gsutil", "-m", "acl", "ch", "-u", "AllUsers:R", f"{staging_path}/plot-light*", f"{staging_path}/plot-dark*"],
        check=False,
    )


def _upload_html(preview_dir: Path, staging_path: str) -> None:
    for theme in ("light", "dark"):
        html = preview_dir / f"plot-{theme}.html"
        if not html.is_file():
            continue
        subprocess.run(
            ["gsutil", "-h", _CACHE_HEADER, "cp", str(html), f"{staging_path}/plot-{theme}.html"], check=True
        )
        subprocess.run(["gsutil", "acl", "ch", "-u", "AllUsers:R", f"{staging_path}/plot-{theme}.html"], check=False)


def stage_images_to_gcs(spec_id: str, library: str, plots_root: Path = Path("plots")) -> str:
    """Process + upload both themes. Returns the staging GCS path."""
    preview_dir = plots_root / spec_id / "implementations" / "python" / ".regen-preview" / library
    if not preview_dir.is_dir():
        raise FileNotFoundError(f"preview dir does not exist: {preview_dir}")

    for theme in ("light", "dark"):
        _process_and_responsive(preview_dir, theme)

    staging_path = _stage_path(spec_id, library)
    _gsutil_cp_bundle(preview_dir, staging_path)
    _gsutil_make_public(staging_path)
    _upload_html(preview_dir, staging_path)
    return staging_path
