"""Tests for core.canvas — the canvas gate and the PNG auto-reject checks.

The parity tests run the inline script of impl-review.yml's "Canvas dimension
gate" step on the same PNG as ``core.canvas`` and require identical lines and
an identical defect file: until the workflow switches to the module, the two
must not drift. Fixture PNGs are generated in ``tmp_path``; none is committed.
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image

from core.canvas import (
    LANDSCAPE,
    LIKELY_CAUSES,
    MAX_BLANK_RATIO,
    MIN_PLOT_BYTES,
    PNG_SIGNATURE,
    SQUARE,
    TOLERANCE,
    AutoRejectResult,
    NotAPngError,
    blank_ratio,
    check_blank,
    check_canvas,
    check_format,
    check_png,
    dominant_color,
    is_blank_png,
    is_png,
    likely_cause,
    main,
    nearest_target,
    png_size,
)
from core.constants import LIBRARIES_METADATA
from core.defects import DEFECT, defect_ids, weakness_class


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "impl-review.yml"
GATE_STEP = "Canvas dimension gate"
WORKFLOW_GATE_FILE = "/tmp/anyplot-canvas-gate.txt"


def _write_png(path: Path, width: int, height: int) -> Path:
    """A bilevel PNG of the given size: tiny on disk, any size the gate needs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("1", (width, height)).save(path)
    return path


def _workflow_script() -> str:
    """The Python heredoc of the workflow's canvas gate step."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = [s for job in workflow["jobs"].values() for s in job.get("steps", []) if s.get("name") == GATE_STEP]
    assert len(steps) == 1, f"expected exactly one {GATE_STEP!r} step"
    run = steps[0]["run"]
    start = run.index("python3 <<'PY'\n") + len("python3 <<'PY'\n")
    return run[start : run.index("\nPY", start)]


def _run_workflow_gate(tmp_path: Path, width: int, height: int, library: str, attempt: str) -> tuple[list[str], str]:
    """Run the workflow's script on a PNG of that size; its stdout lines and gate file ('' when none)."""
    work = tmp_path / "workflow"
    _write_png(work / "plot_images" / "plot-light.png", width, height)
    gate_file = tmp_path / "workflow-gate.txt"
    script = _workflow_script()
    assert WORKFLOW_GATE_FILE in script
    script = script.replace(WORKFLOW_GATE_FILE, str(gate_file))
    env = {**os.environ, "LIBRARY": library, "ATTEMPT": attempt}
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=work, env=env, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines(), gate_file.read_text(encoding="utf-8") if gate_file.exists() else ""


def _run_module_gate(
    tmp_path: Path, width: int, height: int, library: str, attempt: str, capsys: pytest.CaptureFixture[str]
) -> tuple[int, list[str], str]:
    """``python -m core.canvas`` with the workflow's arguments: exit code, stdout lines, gate file."""
    png = _write_png(tmp_path / "module" / "plot-light.png", width, height)
    gate_file = tmp_path / "module-gate.txt"
    code = main([str(png), "--library", library, "--attempt", attempt, "--out", str(gate_file)])
    lines = capsys.readouterr().out.splitlines()
    return code, lines, gate_file.read_text(encoding="utf-8") if gate_file.exists() else ""


# One size per situation the gate distinguishes, spread over the library
# families (static Python, Vega, browser harness, R, Julia).
PARITY_CASES = [
    pytest.param("matplotlib", 3200, 1800, id="exact-landscape"),
    pytest.param("ggplot2", 2400, 2400, id="exact-square"),
    pytest.param("seaborn", 3216, 1784, id="landscape-at-tolerance"),
    pytest.param("plotnine", 2390, 2410, id="square-within-tolerance"),
    pytest.param("matplotlib", 4755, 2655, id="bbox-inches-tight"),
    pytest.param("plotly", 3150, 1800, id="landscape-width-short"),
    pytest.param("bokeh", 3200, 1840, id="landscape-height-over"),
    pytest.param("altair", 2420, 2380, id="square-drift"),
    pytest.param("highcharts", 1600, 900, id="unscaled-landscape-nearer-square"),
    pytest.param("letsplot", 3150, 3800, id="portrait-nearer-landscape"),
    pytest.param("d3", 2400, 2417, id="square-height-one-over-tolerance"),
    pytest.param("makie", 3600, 1800, id="landscape-width-over"),
    pytest.param("pygal", 3217, 1817, id="both-axes-over"),
    pytest.param("not-a-library", 3000, 1700, id="unknown-library"),
]


class TestWorkflowParity:
    @pytest.mark.parametrize(("library", "width", "height"), PARITY_CASES)
    def test_cli_prints_and_writes_what_the_workflow_does(self, tmp_path, capsys, library, width, height):
        wf_lines, wf_file = _run_workflow_gate(tmp_path, width, height, library, "2")
        code, lines, gate_file = _run_module_gate(tmp_path, width, height, library, "2", capsys)

        # The workflow's warning names its own gate file; the CLI names --out.
        assert [line.replace(str(tmp_path / "workflow-gate.txt"), "GATE") for line in wf_lines] == [
            line.replace(str(tmp_path / "module-gate.txt"), "GATE") for line in lines
        ]
        assert gate_file == wf_file
        assert code == (1 if wf_file else 0)

    @pytest.mark.parametrize(("library", "width", "height"), PARITY_CASES)
    def test_verdict_matches_the_workflow(self, tmp_path, library, width, height):
        wf_lines, wf_file = _run_workflow_gate(tmp_path, width, height, library, "1")
        verdict = check_canvas(width, height, library)
        assert wf_lines[0] == verdict.notice("1")
        assert (verdict.defect_line or "") == wf_file

    def test_every_library_hint_matches_the_workflow(self, tmp_path):
        for library in LIKELY_CAUSES:
            _, wf_file = _run_workflow_gate(tmp_path, 4755, 2655, library, "1")
            assert likely_cause(library) in wf_file, library
            assert check_canvas(4755, 2655, library).defect_line == wf_file


class TestCheckCanvas:
    def test_bbox_inches_tight_line_is_pinned(self):
        # The exact wording impl-repair reads; any change here is a change to the repair feedback.
        assert check_canvas(4755, 2655, "matplotlib").defect_line == (
            "VQ-05 (both): Canvas dimensions drifted from required target. "
            "Actual: 4755×2655. Closest valid target: 3200×1800 (±16 px tolerance). "
            "Signed delta: +1555 × +855 — width is 1555 px over; height is 855 px over. "
            "Most likely cause: `bbox_inches='tight'` on `savefig` — remove it (default `bbox_inches=None`). "
            "Re-render at exactly 3200×1800; the post-render gate enforces this."
        )

    def test_pass_notice_is_pinned(self):
        verdict = check_canvas(3210, 1795, "seaborn")
        assert verdict.notice("3") == (
            "::notice::canvas_gate library=seaborn status=pass actual=3210x1795 target=3200x1800 delta=+10x-5 attempt=3"
        )
        assert verdict.notice() == (
            "::notice::canvas_gate library=seaborn status=pass actual=3210x1795 target=3200x1800 delta=+10x-5"
        )

    @pytest.mark.parametrize(
        ("width", "height", "target"),
        [
            (3200, 1800, LANDSCAPE),
            (2400, 2400, SQUARE),
            (4755, 2655, LANDSCAPE),
            (1600, 900, SQUARE),
            (100, 100, SQUARE),
        ],
    )
    def test_nearest_target(self, width, height, target):
        assert nearest_target(width, height) == target
        assert check_canvas(width, height, "matplotlib").target == target

    @pytest.mark.parametrize("offset", [-TOLERANCE, 0, TOLERANCE])
    def test_tolerance_is_inclusive(self, offset):
        assert check_canvas(3200 + offset, 1800 - offset, "matplotlib").ok
        assert check_canvas(2400 - offset, 2400 + offset, "matplotlib").ok

    @pytest.mark.parametrize(("dw", "dh"), [(TOLERANCE + 1, 0), (0, -TOLERANCE - 1), (-TOLERANCE - 1, TOLERANCE + 1)])
    def test_one_pixel_past_tolerance_fails(self, dw, dh):
        verdict = check_canvas(3200 + dw, 1800 + dh, "plotly")
        assert not verdict.ok
        assert verdict.status == "fail"
        assert verdict.delta == (dw, dh)

    def test_pass_has_no_defect_line(self):
        verdict = check_canvas(2400, 2400, "d3")
        assert verdict.ok and verdict.status == "pass" and verdict.delta == (0, 0)
        assert verdict.defect_line is None

    def test_defect_line_is_a_grammar_valid_vq05_line(self):
        line = check_canvas(3150, 1800, "plotly").defect_line
        assert weakness_class(line) == DEFECT
        assert defect_ids(line) == ["VQ-05"]
        assert "width is 50 px short" in line

    def test_orientation_notes(self):
        landscape_on_square = check_canvas(1600, 900, "highcharts").defect_line
        assert "rendered a landscape canvas but the closest target is square" in landscape_on_square
        portrait_on_landscape = check_canvas(3150, 3800, "letsplot").defect_line
        assert "rendered a portrait/square canvas but the closest target is landscape" in portrait_on_landscape
        assert "reconsider orientation" not in check_canvas(3300, 1800, "plotly").defect_line

    def test_every_catalogue_library_has_a_hint(self):
        assert set(LIKELY_CAUSES) == {lib["id"] for lib in LIBRARIES_METADATA}

    def test_hint_fallbacks(self):
        assert likely_cause("newlib") == "Review `prompts/library/newlib.md` 'Canvas — hard rule' section."
        # The workflow always passes a library; the CLI may not.
        assert "prompts/library/`" in likely_cause("")


class TestPngReader:
    def test_reports_size(self, tmp_path):
        png = _write_png(tmp_path / "a.png", 3200, 1800)
        assert is_png(png)
        assert png_size(png) == (3200, 1800)
        verdict = check_png(png, "matplotlib")
        assert (verdict.width, verdict.height, verdict.ok) == (3200, 1800, True)

    def test_rejects_an_image_that_is_not_a_png(self, tmp_path):
        jpeg = tmp_path / "plot-light.png"
        Image.new("RGB", (3200, 1800), "white").save(jpeg, format="JPEG")
        assert not is_png(jpeg)
        with pytest.raises(NotAPngError):
            check_png(jpeg, "matplotlib")

    def test_rejects_a_text_file_and_a_missing_file(self, tmp_path):
        text = tmp_path / "plot.png"
        text.write_text("not a png", encoding="utf-8")
        assert not is_png(text)
        assert not is_png(tmp_path / "missing.png")
        with pytest.raises(NotAPngError):
            check_png(text, "matplotlib")


class TestCli:
    def test_pass_exits_zero_and_removes_a_stale_gate_file(self, tmp_path, capsys):
        png = _write_png(tmp_path / "plot-light.png", 2400, 2400)
        out = tmp_path / "gate.txt"
        out.write_text("stale", encoding="utf-8")
        assert main([str(png), "--library", "ggplot2", "--out", str(out)]) == 0
        assert not out.exists()
        assert capsys.readouterr().out.splitlines() == [
            "::notice::canvas_gate library=ggplot2 status=pass actual=2400x2400 target=2400x2400 delta=+0x+0"
        ]

    def test_drift_without_out_prints_the_line(self, tmp_path, capsys):
        png = _write_png(tmp_path / "plot-light.png", 4755, 2655)
        assert main([str(png), "--library", "matplotlib"]) == 1
        lines = capsys.readouterr().out.splitlines()
        assert lines[1] == "::warning::Canvas gate FAILED: " + check_canvas(4755, 2655, "matplotlib").defect_line

    def test_not_a_png_exits_two(self, tmp_path, capsys):
        bad = tmp_path / "plot-light.png"
        bad.write_bytes(b"GIF89a")
        assert main([str(bad)]) == 2
        assert capsys.readouterr().out.startswith("::error::canvas_gate cannot read")

    def test_runs_as_a_module(self, tmp_path):
        png = _write_png(tmp_path / "plot-light.png", 3300, 1800)
        result = subprocess.run(
            [sys.executable, "-m", "core.canvas", str(png), "--library", "plotly"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1, result.stderr
        assert "status=fail actual=3300x1800" in result.stdout


def _noisy_png(path: Path, size: tuple[int, int], background: str, noise_share: float, seed: int = 7) -> Path:
    """A ``background`` PNG whose left ``noise_share`` of columns is random RGB (incompressible)."""
    width, height = size
    img = Image.new("RGB", size, background)
    noise_width = round(width * noise_share)
    if noise_width:
        data = random.Random(seed).randbytes(noise_width * height * 3)
        img.paste(Image.frombytes("RGB", (noise_width, height), data), (0, 0))
    img.save(path)
    return path


class TestAutoReject:
    def test_format_passes_a_png(self, tmp_path):
        result = check_format(_write_png(tmp_path / "plot-light.png", 10, 10))
        assert result == AutoRejectResult("AR-07", True, "Correct format: PNG")

    def test_format_fails_html_and_missing(self, tmp_path):
        html = tmp_path / "plot-light.html"
        html.write_text("<html></html>", encoding="utf-8")
        assert not check_format(html).passed
        assert check_format(html).code == "AR-07"
        assert not check_format(tmp_path / "nothing.png").passed

    def test_blank_too_small(self, tmp_path):
        png = tmp_path / "plot-light.png"
        Image.new("RGB", (400, 300), "white").save(png)
        assert png.stat().st_size < MIN_PLOT_BYTES
        result = check_blank(png)
        assert result.code == "AR-04" and not result.passed
        assert result.message.startswith("Plot too small: ")
        assert is_blank_png(png)

    @pytest.mark.parametrize(("page", "hex_code"), [("#FAF8F1", "#FAF8F1"), ("#1A1A17", "#1A1A17")])
    def test_blank_full_canvas_in_either_theme(self, tmp_path, page, hex_code):
        # A plain full canvas is about 20 KB: past the size rule, caught by the ratio. The
        # light page is not "white" (a channel at 241), so only a one-color rule sees it.
        png = tmp_path / "plot.png"
        Image.new("RGB", LANDSCAPE, page).save(png)
        assert png.stat().st_size >= MIN_PLOT_BYTES
        assert check_blank(png) == AutoRejectResult("AR-04", False, f"Plot is 100% one color ({hex_code})")

    @pytest.mark.parametrize("page", ["#FAF8F1", "#1A1A17"])
    def test_blank_mostly_one_color(self, tmp_path, page):
        png = _noisy_png(tmp_path / "plot.png", (800, 600), page, 0.03)
        assert png.stat().st_size >= MIN_PLOT_BYTES
        result = check_blank(png)
        assert not result.passed
        assert result.message == f"Plot is 97% one color ({page})"
        assert is_blank_png(png)

    @pytest.mark.parametrize("page", ["#FAF8F1", "#1A1A17"])
    def test_sparse_content_passes(self, tmp_path, page):
        # A sparse line chart covers about 6 % of the canvas (94 % page in the catalogue's sparsest renders).
        png = _noisy_png(tmp_path / "plot.png", (800, 600), page, 0.06)
        result = check_blank(png)
        assert result.passed
        assert result.message.startswith("Plot OK (") and result.message.endswith("KB)")
        assert not is_blank_png(png)

    def test_thresholds_are_parameters(self, tmp_path):
        png = _noisy_png(tmp_path / "plot.png", (800, 600), "white", 0.03)
        assert check_blank(png, max_blank_ratio=0.98).passed
        assert not check_blank(png, min_bytes=png.stat().st_size + 1).passed
        assert MAX_BLANK_RATIO == 0.95

    def test_blank_missing_file_fails(self, tmp_path):
        assert not check_blank(tmp_path / "plot-light.png").passed

    def test_blank_rejects_a_large_non_png(self, tmp_path):
        fake = tmp_path / "plot.png"
        fake.write_bytes(b"x" * MIN_PLOT_BYTES)
        assert check_blank(fake) == AutoRejectResult("AR-04", False, "Not a PNG: plot.png")

    def test_dominant_color_is_an_exact_count(self):
        rng = np.random.default_rng(3)
        arr = rng.choice(np.array([0, 59, 250, 255], dtype=np.uint8), size=(40, 50, 3))
        img = Image.fromarray(arr, "RGB")
        counts = Counter(map(tuple, arr.reshape(-1, 3).tolist()))
        color, count = counts.most_common(1)[0]
        assert dominant_color(img) == (color, count / 2000)
        assert blank_ratio(img) == count / 2000

    def test_dominant_color_ignores_alpha_and_mode(self):
        assert dominant_color(Image.new("RGBA", (4, 4), (10, 20, 30, 0))) == ((10, 20, 30), 1.0)
        assert dominant_color(Image.new("L", (4, 4), 200)) == ((200, 200, 200), 1.0)
        assert dominant_color(Image.new("RGB", (0, 0))) == ((0, 0, 0), 1.0)

    def test_png_signature(self):
        assert PNG_SIGNATURE == b"\x89PNG\r\n\x1a\n"
