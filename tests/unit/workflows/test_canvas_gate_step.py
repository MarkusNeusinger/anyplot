"""The canvas gate in impl-review.yml on both theme renders (review plan step P7).

"Canvas dimension gate" measures plot-light.png and plot-dark.png against the
two canonical canvases (3200x1800, 2400x2400, ±16 px) and requires both on the
same one. On a miss it writes one VQ-05 defect line per render that missed to
/tmp/anyplot-canvas-gate.txt, which the review copies into its weaknesses and
the regen gate reads as `canvas_failed`. The step never fails the job for a
render it measured: impl-repair is dispatched by the verdict step only.

A light render that does not open stops the step, and with a dark render of
the light's size the light verdict and its defect line are those of core.canvas
for one render; "Verify both theme renders exist" stops the job on a missing
file before the gate runs. A missing or unreadable dark render is a gate
failure, because impl-generate never stages a pair without both renders.

The whole step script runs here under `bash -e` (what Actions runs it with)
and `bash -eo pipefail`, on small generated PNGs, with a stub `pip` and the
test interpreter as `python3`; the gate file goes to the test's own directory.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from automation.scripts import canvas_gate_report, regen_gate
from core.canvas import check_canvas, likely_cause
from tests.unit.workflows.test_pipeline_retry_gaps import _step
from tests.unit.workflows.test_render_hash_steps import SHELL_IDS, SHELLS


STEP = "Canvas dimension gate"
GATE_FILE = "/tmp/anyplot-canvas-gate.txt"
LANDSCAPE = (3200, 1800)
SQUARE = (2400, 2400)


def _png(path: Path, size: tuple[int, int]) -> None:
    """A bilevel PNG: tiny on disk, any size the gate needs."""
    Image.new("1", size).save(path)


class Gate:
    """One run of the step: its exit code, stdout lines and gate file."""

    def __init__(self, tmp_path: Path, shell: list[str]):
        self.tmp = tmp_path
        self.shell = shell
        self.images = tmp_path / "work" / "plot_images"
        self.images.mkdir(parents=True)
        self.gate = tmp_path / "anyplot-canvas-gate.txt"
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        for name, body in (("pip", "exit 0\n"), ("python3", f'exec "{sys.executable}" "$@"\n')):
            stub = bin_dir / name
            stub.write_text("#!/bin/sh\n" + body, encoding="utf-8")
            stub.chmod(0o755)
        self.path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

    def light(self, size: tuple[int, int]) -> Gate:
        _png(self.images / "plot-light.png", size)
        return self

    def dark(self, size: tuple[int, int]) -> Gate:
        _png(self.images / "plot-dark.png", size)
        return self

    def run(self, library: str = "matplotlib", attempt: str = "1") -> subprocess.CompletedProcess[str]:
        script = str(_step("impl-review.yml", STEP)["run"])
        assert "${{" not in script
        assert GATE_FILE in script
        script = script.replace(GATE_FILE, str(self.gate))
        env = {**os.environ, "PATH": self.path, "LIBRARY": library, "ATTEMPT": attempt}
        return subprocess.run(
            [*self.shell, script], cwd=self.images.parent, env=env, capture_output=True, text=True, check=False
        )

    def notices(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        return [line for line in result.stdout.splitlines() if line.startswith("::notice::canvas_gate ")]

    def weaknesses(self) -> list[str]:
        return self.gate.read_text(encoding="utf-8").split("\n") if self.gate.exists() else []


@pytest.fixture(params=SHELLS, ids=SHELL_IDS)
def gate(request, tmp_path) -> Gate:
    return Gate(tmp_path, request.param)


def _fields(notice: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in notice.removeprefix("::notice::canvas_gate ").split())


def _render(line: str) -> str:
    """The render tag of a defect line, as the regen gate reads it."""
    match = regen_gate.DEFECT_RE.match(line)
    assert match, line
    assert regen_gate.defect_ids(line) == ["VQ-05"], line
    return match.group("render")


class TestBothRendersFine:
    def test_same_size_passes_and_removes_a_stale_gate_file(self, gate):
        gate.gate.write_text("stale", encoding="utf-8")
        result = gate.light(LANDSCAPE).dark(LANDSCAPE).run(attempt="2")
        assert result.returncode == 0, result.stderr
        assert gate.notices(result) == [
            "::notice::canvas_gate library=matplotlib status=pass actual=3200x1800 target=3200x1800 "
            "delta=+0x+0 attempt=2 light=pass dark=pass dark_actual=3200x1800 dark_target=3200x1800 "
            "dark_delta=+0x+0 same_target=yes"
        ]
        assert not gate.gate.exists()
        assert "::warning::" not in result.stdout

    def test_both_within_tolerance_of_one_target_pass(self, gate):
        result = gate.light((3216, 1784)).dark((3190, 1810)).run()
        assert result.returncode == 0, result.stderr
        fields = _fields(gate.notices(result)[0])
        assert (fields["status"], fields["light"], fields["dark"], fields["same_target"]) == (
            "pass",
            "pass",
            "pass",
            "yes",
        )
        assert fields["dark_delta"] == "-10x+10"
        assert not gate.gate.exists()

    def test_square_pair_passes(self, gate):
        result = gate.light(SQUARE).dark(SQUARE).run(library="ggplot2")
        assert result.returncode == 0, result.stderr
        assert _fields(gate.notices(result)[0])["status"] == "pass"


class TestDarkFails:
    def test_dark_off_canvas(self, gate):
        result = gate.light(LANDSCAPE).dark((3000, 1800)).run(library="plotly")
        assert result.returncode == 0, result.stderr
        notice = gate.notices(result)[0]
        assert notice.startswith(
            "::notice::canvas_gate library=plotly status=fail actual=3200x1800 target=3200x1800 delta=+0x+0 attempt=1 "
        )
        assert notice.endswith(
            "light=pass dark=fail dark_actual=3000x1800 dark_target=3200x1800 dark_delta=-200x+0 same_target=yes"
        )
        [line] = gate.weaknesses()
        assert _render(line) == "dark"
        assert line.startswith(
            "VQ-05 (dark): Canvas dimensions drifted from required target. Actual: 3000×1800. "
            "Closest valid target: 3200×1800 (±16 px tolerance). Signed delta: -200 × +0 — width is 200 px short."
        )
        assert likely_cause("plotly") in line
        assert "plot-light.png is 3200×1800, on target, so a size or save option probably depends on the theme" in line
        assert line.endswith("Re-render at exactly 3200×1800; the post-render gate enforces this.")
        assert f"::warning::Canvas gate FAILED — wrote synthetic weakness to {gate.gate}: {line}" in result.stdout

    def test_dark_on_the_other_canonical_canvas(self, gate):
        result = gate.light(LANDSCAPE).dark(SQUARE).run(library="letsplot")
        assert result.returncode == 0, result.stderr
        fields = _fields(gate.notices(result)[0])
        assert (fields["status"], fields["light"], fields["dark"], fields["same_target"]) == (
            "fail",
            "pass",
            "pass",
            "no",
        )
        assert (fields["dark_actual"], fields["dark_target"], fields["dark_delta"]) == (
            "2400x2400",
            "2400x2400",
            "+0x+0",
        )
        [line] = gate.weaknesses()
        assert _render(line) == "dark"
        assert line.startswith("VQ-05 (dark): plot-dark.png is not on the canvas of plot-light.png. ")
        assert "Actual: 2400×2400, closest valid target 2400×2400; plot-light.png is 3200×1800" in line
        assert (
            "Signed delta to the light render's target: -800 × +600 — width is 800 px short; height is 600 px over."
            in line
        )
        assert "Likely cause: the two theme runs draw different canvases" in line

    def test_dark_missing(self, gate):
        result = gate.light(LANDSCAPE).run()
        assert result.returncode == 0, result.stderr
        assert gate.notices(result) == [
            "::notice::canvas_gate library=matplotlib status=fail actual=3200x1800 target=3200x1800 "
            "delta=+0x+0 attempt=1 light=pass dark=missing"
        ]
        [line] = gate.weaknesses()
        assert _render(line) == "dark"
        assert line.startswith("VQ-05 (dark): plot-dark.png is missing; plot-light.png is 3200×1800. ")
        assert "Both theme renders are required" in line
        assert line.endswith("Render both themes at exactly 3200×1800; the post-render gate enforces this.")

    @pytest.mark.parametrize(
        "content", [b"", b"not a png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 8], ids=["empty", "text", "header-only"]
    )
    def test_dark_unreadable(self, gate, content):
        gate.light(SQUARE)
        (gate.images / "plot-dark.png").write_bytes(content)
        result = gate.run()
        assert result.returncode == 0, result.stderr
        notice = gate.notices(result)[0]
        assert notice.endswith("attempt=1 light=pass dark=unreadable")
        assert _fields(notice)["status"] == "fail"
        [line] = gate.weaknesses()
        assert _render(line) == "dark"
        assert line.startswith("VQ-05 (dark): plot-dark.png does not open as an image (")
        assert "\n" not in line
        assert "Render both themes at exactly 2400×2400" in line

    def test_dark_that_is_a_directory_is_unreadable(self, gate):
        gate.light(LANDSCAPE)
        (gate.images / "plot-dark.png").mkdir()
        result = gate.run()
        assert result.returncode == 0, result.stderr
        assert gate.notices(result)[0].endswith("light=pass dark=unreadable")
        assert gate.weaknesses()[0].startswith("VQ-05 (dark): plot-dark.png does not open as an image (")

    def test_javascript_keeps_the_harness_hint_for_the_dark_render(self, gate):
        result = gate.light(LANDSCAPE).dark((3200, 1661)).run(library="highcharts")
        assert result.returncode == 0, result.stderr
        [line] = gate.weaknesses()
        assert _render(line) == "dark"
        assert likely_cause("highcharts") in line
        assert "The harness owns exact pixels" in line


class TestLightAsBefore:
    """With a dark render of the same size, the light render's notice fields and line are core.canvas's."""

    @pytest.mark.parametrize(
        ("library", "size"),
        [("matplotlib", (4755, 2655)), ("altair", (2420, 2380)), ("highcharts", (1600, 900)), ("newlib", (3000, 1700))],
    )
    def test_light_drift_writes_the_line_of_before(self, gate, library, size):
        result = gate.light(size).dark(size).run(library=library, attempt="3")
        assert result.returncode == 0, result.stderr
        verdict = check_canvas(*size, library)
        notice = gate.notices(result)[0]
        assert notice.split(" light=", 1)[0] == verdict.notice("3")
        assert gate.weaknesses() == [verdict.defect_line]
        assert gate.weaknesses()[0].startswith("VQ-05 (both): ")
        assert result.stdout.count("::warning::Canvas gate FAILED") == 1

    def test_light_drift_with_the_dark_on_target_names_the_light(self, gate):
        result = gate.light((3000, 1800)).dark(LANDSCAPE).run(library="bokeh")
        assert result.returncode == 0, result.stderr
        fields = _fields(gate.notices(result)[0])
        assert (fields["status"], fields["light"], fields["dark"], fields["delta"]) == (
            "fail",
            "fail",
            "pass",
            "-200x+0",
        )
        [line] = gate.weaknesses()
        assert _render(line) == "light"
        assert line.replace("VQ-05 (light):", "VQ-05 (both):", 1).startswith(
            check_canvas(3000, 1800, "bokeh").defect_line.split(" Re-render at exactly", 1)[0]
        )
        assert "plot-dark.png is 3200×1800, on target, so a size or save option probably depends on the theme" in line

    def test_both_drift_differently_one_line_each(self, gate):
        result = gate.light((3000, 1800)).dark((3100, 1800)).run(library="pygal")
        assert result.returncode == 0, result.stderr
        light, dark = gate.weaknesses()
        assert (_render(light), _render(dark)) == ("light", "dark")
        assert "Actual: 3000×1800" in light
        assert "Actual: 3100×1800" in dark
        assert "plot-light.png is 3000×1800, and both renders must share one canvas." in dark
        assert result.stdout.count("::warning::Canvas gate FAILED") == 2

    @pytest.mark.parametrize("light", ["missing", "empty", "text"])
    def test_a_light_render_that_does_not_open_stops_the_step_as_before(self, gate, light):
        if light != "missing":
            (gate.images / "plot-light.png").write_bytes(b"" if light == "empty" else b"not a png")
        gate.dark(LANDSCAPE)
        result = gate.run()
        assert result.returncode == 1
        assert gate.notices(result) == []
        assert not gate.gate.exists()


def test_every_notice_parses_for_the_report(gate):
    """canvas_gate_report.py reads the fields up to attempt=; the dark fields come after it."""
    gate.light(LANDSCAPE).dark((3000, 1800))
    [record] = canvas_gate_report.parse_lines(gate.notices(gate.run()))
    assert record["status"] == "fail"
    assert record["actual"] == (3200, 1800)
    assert record["attempt"] == 1
    assert record["light"] == "pass"
    assert record["dark"] == "fail"
    assert record["dark_delta"] == (-200, 0)


def test_the_step_keeps_its_place_and_never_fails_the_job_by_itself():
    step = _step("impl-review.yml", STEP)
    assert step["if"] == "steps.render_stop.outputs.stopped != 'true'"
    script = str(step["run"])
    assert script.count("python3 <<'PY'") == 1
    assert "exit 1" not in script
    assert "sys.exit(1)" not in script
