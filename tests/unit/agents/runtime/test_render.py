"""Tests for agents/anyplot/render/: PNG hardening, gates, the harness and the backends."""

import asyncio
import io
import json
import os
import subprocess
import sys
import tracemalloc
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from agents.anyplot.code.edits import apply_plan
from agents.anyplot.code.loader import to_run_form
from agents.anyplot.code.normalise import normalise
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.render import make_backend
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome, fixture_png
from agents.anyplot.render.backends.local import LocalDockerBackend, read_tail
from agents.anyplot.render.backends.sandbox import SandboxBackend
from agents.anyplot.render.contract import THEMES, RendererUnavailable, RenderJob, RenderResult, Theme, ThemeOutput
from agents.anyplot.render.gates import data_rows, error_summary, evaluate
from agents.anyplot.render.png import PngRejected, harden, pad_to, read_output, size_of
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE, PythonRuntime
from agents.anyplot.render.store import RenderStore, RenderStoreFull
from agents.anyplot.schemas import AdaptPlan
from agents.anyplot.settings import AgentSettings

from .conftest import CASES
from .fakes import SCATTER_PLAN


BOTH: tuple[Theme, ...] = THEMES


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
        probe = json.loads((tmp_path / "probe-light.json").read_text())
        assert probe["canvas"] == [3200, 1800]
        assert probe["points"] == 24

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
        docker = tmp_path / "docker"
        docker.write_text(f'#!/bin/sh\nif [ "$1" = kill ]; then echo "$2" >> {killed}; exit 0; fi\nexec sleep 30\n')
        docker.chmod(0o755)
        backend = LocalDockerBackend(
            image="anyplot-agents:dev", runtime=PythonRuntime(), environment="development", docker=str(docker)
        )

        task = asyncio.create_task(backend.render(job(job_id="cancelme")))
        await asyncio.sleep(0.5)
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
        assert argv[-4:] == ["/app/.venv/bin/python", "-I", "/opt/anyplot/harness.py", "plot.py"]
        assert "ANYPLOT_THEME=light" in argv

    def test_local_backend_refuses_production_and_missing_docker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with pytest.raises(RendererUnavailable, match="production"):
            LocalDockerBackend(image="x", runtime=PythonRuntime(), environment="production", docker="/usr/bin/docker")
        monkeypatch.setattr("shutil.which", lambda name: None)
        with pytest.raises(RendererUnavailable, match="Docker"):
            LocalDockerBackend(image="x", runtime=PythonRuntime(), environment="development")

    async def test_sandbox_backend_waits_for_spike_s(self) -> None:
        with pytest.raises(NotImplementedError, match="spike S"):
            await SandboxBackend(runtime=PythonRuntime()).render(job())

    async def test_fake_backend_scripts(self) -> None:
        backend = FakeBackend(script=lambda job, theme: FakeOutcome(exit_code=1 if theme == "dark" else 0))
        result = await backend.render(job())

        assert result.outputs["light"].png is not None and result.outputs["dark"].png is None
        assert backend.jobs[0].job_id == "abc123"

    def test_factory(self) -> None:
        assert isinstance(make_backend(AgentSettings(renderer="fake")), FakeBackend)
        assert isinstance(make_backend(AgentSettings(renderer="sandbox")), SandboxBackend)
        with pytest.raises(RendererUnavailable):
            make_backend(AgentSettings(renderer="remote"))

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
