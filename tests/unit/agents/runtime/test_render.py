"""Tests for agents/anyplot/render/: PNG hardening, gates, the harness and the backends."""

import asyncio
import io
import json
import logging
import math
import os
import subprocess
import sys
import tracemalloc
import warnings
from collections.abc import Callable, Iterator
from pathlib import Path

import matplotlib
import matplotlib._text_helpers as text_helpers
import pytest
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.ft2font import FT2Font
from matplotlib.text import Text
from PIL import Image, PngImagePlugin

from agents.anyplot.code.edits import apply_plan
from agents.anyplot.code.loader import to_run_form
from agents.anyplot.code.normalise import normalise
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.render import harness, make_backend
from agents.anyplot.render.backends.fake import FIXTURE_CSV, FakeBackend, FakeOutcome, fixture_png
from agents.anyplot.render.backends.local import LocalDockerBackend, read_tail
from agents.anyplot.render.backends.remote import IdTokenSource, RemoteBackend
from agents.anyplot.render.backends.sandbox import SandboxBackend
from agents.anyplot.render.contract import (
    THEMES,
    ConvertJob,
    DataJob,
    DataRunUnsupported,
    RendererUnavailable,
    RenderJob,
    RenderResult,
    Theme,
    ThemeOutput,
)
from agents.anyplot.render.gates import data_rows, error_summary, evaluate
from agents.anyplot.render.png import PngRejected, harden, pad_to, read_output, size_of
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE, PythonRuntime
from agents.anyplot.render.store import RenderStore, RenderStoreFull
from agents.anyplot.schemas import MAX_NOTE_CHARS, AdaptPlan
from agents.anyplot.settings import AgentSettings
from core.defects import DEFECT_RE

from .conftest import CASES
from .fakes import SCATTER_PLAN


BOTH: tuple[Theme, ...] = THEMES

SEABORN_FONT_RC = {
    "font.family": ["sans-serif"],
    "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans", "Bitstream Vera Sans", "sans-serif"],
}
"""The font rcParams seaborn's `set_theme` writes (seaborn/rcmod.py), which 306 catalogue files call. The unit
tests run without seaborn installed (CI syncs the `test` and `agents` extras only), so they set these directly;
the CI image job renders through real seaborn."""


@pytest.fixture
def glyph_capture(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """The harness's glyph capture on fresh sets, undone afterwards: the wrapper, the sets and the mathtext handler."""
    monkeypatch.setattr(harness, "MISSING_GLYPHS", set())
    monkeypatch.setattr(harness, "MISSING_MATH_GLYPHS", set())
    monkeypatch.setattr(text_helpers, "warn_on_missing_glyph", text_helpers.warn_on_missing_glyph)
    logger = logging.getLogger("matplotlib.mathtext")
    handlers, level = list(logger.handlers), logger.level
    try:
        harness.install_glyph_capture()
        yield
    finally:
        for handler in [handler for handler in logger.handlers if handler not in handlers]:
            logger.removeHandler(handler)
        logger.setLevel(level)


@pytest.fixture
def font_lookup(monkeypatch: pytest.MonkeyPatch) -> Callable[..., object]:
    """matplotlib's own `_find_fonts_by_props`, restored after the test whatever the harness wrapped it with."""
    original = font_manager.FontManager._find_fonts_by_props
    monkeypatch.setattr(font_manager.FontManager, "_find_fonts_by_props", original)
    return original


def png_bytes(size: tuple[int, int], colour: str = "#FAF8F1", draw: bool = True, text: str | None = None) -> bytes:
    image = Image.new("RGB", size, colour)
    if draw:
        for x in range(size[0] // 4, size[0] // 2):
            for y in range(size[1] // 4, size[1] // 4 + 40):
                image.putpixel((x, y), (0, 158, 115))
    info = PngImagePlugin.PngInfo()
    if text:
        info.add_text("Comment", text)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def job(**overrides: object) -> RenderJob:
    values: dict[str, object] = {
        "job_id": "abc123",
        "language": "python",
        "library": "matplotlib",
        "source": "x = 1",
        "data_csv": "a\n1\n",
    }
    values.update(overrides)
    return RenderJob(**values)


class TestPng:
    def test_harden_reencodes_and_drops_text_chunks(self) -> None:
        hardened = harden(png_bytes((400, 300), text="leak me"))

        assert (hardened.width, hardened.height) == (400, 300)
        assert b"leak me" not in hardened.data
        assert hardened.data.startswith(b"\x89PNG")

    @pytest.mark.parametrize(
        ("data", "message"),
        [
            (b"GIF89a....", "PNG signature"),
            (png_bytes((300, 200), draw=False), "one colour"),
            (b"\x89PNG\r\n\x1a\n" + b"\0" * 64, "does not decode"),
        ],
    )
    def test_harden_rejects(self, data: bytes, message: str) -> None:
        with pytest.raises(PngRejected, match=message):
            harden(data)

    @staticmethod
    def sparse_png(drawn_pixels: int) -> bytes:
        """A 1000x100 background with `drawn_pixels` of ink in one strip of 10 rows: 100,000 pixels in all."""
        image = Image.new("RGB", (1000, 100), "#FAF8F1")
        image.paste((0, 158, 115), (0, 0, drawn_pixels // 10, 10))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_a_sparse_render_passes_the_blank_check(self) -> None:
        """99.5 % one colour, as sparse as the sparsest eligible pygal render (network-directed, 99.44 %): drawn."""
        hardened = harden(self.sparse_png(500))

        assert (hardened.width, hardened.height) == (1000, 100)

    def test_a_canvas_with_only_a_title_is_blank(self) -> None:
        """99.8 % one colour, the share of a pygal chart with only its title (99.78 %): nothing was drawn."""
        with pytest.raises(PngRejected, match=r"99\.8% one colour \(#FAF8F1\)"):
            harden(self.sparse_png(200))

    def test_read_output_refuses_symlinks_and_size(self, tmp_path: Path) -> None:
        target = tmp_path / "secret.txt"
        target.write_text("host file")
        (tmp_path / "plot-light.png").symlink_to(target)
        with pytest.raises(PngRejected, match="regular file"):
            read_output(tmp_path / "plot-light.png", 1024)
        (tmp_path / "big.png").write_bytes(b"x" * 2048)
        with pytest.raises(PngRejected, match="limit"):
            read_output(tmp_path / "big.png", 1024)
        assert read_output(tmp_path / "missing.png", 1024) is None

    def test_pad_never_crops(self) -> None:
        small = pad_to(png_bytes((3100, 1700)), (3200, 1800))
        large = pad_to(png_bytes((3300, 1800)), (3200, 1800))

        assert size_of(small) == (3200, 1800)
        assert size_of(large) == (3200, 1800)
        with Image.open(io.BytesIO(small)) as image:
            assert image.getpixel((0, 0)) == (0xFA, 0xF8, 0xF1)  # the background colour, not black


class TestGates:
    def result(self, **outputs: ThemeOutput) -> RenderResult:
        return RenderResult("abc123", dict(outputs))

    def ok(self, theme: str, size: tuple[int, int] = (3200, 1800), probe: dict | None = None) -> ThemeOutput:
        return ThemeOutput(theme, 0, png=fixture_png(theme, size), probe=probe or {})

    def test_clean_render_passes(self) -> None:
        report = evaluate(
            self.result(light=self.ok("light"), dark=self.ok("dark")), themes=BOTH, library="matplotlib", rows=10
        )

        assert report.passed_host_gates and report.canvas_ok
        assert report.defects == [] and set(report.pngs) == {"light", "dark"}

    @pytest.mark.parametrize("theme", ["light", "dark"])
    def test_a_one_theme_job_needs_only_its_theme(self, theme: Theme) -> None:
        report = evaluate(self.result(**{theme: self.ok(theme)}), themes=(theme,), library="matplotlib", rows=10)

        assert report.passed_host_gates and report.canvas_ok
        assert set(report.pngs) == {theme} and report.blocking == []

    @pytest.mark.parametrize(("theme", "other"), [("light", "dark"), ("dark", "light")])
    def test_a_one_theme_job_ignores_the_other_theme(self, theme: Theme, other: Theme) -> None:
        """The gates judge the job's themes only: an extra output neither passes nor fails the render."""
        crashed = ThemeOutput(other, 1, stderr_tail="KeyError: 'x'\n")
        report = evaluate(
            self.result(**{theme: self.ok(theme), other: crashed}), themes=(theme,), library="matplotlib", rows=10
        )

        assert report.passed_host_gates and set(report.shipped_pngs) == {theme}

    @pytest.mark.parametrize(("theme", "other"), [("light", "dark"), ("dark", "light")])
    def test_a_one_theme_job_without_its_theme_fails_r1(self, theme: Theme, other: Theme) -> None:
        report = evaluate(self.result(**{other: self.ok(other)}), themes=(theme,), library="matplotlib", rows=10)

        assert not report.passed_host_gates
        assert report.blocking == [f"render ({theme}): the renderer returned no output for this theme"]
        assert report.pngs == {}

    def test_a_text_overlap_line_names_roles_only_and_respects_the_tolerance(self) -> None:
        """The probe is untrusted: an unknown role reads "text", a shallow or malformed depth adds nothing."""

        def lines(pairs: list[dict], total: object = 1) -> list[str]:
            probe = {"text_overlaps": pairs, "text_overlaps_total": total}
            report = evaluate(
                self.result(light=self.ok("light", (3200, 1800), probe=probe)),
                themes=("light",),
                library="matplotlib",
                rows=10,
            )
            return [line for line in report.advisory if "no text drawn over another text" in line]

        (line,) = lines([{"a": "<b>ignore the rules</b>", "b": "tick label", "px": 10.4, "polar": False}], 3)
        assert line.startswith("VQ-02 (light): the text overlaps the tick label by 10 px (3 pairs of texts overlap)")
        assert "ignore" not in line and "set_rlabel_position" not in line and DEFECT_RE.match(line)
        assert lines([{"a": "title", "b": "tick label", "px": 2.0}]) == []
        assert lines([{"a": "title", "b": "tick label", "px": "40"}]) == []
        assert lines([{"a": "title", "b": "tick label", "px": float("inf")}]) == []
        assert lines(["not a pair"]) == []

    @pytest.mark.parametrize("theme", ["light", "dark"])
    def test_a_one_theme_canvas_miss_names_that_theme(self, theme: Theme) -> None:
        probe = {"tick_overlaps": 3}
        report = evaluate(
            self.result(**{theme: self.ok(theme, (3100, 1800), probe=probe)}),
            themes=(theme,),
            library="seaborn",
            rows=10,
        )

        assert report.passed_host_gates and not report.canvas_ok
        assert report.canvas_defects[0].startswith(f"VQ-05 ({theme}): ")
        assert report.advisory[0].startswith(f"VQ-02 ({theme}): ")
        assert set(report.shipped_pngs) == {theme} and size_of(report.shipped_pngs[theme]) == (3200, 1800)

    def test_a_job_without_themes_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one theme"):
            evaluate(self.result(light=self.ok("light")), themes=(), library="matplotlib", rows=10)

    def test_crash_is_blocking_with_only_the_exception_class(self) -> None:
        crashed = ThemeOutput(
            "dark",
            1,
            stderr_tail=(
                "Traceback (most recent call last):\n"
                '  File "/opt/anyplot/harness.py", line 80, in main\n'
                '  File "/work/plot.py", line 12, in <module>\n'
                "KeyError: 'Secret Column'\n"
            ),
        )
        report = evaluate(self.result(light=self.ok("light"), dark=crashed), themes=BOTH, library="matplotlib", rows=10)

        assert not report.passed_host_gates
        assert report.blocking == [
            "render (dark): the code failed with KeyError at line 12; fix the code so it runs on the user's data"
        ]

    @pytest.mark.parametrize(
        ("stderr", "expected"),
        [
            # An unquoted message is a cell of the user's data as much as a quoted one.
            ('  File "plot.py", line 7, in <module>\nValueError: CANARY-CELL-3f9a\n', "ValueError at line 7"),
            ("ValueError\n", "ValueError"),
            ("pandas.errors.ParserError: Error tokenizing CANARY-CELL-3f9a\n", "pandas.errors.ParserError"),
            # Not a builtin exception: never echoed. A made-up qualified class is not echoed either.
            ("CANARYCELLError: x\n", "an error that printed no exception line"),
            ("SecretTable.LeakError: y\n", "an error of an unlisted exception class"),
            ("pandas.Alice_Smith_4111Error: y\n", "an error of an unlisted exception class"),
            ("pandas.SECRET.Error\n", "an error of an unlisted exception class"),
            ("CANARY-CELL-3f9a\n", "an error that printed no exception line"),
            (
                '  File "plot.py", line 3\nTypeError: a\n\nDuring handling ...\nRuntimeError: CANARY\n',
                "RuntimeError at line 3",
            ),
        ],
    )
    def test_error_summary_never_carries_the_message(self, stderr: str, expected: str) -> None:
        summary = error_summary(stderr)

        assert summary == expected
        assert "CANARY" not in summary and "Alice" not in summary and "SECRET" not in summary

    def test_error_summary_of_a_data_snippet_reads_its_own_frames(self) -> None:
        stderr = (
            '  File "/work/plot.py", line 9, in <module>\n'
            '  File "/work/snippet.py", line 4, in <module>\nZeroDivisionError: CANARY\n'
        )

        assert error_summary(stderr, code_file="snippet.py") == "ZeroDivisionError at line 4"
        assert error_summary(stderr) == "ZeroDivisionError at line 9"

    def test_missing_theme_fails_r1(self) -> None:
        """A two-theme job with only one theme back is incomplete although every output it has passed."""
        report = evaluate(self.result(light=self.ok("light")), themes=BOTH, library="matplotlib", rows=10)

        assert not report.passed_host_gates
        assert report.blocking == ["render (dark): the renderer returned no output for this theme"]
        assert set(report.pngs) == {"light"}

    def test_one_theme_off_canvas_ships_both_themes(self) -> None:
        report = evaluate(
            self.result(light=self.ok("light"), dark=self.ok("dark", (3100, 1800))),
            themes=BOTH,
            library="seaborn",
            rows=10,
        )

        assert report.passed_host_gates and not report.canvas_ok
        assert set(report.padded_pngs) == {"dark"}
        assert len(report.canvas_defects) == 1 and report.canvas_defects[0].startswith("VQ-05 (dark): ")
        assert set(report.shipped_pngs) == {"light", "dark"}
        assert report.shipped_pngs["light"] == report.pngs["light"]
        assert report.shipped_pngs["dark"] == report.padded_pngs["dark"]
        assert size_of(report.shipped_pngs["dark"]) == (3200, 1800)

    def test_timeout_and_missing_png(self) -> None:
        report = evaluate(
            self.result(light=ThemeOutput("light", None, timed_out=True), dark=ThemeOutput("dark", 0)),
            themes=BOTH,
            library="matplotlib",
            rows=10,
        )

        assert not report.passed_host_gates
        assert "time limit" in report.blocking[0] and "saved no plot-dark.png" in report.blocking[1]
        assert report.failed_gates == ["R1-timeout", "R1"]

    def test_canvas_miss_is_a_defect_with_a_padded_copy(self) -> None:
        report = evaluate(
            self.result(light=self.ok("light", (3100, 1800)), dark=self.ok("dark", (3100, 1800))),
            themes=BOTH,
            library="seaborn",
            rows=10,
        )

        assert report.passed_host_gates and not report.canvas_ok
        assert len(report.canvas_defects) == 1 and report.canvas_defects[0].startswith("VQ-05 (both)")
        assert size_of(report.padded_pngs["light"]) == (3200, 1800)
        assert report.failed_gates == ["R3", "R3"]  # one entry per theme, for the attribution log

    def test_advisory_probe_lines(self) -> None:
        probe = {
            "canvas": [3200, 1800],
            "texts": [{"kind": "Text", "box": [-30, 10, 200, 50]}],
            "tick_overlaps": 2,
            "annotations_outside": 1,
            "points": 500,
        }
        report = evaluate(
            self.result(light=self.ok("light", probe=probe), dark=self.ok("dark", probe=probe)),
            themes=BOTH,
            library="matplotlib",
            rows=24,
        )

        assert report.passed_host_gates
        assert [line.split(":")[0] for line in report.advisory] == [
            "AR-09 (both)",
            "VQ-02 (both)",
            "DQ-03 (both)",
            "DQ-03 (code)",
        ]
        assert report.failed_gates == ["G3", "G7", "G5", "G8"] * 2  # per theme, in the probe's check order

    @pytest.mark.parametrize(
        "probe",
        [
            {"canvas": [3200, 1800], "texts": [{"box": [0, 0, float("inf"), 0]}]},
            {"canvas": [3200, 1800], "texts": [{"box": ["a", 0, 1, 1]}]},
            {"canvas": [float("nan"), 1800], "texts": [{"box": [-50, 0, 1, 1]}]},
            {"canvas": [3200, 1800], "texts": "not a list", "points": "many"},
            {"canvas": [3200, 1800], "texts": [{"box": [-1e308, 0, 1, 1]}, None, {"box": [True, 0, 1, 1]}]},
        ],
    )
    def test_malformed_probe_adds_no_line_and_never_raises(self, probe: dict) -> None:
        report = evaluate(
            self.result(light=self.ok("light", probe=probe), dark=self.ok("dark", probe=probe)),
            themes=BOTH,
            library="matplotlib",
            rows=24,
        )

        assert report.passed_host_gates
        assert all(not line.startswith("AR-09") or "px" in line for line in report.advisory)

    def glyph_lines(self, missing: object) -> tuple[list[str], list[str]]:
        """The failed gates and advisory lines of a two-theme render whose probes carry `missing_glyphs`."""
        probe = {"canvas": [3200, 1800], "missing_glyphs": missing}
        report = evaluate(
            self.result(light=self.ok("light", probe=probe), dark=self.ok("dark", probe=probe)),
            themes=BOTH,
            library="matplotlib",
            rows=24,
        )
        assert report.passed_host_gates  # G10 advises, it never fails a render
        return report.failed_gates, report.advisory

    def test_g10_names_the_count_and_a_labelled_sample(self) -> None:
        failed, advisory = self.glyph_lines({"count": 7, "math": 0, "sample": [0x41, 0x9500, 0xD55C, 0x1F525, 0xE000]})

        assert failed == ["G10", "G10"]
        assert len(advisory) == 1
        line = advisory[0]
        assert line.startswith("VQ-01 (both): 7 characters have no glyph, drawn as boxes")
        assert "U+9500 销 cjk unified, U+D55C 한 hangul syllable, U+1F525 🔥 fire, …" in line
        assert "a user's column name stays" in line
        assert "U+0041" not in line  # printable ASCII is in every font: a tampered sample
        assert "U+E000" not in line  # the fourth valid code point; the line names three
        assert line.endswith("Likely cause: an emoji, a flag or a script the fonts lack.")
        assert DEFECT_RE.match(line) and len(line) <= MAX_NOTE_CHARS

        _, capped = self.glyph_lines({"count": 2, "math": 0, "sample": [0x0924, 0x10140]})
        # "devanagari letter" and "greek acrophonic" exceed the 15-character name cap: the first word stays.
        assert "(U+0924 त devanagari, U+10140 𐅀 greek)" in capped[0]

    def test_g10_blames_mathtext_when_math_is_positive(self) -> None:
        _, advisory = self.glyph_lines({"count": 1, "math": 1, "sample": [0xD55C]})

        line = advisory[0]
        assert line.startswith(
            "VQ-01 (both): 1 character has no glyph, drawn as boxes or ¤ (U+D55C 한 hangul syllable)"
        )
        assert "…" not in line.split("→")[0]
        assert "→ keep non-Latin text outside $…$ math strings; a user's column name stays." in line
        assert line.endswith("Likely cause: a $…$ math string, which has no font fallback.")
        assert DEFECT_RE.match(line)

    def test_g10_never_echoes_a_control_or_format_character(self) -> None:
        _, advisory = self.glyph_lines({"count": 3, "sample": [0x202E, 0x200B, 0x09, 0x20, 0x41]})

        line = advisory[0]
        assert "(U+202E right-to-left, U+200B zero width, U+0009 control)" in line
        assert line.endswith("Likely cause: a tab or carriage return in a label.")
        assert "‮" not in line and "​" not in line and "\t" not in line
        assert "U+0020" not in line and "U+0041" not in line  # printable ASCII is dropped

    @pytest.mark.parametrize(
        ("missing", "names_a_line"),
        [
            ({"count": True}, False),
            ({"count": -1}, False),
            ({"count": "7"}, False),
            ({"count": 0}, False),
            ({"count": 10**12}, False),  # more distinct code points than Unicode has
            ([1, 2], False),
            ("text", False),
            ({"count": 3, "sample": "abc"}, True),
            ({"count": 3, "sample": [0x110000, -1, 0xD800, 1.5, None, True]}, True),
        ],
    )
    def test_a_malformed_glyph_report_never_raises(self, missing: object, names_a_line: bool) -> None:
        failed, advisory = self.glyph_lines(missing)

        assert ("G10" in failed) is names_a_line
        if names_a_line:  # a valid count with an unusable sample: the line names no characters
            assert advisory == [
                "VQ-01 (both): 3 characters have no glyph, drawn as boxes → in text the code writes, use characters "
                "the fonts cover; a user's column name stays. Likely cause: an emoji, a flag or a script the fonts "
                "lack."
            ]
        else:
            assert advisory == []

    def test_helpers(self) -> None:
        assert data_rows("a,b\n1,2\n3,4\n") == 2
        assert error_summary("") == "no error output"


class TestHarness:
    def test_real_render_of_the_adapted_catalogue_file(self, tmp_path: Path) -> None:
        """The whole deterministic chain on a real catalogue file: normalise, edits, loader, harness, gates."""
        snapshot = snapshot_from_repo("scatter-basic", "matplotlib")
        working = normalise(snapshot.code, library="matplotlib")
        applied = apply_plan(working, AdaptPlan.model_validate(SCATTER_PLAN))
        assert applied.code is not None, applied.failures
        data_text = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text()
        parsed = parse_dataset(data_text)
        run_form = to_run_form(
            normalise(applied.code, library="matplotlib"),
            columns=[column.name for column in parsed.profile.columns],
            dtypes=dict(parsed.column_dtypes),
            parse_dates=list(parsed.parse_dates),
        )
        (tmp_path / "plot.py").write_text(run_form)
        (tmp_path / "data.csv").write_text(parsed.csv)
        runtime = PythonRuntime(python=sys.executable, harness=str(HARNESS_SOURCE), mplconfig=str(tmp_path / "mpl"))
        outputs = {}
        for theme in ("light", "dark"):
            env = {**runtime.env(theme), "MPLCONFIGDIR": str(tmp_path / "mpl"), "HOME": str(tmp_path)}
            env["PATH"] = os.environ.get("PATH", "")
            done = subprocess.run(
                runtime.command(theme), cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120
            )
            assert done.returncode == 0, done.stderr[-2000:]
            png, probe = runtime.collect(tmp_path, theme)
            outputs[theme] = ThemeOutput(theme, 0, png=png, probe=probe)

        report = evaluate(RenderResult("real", outputs), themes=BOTH, library="matplotlib", rows=parsed.profile.rows)

        assert report.passed_host_gates, report.blocking
        assert report.canvas_ok, report.canvas_defects
        # Spike X saw a 441 px G3 here from the undrawn x tick label one step past the view.
        assert report.failed_gates == [], report.advisory
        probe = json.loads((tmp_path / "probe-light.json").read_text())
        assert probe["canvas"] == [3200, 1800]
        assert probe["points"] == 24
        assert probe["missing_glyphs"] == {"count": 0, "math": 0, "sample": []}
        # The catalogue file sets `font.family` itself; the normaliser leaves it, and the harness's
        # lookup hook appends its fallbacks after it instead of rewriting it.
        assert '"font.family": "DejaVu Sans"' in run_form

    @staticmethod
    def figure() -> Figure:
        fig = Figure(figsize=(16, 9))
        FigureCanvasAgg(fig)
        return fig

    @staticmethod
    def gates(probe: dict) -> list[str]:
        """The probe gates the host derives from one in-process probe of a 3200x1800 canvas."""
        output = ThemeOutput("light", 0, png=fixture_png("light", (3200, 1800)), probe=probe)
        return evaluate(
            RenderResult("p", {"light": output}), themes=("light",), library="matplotlib", rows=10_000
        ).failed_gates

    def test_tick_labels_outside_the_view_interval_are_not_measured(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        ax.plot(range(1, 13), [-2, 1, 6, 12, 18, 24, 29, 31, 26, 18, 9, 2])
        ax.set_title("Monthly temperature", fontsize=24)
        fig.tight_layout()
        assert max(ax.yaxis.get_majorticklocs()) > ax.get_ylim()[1]  # the locator places a tick past the view

        report = harness.probe(fig, 200)

        assert "G3" not in self.gates(report), report["texts"]

    def test_a_drawn_title_beyond_the_canvas_is_still_measured(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        ax.plot([0, 1], [0, 1])
        ax.set_title("A title placed off the canvas", fontsize=24, x=1.08, ha="left")
        fig.tight_layout()

        assert "G3" in self.gates(harness.probe(fig, 200))

    def test_tick_labels_of_a_hidden_axis_are_not_measured(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        ax.plot(range(10), range(10))
        ax.set_xticks(range(10), [f"a long category label {number}" for number in range(10)])
        ax.axis("off")

        report = harness.probe(fig, 200)

        assert report["tick_overlaps"] == 0 and self.gates(report) == []

    def polar_with_ylabel(self, *, labelpad: float = 4.0) -> Figure:
        """The owner's case of 2026-10-12 (polar-scatter): the radial axis label sits on the 270° tick label."""
        fig = self.figure()
        ax = fig.add_subplot(projection="polar")
        theta = [index * 0.0314 for index in range(200)]
        ax.scatter(theta, [abs(math.sin(value)) for value in theta], s=60)
        ax.set_xlabel("x (Grad)", fontsize=22)
        ax.set_ylabel("y", fontsize=22, labelpad=labelpad)
        ax.tick_params(labelsize=20)
        fig.tight_layout()
        return fig

    def test_an_axis_label_on_a_tick_label_is_a_g7_line(self) -> None:
        report = harness.probe(self.polar_with_ylabel(), 200)

        assert report["text_overlaps_total"] >= 1, report["text_overlaps"]
        worst = report["text_overlaps"][0]
        assert {worst["a"], worst["b"]} & {"radial axis label", "angular axis label"}
        assert worst["polar"] is True and worst["px"] > harness.TEXT_OVERLAP_TOLERANCE_PX
        output = ThemeOutput("light", 0, png=fixture_png("light", (3200, 1800)), probe=report)
        lines = evaluate(
            RenderResult("p", {"light": output}), themes=("light",), library="matplotlib", rows=10_000
        ).advisory
        line = next(line for line in lines if "no text drawn over another text" in line)
        assert line.startswith("VQ-02 (light): the ") and "axis label" in line and "set_rlabel_position" in line
        assert DEFECT_RE.match(line), line

    def test_a_clean_plot_with_title_labels_and_legend_has_no_text_overlap(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        ax.plot(range(10), [value * value for value in range(10)], label="squares")
        ax.plot(range(10), range(10), label="identity")
        ax.set_title("Two series", fontsize=24)
        ax.set_xlabel("x", fontsize=20)
        ax.set_ylabel("value", fontsize=20)
        ax.legend(fontsize=16)
        ax.annotate("start", xy=(0, 0), xytext=(1, 40), fontsize=16)
        fig.suptitle("A figure title", fontsize=26)
        fig.tight_layout()

        report = harness.probe(fig, 200)

        assert report["text_overlaps"] == [] and report["text_overlaps_total"] == 0
        assert "G7" not in self.gates(report)

    def test_a_polar_label_moved_off_the_ticks_is_clean(self) -> None:
        report = harness.probe(self.polar_with_ylabel(labelpad=60), 200)

        assert report["text_overlaps_total"] == 0, report["text_overlaps"]

    def test_two_legends_on_one_spot_overlap_but_one_legend_never_with_itself(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        first = ax.legend(handles=ax.plot([0, 1], [0, 1], label="first series"), loc="upper left", fontsize=20)
        ax.add_artist(first)
        ax.legend(handles=ax.plot([0, 1], [1, 0], label="second series"), loc="upper left", fontsize=20)

        report = harness.probe(fig, 200)

        assert [(pair["a"], pair["b"]) for pair in report["text_overlaps"]] == [("legend text", "legend text")]

    def test_a_drawn_text_without_a_role_still_counts(self) -> None:
        """An axis offset text (the `1e6` multiplier) is drawn but named by no role: it reads "text"."""
        fig = self.figure()
        ax = fig.subplots()
        ax.plot([0, 1], [0, 3e6])
        offset = ax.yaxis.get_offset_text()
        offset.set_fontsize(40)
        ax.set_title("over the multiplier", loc="left", fontsize=40, y=0.99)

        report = harness.probe(fig, 200)

        assert {"title", "text"} in [{pair["a"], pair["b"]} for pair in report["text_overlaps"]]

    def test_crowded_z_tick_labels_of_3d_axes_count(self) -> None:
        fig = self.figure()
        ax = fig.add_subplot(projection="3d")
        ax.plot([0, 1], [0, 1], [0, 1])
        ax.set_zticks([index / 80 for index in range(80)], [f"level {index}" for index in range(80)])

        assert harness.probe(fig, 200)["tick_overlaps"] > 0

    def test_tick_label_pairs_stay_their_own_count(self) -> None:
        fig = self.figure()
        ax = fig.subplots()
        ax.set_xticks(range(60), [f"category {number}" for number in range(60)])

        report = harness.probe(fig, 200)

        assert report["tick_overlaps"] > 0 and report["text_overlaps_total"] == 0

    def test_an_annotation_clipped_out_of_its_axes_still_counts(self) -> None:
        """G5 looks for exactly this: an annotation at a data coordinate of the example data."""
        fig = self.figure()
        ax = fig.subplots()
        ax.plot([0, 1, 2], [3, 1, 2])
        ax.set_xlim(0, 2)
        ax.annotate("peak of the example data", xy=(40, 3))

        assert harness.probe(fig, 200)["annotations_outside"] == 1

    def test_the_probe_restores_text_draw_even_when_the_draw_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original = Text.draw
        fig = self.figure()
        fig.subplots().set_title("t")
        harness.probe(fig, 200)
        assert Text.draw is original

        broken = self.figure()

        def fail() -> None:
            raise RuntimeError("draw failed")

        monkeypatch.setattr(broken.canvas, "draw", fail)
        with pytest.raises(RuntimeError):
            harness.probe(broken, 200)
        assert Text.draw is original

    def test_glyph_capture_records_plain_and_math_code_points_under_silenced_warnings(
        self, glyph_capture: None
    ) -> None:
        """Brief item 5: with DejaVu alone the report fires and is captured, whatever the plot code silences."""
        parent = logging.getLogger("matplotlib")
        level = parent.level
        with warnings.catch_warnings(), matplotlib.rc_context({"font.family": ["DejaVu Sans"]}):
            warnings.simplefilter("ignore")
            # The level `matplotlib.set_loglevel("error")` sets; the function itself would also attach
            # a stream handler for the rest of the test process.
            parent.setLevel(logging.ERROR)
            try:
                fig = self.figure()
                ax = fig.subplots()
                ax.set_title("销售" + chr(0xE000))  # a private-use character no font maps
                ax.text(0.2, 0.5, "한 $x^2$")  # a string with `$…$` is laid out by mathtext as a whole
                fig.canvas.draw()
            finally:
                parent.setLevel(level)

        assert {0x9500, 0x552E, 0xE000} <= harness.MISSING_GLYPHS
        assert harness.MISSING_MATH_GLYPHS == {0xD55C}
        assert harness.glyph_report() == {"count": 4, "math": 1, "sample": [0x552E, 0x9500, 0xD55C, 0xE000]}

    def test_glyph_report_caps_the_sample(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(harness, "MISSING_GLYPHS", set(range(0x4E00 + 39, 0x4E00 - 1, -1)))
        monkeypatch.setattr(harness, "MISSING_MATH_GLYPHS", set())

        report = harness.glyph_report()

        assert report["count"] == 40 and report["math"] == 0
        assert report["sample"] == list(range(0x4E00, 0x4E00 + harness.GLYPH_SAMPLE_LIMIT))

    def test_fallback_hook_keeps_the_codes_choice_first_and_skips_uninstalled_families(
        self, font_lookup: Callable[..., object], monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        manager = font_manager.fontManager
        bold = FontProperties(family="DejaVu Sans Mono", weight="bold")

        def names(prop: FontProperties) -> list[str]:
            return [Path(path).name for path in manager._find_fonts_by_props(prop)]

        monkeypatch.setattr(harness, "FALLBACK_FAMILIES", ("No Such Family", "DejaVu Serif"))
        harness.install_fallback_fonts()
        with caplog.at_level(logging.WARNING, logger="matplotlib.font_manager"):
            assert names(FontProperties(family="DejaVu Sans Mono")) == ["DejaVuSansMono.ttf", "DejaVuSerif.ttf"]
            assert names(FontProperties(family="DejaVu Serif")) == ["DejaVuSerif.ttf"]  # no duplicate entry
            assert names(bold) == ["DejaVuSansMono-Bold.ttf", "DejaVuSerif-Bold.ttf"]  # the nearest weight
        # The uninstalled family was dropped at install, so no lookup ever asked for it.
        assert not [record for record in caplog.records if "not found" in record.getMessage()]

        monkeypatch.setattr(font_manager.FontManager, "_find_fonts_by_props", font_lookup)
        monkeypatch.setattr(harness, "FALLBACK_FAMILIES", ("DejaVu Sans Display",))  # one file, weight 400
        harness.install_fallback_fonts()
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="matplotlib.font_manager"):
            assert names(bold) == ["DejaVuSansMono-Bold.ttf", "DejaVuSansDisplay.ttf"]
        # Asked for weight 400, the only one it has; asking for bold would log one record per lookup key.
        assert not [record for record in caplog.records if "Failed to find font weight" in record.getMessage()]

    def test_fallback_hook_survives_a_font_family_reset_and_a_per_text_family(
        self, glyph_capture: None, font_lookup: Callable[..., object], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The rcParams seaborn's `set_theme` writes and a per-text `monospace` both leave the hook's fallback in place."""
        manager = font_manager.fontManager

        def draw(text: str) -> None:
            with matplotlib.rc_context(SEABORN_FONT_RC):
                fig = self.figure()
                ax = fig.subplots()
                ax.set_xticks([0.5], [text])  # a tick label: the rc family
                ax.text(0.2, 0.5, text, family="monospace")  # a family set on the text bypasses the rc list
                fig.canvas.draw()

        # A code point the stand-in fallback has and that neither text's own fonts cover, read from
        # the files these lookups resolve to (a runner may serve a system DejaVu).
        with matplotlib.rc_context(SEABORN_FONT_RC):
            tick, mono = FontProperties(), FontProperties(family="monospace")
            own = {*manager._find_fonts_by_props(tick), *manager._find_fonts_by_props(mono)}
        covered = set().union(*(FT2Font(str(path)).get_charmap() for path in own))
        serif = manager.findfont(FontProperties(family="DejaVu Serif"), fallback_to_default=False)
        candidates = sorted(code for code in FT2Font(str(serif)).get_charmap() if code not in covered)
        codepoint = next(code for code in candidates if chr(code).isprintable())

        monkeypatch.setattr(harness, "FALLBACK_FAMILIES", ("DejaVu Serif",))
        harness.install_fallback_fonts()
        draw(chr(codepoint))
        assert harness.MISSING_GLYPHS == set()

        monkeypatch.setattr(font_manager.FontManager, "_find_fonts_by_props", font_lookup)
        with pytest.warns(UserWarning, match="missing from font"):  # the capture calls matplotlib's report through
            draw(chr(codepoint))
        assert codepoint in harness.MISSING_GLYPHS  # without the hook the same code point has no glyph

    def test_the_dejavu_only_control_reports_g10_through_the_whole_chain(self, tmp_path: Path) -> None:
        """matplotlib's bundled fonts only (as the CI image job's control): the harness, the probe and the gate."""
        (tmp_path / "plot.py").write_text(
            "import os\n"
            "import matplotlib.pyplot as plt\n"
            'THEME = os.environ["ANYPLOT_THEME"]\n'
            'plt.rcParams.update({"font.family": ["sans-serif"]})\n'
            "fig, ax = plt.subplots(figsize=(16, 9), dpi=200)\n"
            "ax.bar([0, 1, 2], [3, 1, 2])  # enough ink for R2, which a near-blank PNG fails before any probe gate\n"
            'ax.set_title("销售額 नमस्ते")\n'
            'fig.savefig(f"plot-{THEME}.png")\n',
            encoding="utf-8",
        )
        runtime = PythonRuntime(python=sys.executable, harness=str(HARNESS_SOURCE), mplconfig=str(tmp_path / "mpl"))
        env = {**runtime.env("light"), "MPLCONFIGDIR": str(tmp_path / "mpl"), "HOME": str(tmp_path)}
        env.update({"MPL_IGNORE_SYSTEM_FONTS": "1", "PATH": os.environ.get("PATH", "")})
        del env["ANYPLOT_MPL_SEED"]
        done = subprocess.run(
            runtime.command("light"), cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120
        )
        assert done.returncode == 0, done.stderr[-2000:]
        png, probe = runtime.collect(tmp_path, "light")

        report = evaluate(
            RenderResult("g10", {"light": ThemeOutput("light", 0, png=png, probe=probe)}),
            themes=("light",),
            library="matplotlib",
            rows=2,
        )

        assert probe is not None and probe["missing_glyphs"]["count"] >= 6  # three Han, four Devanagari
        assert "G10" in report.failed_gates
        lines = [line for line in report.advisory if line.startswith("VQ-01 (light):")]
        assert len(lines) == 1 and DEFECT_RE.match(lines[0])
        # The harness sorts the sample ascending and the host names the first three: Devanagari before Han.
        assert "U+0924 त devanagari" in lines[0] and "U+9500" not in lines[0]

    def test_check_fonts_names_the_missing_family(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(harness, "FALLBACK_FAMILIES", ("No Such Family",))
        with pytest.raises(SystemExit, match="No Such Family"):
            harness.check_fonts()

        monkeypatch.setattr(harness, "FALLBACK_FAMILIES", ("DejaVu Serif",))
        harness.check_fonts()
        assert capsys.readouterr().out.startswith("font cache:")

    def test_harness_refuses_an_unknown_theme(self, tmp_path: Path) -> None:
        (tmp_path / "plot.py").write_text("print('never')\n")
        done = subprocess.run(
            [sys.executable, "-I", str(HARNESS_SOURCE), "plot.py"],
            cwd=tmp_path,
            env={"ANYPLOT_THEME": "sepia", "PATH": os.environ.get("PATH", "")},
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert done.returncode == 2 and "never" not in done.stdout


class TestBackends:
    async def test_local_backend_kills_the_container_on_cancellation(self, tmp_path: Path) -> None:
        killed = tmp_path / "killed.txt"
        started = tmp_path / "started.txt"
        docker = tmp_path / "docker"
        docker.write_text(
            f'#!/bin/sh\nif [ "$1" = kill ]; then echo "$2" >> {killed}; exit 0; fi\necho run >> {started}\nexec sleep 30\n'
        )
        docker.chmod(0o755)
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker=str(docker)
        )

        task = asyncio.create_task(backend.render(job(job_id="cancelme")))
        # Cancel once both theme containers run: a fixed sleep lost the race on a loaded CI runner.
        for _ in range(500):
            if started.exists() and len(started.read_text().split()) == 2:
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Timed out waiting for containers to start")
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert sorted(killed.read_text().split()) == ["r-cancelme-dark", "r-cancelme-light"]

    async def test_local_backend_keeps_only_a_bounded_stderr_tail(self, tmp_path: Path) -> None:
        """Code under test that floods stderr never makes the host hold the whole stream."""
        flood = 16 * 1024 * 1024
        docker = tmp_path / "docker"
        docker.write_text(
            "#!/bin/sh\n"
            f"head -c {flood} /dev/zero | tr '\\000' x >&2\n"
            "printf '\\nValueError: TAIL-MARKER\\n' >&2\n"
            "exit 1\n"
        )
        docker.chmod(0o755)
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker=str(docker)
        )

        tracemalloc.start()
        try:
            result = await backend.render(job(job_id="flood"))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        assert peak < 4 * 1024 * 1024, f"peak {peak} bytes for {2 * flood} bytes of stderr"
        for theme in ("light", "dark"):
            output = result.outputs[theme]
            assert output.exit_code == 1
            assert output.stderr_tail.endswith("ValueError: TAIL-MARKER\n")

    async def test_read_tail_keeps_the_last_bytes(self) -> None:
        stream = asyncio.StreamReader()
        stream.feed_data(b"a" * 300_000)
        stream.feed_data(b"END")
        stream.feed_eof()

        tail = await read_tail(stream, limit=1000)

        assert len(tail) == 1000 and tail.endswith(b"aEND")

    def test_local_backend_command_keeps_the_network_off(self) -> None:
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker="/usr/bin/docker"
        )
        argv = backend.argv(job(), "light", Path("/tmp/run"))

        assert argv[:3] == ["/usr/bin/docker", "run", "--rm"]
        assert argv[argv.index("--network") + 1] == "none"
        assert "--read-only" in argv and "--allow-egress" not in argv
        assert "/tmp/run:/work" in argv
        assert argv[-6:] == [
            "/app/.venv/bin/python",
            "-I",
            "-X",
            "disable-remote-debug",
            "/opt/anyplot/harness.py",
            "plot.py",
        ]
        assert "ANYPLOT_THEME=light" in argv

    def test_local_backend_data_command_keeps_the_network_off_and_has_no_theme(self) -> None:
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker="/usr/bin/docker"
        )
        argv = backend.data_argv(DataJob(job_id="d1", source="df = 1\n"), Path("/tmp/run"))

        assert argv[argv.index("--network") + 1] == "none" and "--read-only" in argv
        assert "/tmp/run:/work" in argv and "r-d1-data" in argv
        assert argv[-7:] == [
            "/app/.venv/bin/python",
            "-I",
            "-X",
            "disable-remote-debug",
            "/opt/anyplot/harness.py",
            "--data",
            "snippet.py",
        ]
        assert not any(part.startswith(("ANYPLOT_THEME", "MPLBACKEND")) for part in argv)
        # The renderer's limits for a data run, address space and processes included (parity with `sandbox_env`).
        from agents.renderer.settings import RendererSettings

        deployed = RendererSettings()
        assert f"ANYPLOT_RLIMIT_AS_MB={deployed.rlimit_as_mb}" in argv
        assert f"ANYPLOT_RLIMIT_NPROC={deployed.rlimit_nproc}" in argv

    async def test_local_backend_runs_a_data_snippet(self, tmp_path: Path) -> None:
        """A stand-in `docker` that runs the command with this interpreter and the checkout's harness in `/work`."""
        docker = tmp_path / "docker"
        docker.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "args = sys.argv[1:]\n"
            "if args[0] == 'kill':\n"
            "    sys.exit(0)\n"
            "work = next(v.split(':')[0] for f, v in zip(args, args[1:]) if f == '-v' and v.endswith(':/work'))\n"
            "image = args.index('anyplot-agents:dev')\n"
            "command = args[image + 1:]\n"
            f"command[0] = {sys.executable!r}\n"
            f"command[command.index('/opt/anyplot/harness.py')] = {str(HARNESS_SOURCE)!r}\n"
            "os.chdir(work)\n"
            "os.execv(command[0], command)\n",
            encoding="utf-8",
        )
        docker.chmod(0o755)
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker=str(docker)
        )
        snippet = "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})\n"

        output = await backend.run_data(DataJob(job_id="d1", source=snippet))
        failed = await backend.run_data(DataJob(job_id="d2", source="x = 1\nraise ValueError('secret')\n"))

        assert output.exit_code == 0 and output.csv_text == "x,y\n1,3\n2,4\n", output.stderr_tail
        assert failed.exit_code == 1 and failed.csv_text is None and 'snippet.py", line 2' in failed.stderr_tail

    async def test_local_backend_converts_a_file(self, tmp_path: Path) -> None:
        """The stand-in `docker` above, with the harness in convert mode: a workbook, then a refused pickle."""
        from tests.unit.agents.runtime.convert_fixtures import Sheet, xlsx

        docker = tmp_path / "docker"
        docker.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "args = sys.argv[1:]\n"
            "if args[0] == 'kill':\n"
            "    sys.exit(0)\n"
            "work = next(v.split(':')[0] for f, v in zip(args, args[1:]) if f == '-v' and v.endswith(':/work'))\n"
            "image = args.index('anyplot-agents:dev')\n"
            "command = args[image + 1:]\n"
            f"command[0] = {sys.executable!r}\n"
            f"command[command.index('/opt/anyplot/harness.py')] = {str(HARNESS_SOURCE)!r}\n"
            "os.environ['ARROW_DEFAULT_MEMORY_POOL'] = 'system'\n"
            "os.chdir(work)\n"
            "os.execv(command[0], command)\n",
            encoding="utf-8",
        )
        docker.chmod(0o755)
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker=str(docker)
        )
        argv = backend.convert_argv(ConvertJob(job_id="c1", data=b"x"), Path("/tmp/run"))
        assert argv[-7:] == [
            "/app/.venv/bin/python",
            "-I",
            "-X",
            "disable-remote-debug",
            "/opt/anyplot/harness.py",
            "--convert",
            "input.bin",
        ]
        assert "ARROW_DEFAULT_MEMORY_POOL=system" in argv and argv[argv.index("--network") + 1] == "none"

        data = xlsx([Sheet("A", [["a"]]), Sheet("B", [["b"], [2]])])
        output = await backend.convert(ConvertJob(job_id="c1", data=data, sheet="B"))
        refused = await backend.convert(ConvertJob(job_id="c2", data=b"\x80\x04K\x01."))

        assert output.exit_code == 0 and output.text == "b\n2\n"
        assert output.meta is not None and output.meta.sheets == ["A", "B"]
        assert refused.refusal == "pickle" and refused.text is None

    async def test_fake_and_sandbox_conversions(self) -> None:
        fake = FakeBackend()
        assert (await fake.convert(ConvertJob(job_id="c1", data=b"x"))).text == FIXTURE_CSV
        assert fake.convert_jobs[0].sheet is None
        with pytest.raises(DataRunUnsupported):
            await SandboxBackend(runtime=PythonRuntime()).convert(ConvertJob(job_id="c1", data=b"x"))
        with pytest.raises(ValueError):
            ConvertJob(job_id="../x", data=b"x")
        with pytest.raises(ValueError):
            ConvertJob(job_id="c1", data=b"x", timeout_s=16)

    async def test_fake_and_sandbox_data_runs(self) -> None:
        fake = FakeBackend()
        assert (await fake.run_data(DataJob(job_id="d1", source="df = 1\n"))).csv_text == FIXTURE_CSV
        assert fake.data_jobs[0].job_id == "d1"
        with pytest.raises(DataRunUnsupported):
            await SandboxBackend(runtime=PythonRuntime()).run_data(DataJob(job_id="d1", source="df = 1\n"))
        with pytest.raises(ValueError):
            DataJob(job_id="../x", source="df = 1\n")
        with pytest.raises(ValueError):
            DataJob(job_id="d1", source="df = 1\n", timeout_s=31)

    def test_local_backend_refuses_production_and_missing_docker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with pytest.raises(RendererUnavailable, match="production"):
            LocalDockerBackend(image="x", runtime=PythonRuntime(), environment="production", docker="/usr/bin/docker")
        monkeypatch.setattr("shutil.which", lambda name: None)
        with pytest.raises(RendererUnavailable, match="Docker"):
            LocalDockerBackend(image="x", runtime=PythonRuntime(), environment="development")

    async def test_in_process_sandbox_backend_is_not_used_in_phase_1(self) -> None:
        with pytest.raises(NotImplementedError, match="not used in phase 1"):
            await SandboxBackend(runtime=PythonRuntime()).render(job())

    async def test_fake_backend_scripts(self) -> None:
        backend = FakeBackend(script=lambda job, theme: FakeOutcome(exit_code=1 if theme == "dark" else 0))
        result = await backend.render(job())

        assert result.outputs["light"].png is not None and result.outputs["dark"].png is None
        assert backend.jobs[0].job_id == "abc123"

    def test_factory(self) -> None:
        assert isinstance(make_backend(AgentSettings(renderer="fake")), FakeBackend)
        assert isinstance(make_backend(AgentSettings(renderer="sandbox")), SandboxBackend)
        with pytest.raises(RendererUnavailable, match="AGENT_RENDER_URL"):
            make_backend(AgentSettings(renderer="remote"))
        remote = make_backend(AgentSettings(renderer="remote", render_url="https://anyplot-renderer.example.run.app/"))
        assert isinstance(remote, RemoteBackend) and remote.url == "https://anyplot-renderer.example.run.app"
        assert isinstance(remote.tokens, IdTokenSource) and remote.tokens.audience == remote.url

    def test_the_local_factory_resolves_a_render_runtime_by_library(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`make_backend` hands the local backend the registry's `runtime_for`, with the render timeout as the
        CPU limit of every runtime it resolves; a library without a runtime is the registry's error."""
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker")
        local = make_backend(AgentSettings(renderer="local", environment="development", render_timeout_s=45))

        assert isinstance(local, LocalDockerBackend) and local.runtime_for is not None
        runtime = local.runtime_for("seaborn")
        assert isinstance(runtime, PythonRuntime) and (runtime.library, runtime.cpu_seconds) == ("seaborn", 45)
        assert isinstance(local.runtime, PythonRuntime) and local.runtime.cpu_seconds == 45  # the data runs' runtime
        with pytest.raises(ValueError, match="no runtime for 'plotly'"):
            local.runtime_for("plotly")

    def test_job_validation(self) -> None:
        with pytest.raises(ValueError):
            job(job_id="../escape")
        with pytest.raises(ValueError):
            job(themes=("sepia",))


class TestRenderStore:
    def test_owned_by_one_session(self) -> None:
        store = RenderStore()
        render_id = store.put("s1", {"light": b"a", "dark": b"b"})

        assert store.get(render_id, "s1") is not None
        assert store.get(render_id, "s2") is None
        assert store.delete_session("s1") == [render_id] and len(store) == 0

    def test_add_theme_joins_the_render_under_the_cap(self) -> None:
        store = RenderStore(max_bytes=6)
        render_id = store.put("s1", {"light": b"ab"})

        store.add_theme(render_id, "s1", "dark", b"cd")
        stored = store.get(render_id, "s1")
        assert stored is not None and stored.pngs == {"light": b"ab", "dark": b"cd"}
        assert store.used_bytes == 4
        store.add_theme(render_id, "s1", "dark", b"cdef")  # a replacement counts only the difference
        assert store.used_bytes == 6
        with pytest.raises(RenderStoreFull):
            store.add_theme(render_id, "s1", "dark", b"cdefg")
        with pytest.raises(KeyError):
            store.add_theme(render_id, "s2", "dark", b"x")  # another session's render is not there

    def test_cap_and_sweep(self) -> None:
        clock = iter([0.0, 0.0, 100.0]).__next__
        store = RenderStore(max_bytes=4, clock=clock)
        store.put("s1", {"light": b"ab"})
        with pytest.raises(RenderStoreFull):
            store.put("s1", {"light": b"abcd"})
        assert len(store.sweep(10, now=100.0)) == 1


class Composer:
    """A `compose` callable for `RenderStore.shown_png` that counts its calls."""

    def __init__(self, suffix: bytes = b"+strip") -> None:
        self.suffix = suffix
        self.calls: list[bytes] = []

    async def __call__(self, raw: bytes) -> bytes:
        self.calls.append(raw)
        return raw + self.suffix


class TestShownPng:
    async def test_the_shown_variant_is_composed_once_and_counted(self) -> None:
        store = RenderStore()
        render_id = store.put("s1", {"light": b"raw"})
        compose = Composer()

        first = await store.shown_png(render_id, "s1", "light", compose)
        second = await store.shown_png(render_id, "s1", "light", compose)

        assert first == second == b"raw+strip"
        assert compose.calls == [b"raw"]  # a hit does not compose again
        stored = store.get(render_id, "s1")
        assert stored is not None
        assert stored.pngs == {"light": b"raw"}  # the raw render stays what the gates and the reviewer saw
        assert stored.shown == {"light": b"raw+strip"}
        assert stored.size_bytes == store.used_bytes == len(b"raw") + len(b"raw+strip")

    async def test_a_missing_render_theme_or_session_composes_nothing(self) -> None:
        store = RenderStore()
        render_id = store.put("s1", {"light": b"raw"})
        compose = Composer()

        assert await store.shown_png(render_id, "s1", "dark", compose) is None
        assert await store.shown_png(render_id, "s2", "light", compose) is None
        assert await store.shown_png("unknown", "s1", "light", compose) is None
        assert compose.calls == []

    async def test_a_variant_over_the_cap_is_served_uncached(self) -> None:
        store = RenderStore(max_bytes=10)
        render_id = store.put("s1", {"light": b"raw"})
        compose = Composer()

        assert await store.shown_png(render_id, "s1", "light", compose) == b"raw+strip"
        assert await store.shown_png(render_id, "s1", "light", compose) == b"raw+strip"

        assert len(compose.calls) == 2
        assert store.used_bytes == 3
        stored = store.get(render_id, "s1")
        assert stored is not None and stored.shown == {}

    async def test_add_theme_drops_that_themes_variant_only(self) -> None:
        store = RenderStore()
        render_id = store.put("s1", {"light": b"raw", "dark": b"night"})
        compose = Composer()
        await store.shown_png(render_id, "s1", "light", compose)
        await store.shown_png(render_id, "s1", "dark", compose)

        store.add_theme(render_id, "s1", "light", b"padded")

        stored = store.get(render_id, "s1")
        assert stored is not None
        assert stored.shown == {"dark": b"night+strip"}
        assert store.used_bytes == len(b"padded") + len(b"night") + len(b"night+strip")
        assert await store.shown_png(render_id, "s1", "light", compose) == b"padded+strip"

    async def test_a_theme_replaced_while_composing_keeps_no_stale_variant(self) -> None:
        store = RenderStore()
        render_id = store.put("s1", {"light": b"old"})

        async def compose(raw: bytes) -> bytes:
            store.add_theme(render_id, "s1", "light", b"new")  # the toggle lands mid-composition
            return raw + b"+strip"

        assert await store.shown_png(render_id, "s1", "light", compose) == b"old+strip"
        stored = store.get(render_id, "s1")
        assert stored is not None and stored.shown == {}
        assert store.used_bytes == len(b"new")

    async def test_cached_variants_give_way_to_renders(self) -> None:
        store = RenderStore(max_bytes=20)
        render_id = store.put("s1", {"light": b"raw"})
        await store.shown_png(render_id, "s1", "light", Composer())
        assert store.used_bytes == 12

        store.put("s1", {"light": b"0123456789"})  # fits only once the cached variant is gone

        stored = store.get(render_id, "s1")
        assert stored is not None and stored.shown == {}
        assert store.used_bytes == 13

    async def test_delete_and_sweep_free_the_variants_too(self) -> None:
        store = RenderStore()
        first = store.put("s1", {"light": b"raw"})
        second = store.put("s2", {"dark": b"night"})
        await store.shown_png(first, "s1", "light", Composer())
        await store.shown_png(second, "s2", "dark", Composer())

        assert store.delete_session("s1") == [first]
        assert store.used_bytes == len(b"night") + len(b"night+strip")
        assert store.sweep(0, now=float("inf")) == [second]
        assert store.used_bytes == 0
