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


def test_run_theme_renders_preserves_dunder_file(tmp_path, monkeypatch):
    """Regression: highcharts/pygal impls use Path(__file__).parents[...] to
    resolve assets like node_modules. When we used to copy the impl into
    .regen-preview/{lib}/run_impl.py, __file__ pointed there and asset
    resolution broke. With `python -P <impl>`, __file__ stays at the
    original impl path."""
    monkeypatch.chdir(tmp_path)
    plots = tmp_path / "plots"
    expected_path = plots / "scatter-basic" / "implementations" / "python" / "altair.py"
    body = (
        "import os, pathlib\n"
        "theme = os.environ['ANYPLOT_THEME']\n"
        f"expected = pathlib.Path({str(expected_path)!r}).resolve()\n"
        "actual = pathlib.Path(__file__).resolve()\n"
        "assert actual == expected, f'__file__ moved! {actual} != {expected}'\n"
        "pathlib.Path(f'plot-{theme}.png').write_bytes(b'fake')\n"
    )
    _stub_impl(plots, "scatter-basic", "altair", body)
    result = run_theme_renders("scatter-basic", "altair")
    assert result.light_png.is_file()
    assert result.dark_png.is_file()


def test_run_theme_renders_avoids_self_import_collision(tmp_path, monkeypatch):
    """The impl file is named after its library (e.g. altair.py). Without
    python -P, sys.path[0] contains the impl's dir and `import altair`
    resolves to the local file. With -P, the install-tree package wins.

    We use the stdlib `json` module here (not `altair`) so the test runs
    in any Python env, even ones without the plotting extras installed.
    The collision behavior is identical: an impl named `json.py` would
    shadow the stdlib without -P."""
    monkeypatch.chdir(tmp_path)
    plots = tmp_path / "plots"
    body = (
        "import os, pathlib\n"
        "import json\n"
        # If shadowing happened, the local json.py would be re-executed and
        # there'd be no `loads` attribute. With -P, we get the stdlib.
        "assert hasattr(json, 'loads'), 'local json.py shadowed the stdlib'\n"
        "theme = os.environ['ANYPLOT_THEME']\n"
        "pathlib.Path(f'plot-{theme}.png').write_bytes(b'fake')\n"
    )
    _stub_impl(plots, "scatter-basic", "json", body)
    result = run_theme_renders("scatter-basic", "json")
    assert result.light_png.is_file()
