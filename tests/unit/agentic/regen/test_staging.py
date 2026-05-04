"""Tests for `agentic.workflows.modules.regen.staging`.

Staging shells out to `uv run python -m core.images ...` and `gsutil` —
both heavyweight and external. Patch subprocess and verify the call
sequence + path math.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agentic.workflows.modules.regen.staging import (
    _gsutil_cp_bundle,
    _process_and_responsive,
    _stage_path,
    stage_images_to_gcs,
)


def _populate_preview(plots: Path, spec: str, library: str, with_html: bool = True) -> Path:
    preview = plots / spec / "implementations" / "python" / ".regen-preview" / library
    preview.mkdir(parents=True)
    for theme in ("light", "dark"):
        (preview / f"plot-{theme}.png").write_bytes(b"fake png")
        if with_html:
            (preview / f"plot-{theme}.html").write_text("<html></html>", encoding="utf-8")
    # responsive variants the upload step expects to find
    for theme in ("light", "dark"):
        for size in ("400", "800", "1200"):
            (preview / f"plot-{theme}_{size}.png").write_bytes(b"fake")
            (preview / f"plot-{theme}_{size}.webp").write_bytes(b"fake")
        (preview / f"plot-{theme}.webp").write_bytes(b"fake")
    return preview


def test_stage_path_uses_python_segment():
    assert _stage_path("scatter-basic", "altair") == "gs://anyplot-images/staging/scatter-basic/python/altair"


def test_process_and_responsive_calls_core_images_for_theme(tmp_path):
    preview = tmp_path / ".regen-preview" / "altair"
    preview.mkdir(parents=True)
    (preview / "plot-light.png").write_bytes(b"fake")
    with patch("agentic.workflows.modules.regen.staging.subprocess") as sp:
        sp.run.return_value = None
        _process_and_responsive(preview, "light")
        cmds = [c.args[0] for c in sp.run.call_args_list]
        assert any("process" in cmd for cmd in cmds)
        assert any("responsive" in cmd for cmd in cmds)


def test_process_and_responsive_raises_on_missing_render(tmp_path):
    preview = tmp_path / ".regen-preview" / "altair"
    preview.mkdir(parents=True)
    # No plot-light.png present
    with pytest.raises(FileNotFoundError, match="missing render"):
        _process_and_responsive(preview, "light")


def test_gsutil_cp_bundle_includes_both_themes(tmp_path):
    preview = _populate_preview(tmp_path / "plots", "scatter-basic", "altair")
    with patch("agentic.workflows.modules.regen.staging.subprocess") as sp:
        sp.run.return_value = None
        _gsutil_cp_bundle(preview, "gs://anyplot-images/staging/x/python/altair")
    cmd = sp.run.call_args.args[0]
    targets = [p for p in cmd if isinstance(p, str) and p.startswith(str(preview))]
    # At least one light png + one dark png + variants
    assert any("plot-light.png" in p for p in targets)
    assert any("plot-dark.png" in p for p in targets)
    assert any("plot-light.webp" in p for p in targets)
    assert any("plot-dark.webp" in p for p in targets)
    # Cache header is set
    assert "Cache-Control:public, max-age=604800" in cmd


def test_stage_images_to_gcs_full_pipeline(tmp_path, monkeypatch):
    plots = tmp_path / "plots"
    _populate_preview(plots, "scatter-basic", "altair")
    monkeypatch.chdir(tmp_path)

    with patch("agentic.workflows.modules.regen.staging.subprocess") as sp:
        sp.run.return_value = None
        result = stage_images_to_gcs("scatter-basic", "altair", plots_root=plots)
    assert result == "gs://anyplot-images/staging/scatter-basic/python/altair"
    cmds = [c.args[0] for c in sp.run.call_args_list]
    # process+responsive for both themes (4 invocations)
    assert sum(1 for c in cmds if "process" in c and "core.images" in c) == 2
    assert sum(1 for c in cmds if "responsive" in c and "core.images" in c) == 2
    # one batch gsutil cp
    assert sum(1 for c in cmds if c[:1] == ["gsutil"] and "cp" in c) >= 1
    # html upload for both themes (interactive lib)
    html_uploads = [
        c for c in cmds if c[:1] == ["gsutil"] and any("plot-light.html" in p or "plot-dark.html" in p for p in c)
    ]
    assert len(html_uploads) >= 2


def test_stage_images_to_gcs_missing_preview_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="preview dir does not exist"):
        stage_images_to_gcs("nonexistent", "altair", plots_root=tmp_path)
