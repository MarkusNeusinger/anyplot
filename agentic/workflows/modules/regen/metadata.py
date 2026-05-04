"""Build + write `metadata/python/{library}.yaml` from a `QualityEval`.

Replaces regen.md step 2g. The YAML structure mirrors what
`impl-generate.yml` writes (`preview_url_light`/`preview_url_dark`,
`preview_html_light`/`preview_html_dark`, full `review.criteria_checklist`).
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import yaml

from . import QualityEval


# library → pip package name (where they differ)
_PIP_PACKAGE = {"letsplot": "lets-plot", "highcharts": "highcharts-core"}

# Libraries that emit interactive HTML in addition to PNG
_INTERACTIVE_LIBS = {"plotly", "bokeh", "altair", "highcharts", "pygal", "letsplot"}

_GCS_BASE = "https://storage.googleapis.com/anyplot-images/plots"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _python_version() -> str:
    out = subprocess.check_output(["uv", "run", "python", "--version"], text=True).strip()
    # "Python 3.13.12"
    return out.split()[-1]


def _library_version(library: str) -> str:
    pkg = _PIP_PACKAGE.get(library, library)
    try:
        return version(pkg)
    except PackageNotFoundError:
        # Fallback to `uv run python -c` in case importlib metadata isn't available
        try:
            out = subprocess.check_output(
                ["uv", "run", "python", "-c", f"from importlib.metadata import version; print(version({pkg!r}))"],
                text=True,
            ).strip()
            return out
        except subprocess.CalledProcessError:
            return "unknown"


def _generated_by() -> str:
    """Best-effort detection of the model running this regen.

    Honors `CLAUDE_MODEL` env var, otherwise records `local-regen` so the
    metadata is self-describing.
    """
    import os

    return os.environ.get("CLAUDE_MODEL", "local-regen")


def _preview_urls(spec_id: str, library: str) -> dict[str, str | None]:
    base = f"{_GCS_BASE}/{spec_id}/python/{library}"
    has_html = library in _INTERACTIVE_LIBS
    return {
        "preview_url_light": f"{base}/plot-light.png",
        "preview_url_dark": f"{base}/plot-dark.png",
        "preview_html_light": f"{base}/plot-light.html" if has_html else None,
        "preview_html_dark": f"{base}/plot-dark.html" if has_html else None,
    }


def _read_existing(metadata_path: Path) -> dict[str, Any]:
    if not metadata_path.is_file():
        return {}
    try:
        return yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def _review_block(quality: QualityEval) -> dict[str, Any]:
    return {
        "strengths": list(quality.strengths),
        "weaknesses": list(quality.weaknesses),
        "image_description": quality.image_description,
        "criteria_checklist": dict(quality.criteria_checklist),
        "verdict": quality.verdict,
    }


def build_metadata_dict(spec_id: str, library: str, quality: QualityEval, metadata_path: Path) -> dict[str, Any]:
    existing = _read_existing(metadata_path)

    created = existing.get("created") or _now_iso()
    issue = existing.get("issue", 0)
    workflow_run = existing.get("workflow_run", 0)
    impl_tags = existing.get("impl_tags") or {
        "dependencies": [],
        "techniques": [],
        "patterns": [],
        "dataprep": [],
        "styling": [],
    }

    data: dict[str, Any] = {
        "library": library,
        "language": "python",
        "specification_id": spec_id,
        "created": created,
        "updated": _now_iso(),
        "generated_by": _generated_by(),
        "workflow_run": workflow_run,
        "issue": issue,
        "python_version": _python_version(),
        "library_version": _library_version(library),
        **_preview_urls(spec_id, library),
        "quality_score": int(quality.score),
        "impl_tags": impl_tags,
        "review": _review_block(quality),
    }
    return data


def write_metadata(spec_id: str, library: str, quality: QualityEval, plots_root: Path = Path("plots")) -> Path:
    metadata_path = plots_root / spec_id / "metadata" / "python" / f"{library}.yaml"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    data = build_metadata_dict(spec_id, library, quality, metadata_path)
    metadata_path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return metadata_path


def update_impl_header(spec_id: str, library: str, score: int, plots_root: Path = Path("plots")) -> None:
    """Rewrite the docstring's `Quality:` and `Updated:` lines to match the score."""
    impl = plots_root / spec_id / "implementations" / "python" / f"{library}.py"
    if not impl.is_file():
        return
    text = impl.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_line = f"Quality: {int(score)}/100 | Updated: {today}"
    import re

    text = re.sub(r"^Quality:.*$", new_line, text, count=1, flags=re.MULTILINE)
    impl.write_text(text, encoding="utf-8")


__all__ = [
    "build_metadata_dict",
    "write_metadata",
    "update_impl_header",
    "asdict",  # re-export for CLI's JSON helpers
]
