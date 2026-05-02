"""Tests for `agentic.workflows.modules.regen.render`."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic.workflows.modules.regen.render import _preview_dir, run_theme_renders


def _stub_impl(plots: Path, spec: str, library: str, body: str) -> Path:
    impl_dir = plots / spec / "implementations" / "python"
    impl_dir.mkdir(parents=True)
    impl = impl_dir / f"{library}.py"
    impl.write_text(body, encoding="utf-8")
    return impl


def test_run_theme_renders_creates_both_pngs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plots = tmp_path / "plots"
    # Implementation that writes plot-{light,dark}.png based on env var.
    body = (
        "import os, pathlib\n"
        "theme = os.environ['ANYPLOT_THEME']\n"
        "pathlib.Path(f'plot-{theme}.png').write_bytes(b'\\x89PNG\\r\\n\\x1a\\nfake')\n"
    )
    _stub_impl(plots, "scatter-basic", "altair", body)
    # Run with real subprocess but a no-op script — uses uv run python
    result = run_theme_renders("scatter-basic", "altair")
    assert result.light_png.is_file()
    assert result.dark_png.is_file()
    assert result.light_html is None
    assert result.dark_html is None


def test_run_theme_renders_clears_stale_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plots = tmp_path / "plots"
    _stub_impl(plots, "scatter-basic", "altair", "# does nothing\n")
    # Pre-populate stale artifacts in the preview dir
    preview = _preview_dir("scatter-basic", "altair")
    preview.mkdir(parents=True)
    (preview / "plot-light.png").write_bytes(b"stale")
    (preview / "plot-dark.png").write_bytes(b"stale")
    # The impl produces nothing — so after the wipe, both PNGs should be missing
    with pytest.raises(RuntimeError, match="plot-light.png not produced"):
        run_theme_renders("scatter-basic", "altair", max_retries=1)


def test_run_theme_renders_missing_impl_raises(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        run_theme_renders("does-not-exist", "altair", max_retries=1)


def test_run_theme_renders_retries_then_gives_up(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plots = tmp_path / "plots"
    # Impl that always raises
    _stub_impl(plots, "scatter-basic", "altair", "raise SystemExit(1)\n")
    with pytest.raises(RuntimeError, match="render failed for theme=light"):
        run_theme_renders("scatter-basic", "altair", max_retries=2)
