"""Tests for core/smoke_run.py: the perturbation smoke run, the render pair and the generator's self-check.

The fixtures are the bar-grouped example of docs/concepts/adaptable-code.md (it passes) and a
variant with a fixed bar width, an unguarded index into the second-largest bar and a callout
typed as "Near-tie in Q3" (it fails). Every run uses the light theme only and a minimal spec,
so the module stays at a few seconds and needs no network.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from core import smoke_run
from core.smoke_run import (
    SmokeRun,
    code_sha256,
    execute,
    execution_env,
    line_map,
    main,
    pair,
    pair_exit_code,
    run,
    selfcheck,
    stale_labels,
    traceback_error,
)


FIXTURES = Path(__file__).parent / "fixtures" / "adaptability"
PASSING = (FIXTURES / "bar_grouped_matplotlib.py").read_text(encoding="utf-8")
SPEC = """# bar-grouped: Grouped Bar Chart

## Data

- `category` (categorical) - Labels for each group of bars on the x-axis
- `group` (categorical) - The different series being compared (creates side-by-side bars)
- `value` (numeric) - Heights of the bars

## Notes

- Minimal spec for the smoke-run tests.
"""
LIGHT = ("light",)


def _replace(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, old
    return source.replace(old, new)


FAILING = _replace(
    _replace(
        _replace(PASSING, "width = 0.8 / len(table.columns)", "width = 0.25"),
        "if len(table.columns) > 1:\n",
        "if True:\n",
    ),
    'f"Near-tie in {table.index[tie]}"',
    '"Near-tie in Q3"',
)
SECOND_LARGEST_LINE = FAILING.splitlines().index("    gaps = ranked[:, -1] - ranked[:, -2]") + 1
STATIC_FAILING = _replace(
    FAILING,
    'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]',
    'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]',
)
"""The failing variant with three palette positions, which the static palette rule rejects."""


def _catalogue(root: Path, source: str, library: str = "matplotlib", spec_id: str = "bar-grouped") -> Path:
    """`plots/<spec>/implementations/python/<library>.py` with its specification.md under `root`."""
    spec_dir = root / "plots" / spec_id
    impl = spec_dir / "implementations" / "python" / f"{library}.py"
    impl.parent.mkdir(parents=True, exist_ok=True)
    (spec_dir / "specification.md").write_text(SPEC, encoding="utf-8")
    impl.write_text(source, encoding="utf-8")
    return impl


@pytest.fixture(scope="module")
def passing_run(tmp_path_factory: pytest.TempPathFactory) -> SmokeRun:
    return run(_catalogue(tmp_path_factory.mktemp("pass"), PASSING), themes=LIGHT)


@pytest.fixture(scope="module")
def failing_run(tmp_path_factory: pytest.TempPathFactory) -> SmokeRun:
    return run(_catalogue(tmp_path_factory.mktemp("fail"), FAILING), themes=LIGHT)


def _result(smoke: SmokeRun, name: str) -> dict[str, object]:
    (found,) = [result for result in smoke.results if result["name"] == name]
    return found


class TestRun:
    def test_the_example_passes_every_binding_perturbation(self, passing_run: SmokeRun) -> None:
        record = passing_run.to_dict()
        assert (record["status"], record["why"], record["failed"]) == ("pass", "-", [])
        assert passing_run.exit_code() == 0
        assert record["shape"] == "table" and record["color_role"] == "group" and record["static_status"] == "pass"
        assert record["sample"] == {
            "status": "pass",
            "rows": 12,
            "columns": {"category": "Quarter", "group": "Product line", "value": "Sales (thousand USD)"},
            "error": None,
            "line": None,
        }
        names = [result["name"] for result in passing_run.results]
        assert names[:7] == [
            "renamed",
            "more_categories",
            "fewer_categories",
            "single_group",
            "fewer_rows",
            "more_rows",
            "scaled",
        ]
        assert set(names[7:]) <= {"missing_number", "missing_nullable"}
        assert _result(passing_run, "renamed")["canvas"] == {"light": "3200x1800"}
        assert _result(passing_run, "renamed")["stale_labels"] == []

    def test_the_record_carries_the_pinned_fields(self, passing_run: SmokeRun) -> None:
        record = passing_run.to_dict()
        assert record["v"] == 1 and record["tool"] == "core.smoke_run run" and record["checker_version"] == 1
        assert (record["spec"], record["library"], record["language"], record["themes"]) == (
            "bar-grouped",
            "matplotlib",
            "python",
            ["light"],
        )
        assert record["code_sha256"] == code_sha256(PASSING)
        for result in passing_run.results:
            assert set(result) == {
                "name",
                "description",
                "advisory",
                "status",
                "rows",
                "theme",
                "error",
                "line",
                "code",
                "canvas",
                "stale_labels",
                "seconds",
            }
        json.dumps(record)  # serializable as it stands

    def test_an_unguarded_second_largest_index_fails_the_single_group(self, failing_run: SmokeRun) -> None:
        # The design's point: this draft passes every static rule, only the smoke run finds the crash.
        assert failing_run.to_dict()["static_status"] == "pass"
        assert (failing_run.status, failing_run.why) == ("fail", "perturbation_failed")
        assert failing_run.exit_code() == 1
        single = _result(failing_run, "single_group")
        assert single["status"] == "fail" and single["theme"] == "light"
        assert str(single["error"]).startswith("IndexError")
        assert single["line"] == SECOND_LARGEST_LINE  # the original source's line, not the smoke file's
        assert single["code"] == "gaps = ranked[:, -1] - ranked[:, -2]"
        assert "single_group" in failing_run.failed

    def test_a_typed_callout_is_a_stale_label_on_renamed_data(self, failing_run: SmokeRun) -> None:
        renamed = _result(failing_run, "renamed")
        assert renamed["status"] == "fail" and renamed["line"] is None
        assert renamed["stale_labels"] == ["Near-tie in Q3"]
        assert renamed["error"] == "stale label: 'Near-tie in Q3' shows the retired category 'Q3'"
        assert renamed["canvas"] == {"light": "3200x1800"}  # the render itself was fine

    def test_the_summary_names_each_failure(self, failing_run: SmokeRun) -> None:
        lines = failing_run.summary()
        assert lines[0].startswith("smoke_run bar-grouped matplotlib: fail (perturbation_failed): ")
        (single,) = [line for line in lines if line.startswith("  single_group")]
        assert f"FAIL  line {SECOND_LARGEST_LINE}: IndexError" in single
        assert single.endswith("|  gaps = ranked[:, -1] - ranked[:, -2]")

    def test_a_block_without_df_fails_the_sample(self, tmp_path: Path) -> None:
        source = _replace(PASSING, "df = pd.DataFrame(\n", "frame = pd.DataFrame(\n")
        smoke = run(_catalogue(tmp_path, source), themes=LIGHT)
        assert (smoke.status, smoke.why, smoke.results) == ("fail", "sample_failed", [])
        assert smoke.sample is not None and smoke.sample["status"] == "fail"
        assert "binds no df" in str(smoke.sample["error"])

    def test_a_raising_block_reports_its_line(self, tmp_path: Path) -> None:
        source = _replace(PASSING, "df = pd.DataFrame(\n", "raise ValueError('no sample')\ndf = pd.DataFrame(\n")
        smoke = run(_catalogue(tmp_path, source), themes=LIGHT)
        assert smoke.why == "sample_failed" and smoke.sample is not None
        assert smoke.sample["error"] == "ValueError: no sample"
        assert smoke.sample["line"] == source.splitlines().index("raise ValueError('no sample')") + 1

    def test_skip_if_static_fails_runs_nothing(self, tmp_path: Path) -> None:
        smoke = run(_catalogue(tmp_path, STATIC_FAILING), themes=LIGHT, skip_if_static_fails=True)
        assert (smoke.status, smoke.why, smoke.results, smoke.sample) == ("skipped", "static_failed", [], None)
        assert smoke.to_dict()["static_status"] == "fail" and smoke.exit_code() == 0

    @pytest.mark.parametrize(
        ("spec_id", "why"), [("maze-circular", "shape:generated"), ("choropleth-basic", "shape:excluded")]
    )
    def test_shapes_without_a_table_skip_without_probing(self, tmp_path: Path, spec_id: str, why: str) -> None:
        impl = _catalogue(tmp_path, PASSING)
        smoke = run(impl, spec_id=spec_id, themes=LIGHT)
        assert (smoke.status, smoke.why, smoke.sample) == ("skipped", why, None)

    def test_no_block_is_skipped(self, tmp_path: Path) -> None:
        source = _replace(PASSING, "# Plot: reads only df", "# Drawing: reads only df")
        smoke = run(_catalogue(tmp_path, source), themes=LIGHT)
        assert (smoke.status, smoke.why) == ("skipped", "no_block")

    def test_other_languages_are_not_python(self, tmp_path: Path) -> None:
        impl = tmp_path / "ggplot2.R"
        impl.write_text("library(ggplot2)\n", encoding="utf-8")
        smoke = run(impl)
        assert (smoke.status, smoke.why, smoke.exit_code()) == ("skipped", "not_python", 0)
        assert smoke.to_dict()["language"] == "r"

    @pytest.mark.parametrize(
        ("file_name", "library", "python", "message"),
        [
            ("missing.py", "matplotlib", None, "cannot read the source"),
            ("plot.py", None, None, "pass --library"),
            ("plot.py", "excel", None, "unknown library"),
            ("plot.py", "matplotlib", "/nonexistent/python", "no Python interpreter"),
        ],
    )
    def test_a_run_that_cannot_happen_is_a_runner_error(
        self, tmp_path: Path, file_name: str, library: str | None, python: str | None, message: str
    ) -> None:
        spec = _catalogue(tmp_path, PASSING).parents[2] / "specification.md"
        source = tmp_path / file_name
        if file_name == "plot.py":
            source.write_text(PASSING, encoding="utf-8")
        smoke = run(source, spec_path=spec, library=library, python=python)
        assert (smoke.status, smoke.why, smoke.exit_code()) == ("skipped", "runner_error", 2)
        assert message in str(smoke.error)
        assert smoke.to_dict()["error"] == smoke.error

    def test_the_cli_writes_the_record_and_exits_by_status(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = tmp_path / "out" / "smoke.json"
        impl = tmp_path / "ggplot2.R"
        impl.write_text("library(ggplot2)\n", encoding="utf-8")
        assert main(["run", str(impl), "--out", str(out)]) == 0
        assert json.loads(out.read_text(encoding="utf-8"))["why"] == "not_python"
        assert main(["run", str(tmp_path / "nothing.py"), "--library", "matplotlib", "--out", str(out)]) == 2
        record = json.loads(out.read_text(encoding="utf-8"))
        assert (record["status"], record["why"]) == ("skipped", "runner_error")
        assert "smoke_run" in capsys.readouterr().out


class TestPair:
    def test_the_same_source_renders_identical(self, tmp_path: Path) -> None:
        new, prev = tmp_path / "new" / "matplotlib.py", tmp_path / "prev" / "matplotlib.py"
        for path in (new, prev):
            path.parent.mkdir()
            path.write_text(PASSING, encoding="utf-8")
        out = tmp_path / "adapt"
        record = pair(new, prev, out, themes=LIGHT)
        assert (record["status"], record["why"], pair_exit_code(record)) == ("identical", "-", 0)
        assert (out / "new" / "plot-light.png").is_file() and (out / "prev" / "plot-light.png").is_file()
        identity = record["identity"]
        assert isinstance(identity, dict) and identity["light"]["fraction"] == 0.0 and identity["light"]["passed"]
        new_side = record["new"]
        assert isinstance(new_side, dict) and new_side["code_sha256"] == code_sha256(PASSING)
        assert new_side["renders"]["light"]["status"] == "ok" and new_side["renders"]["light"]["size"] == [3200, 1800]

    def test_another_palette_is_different(self, tmp_path: Path) -> None:
        new, prev = tmp_path / "matplotlib.py", tmp_path / "prev" / "matplotlib.py"
        new.write_text(PASSING, encoding="utf-8")
        prev.parent.mkdir()
        prev.write_text(_replace(PASSING, 'IMPRINT = ["#009E73"', 'IMPRINT = ["#000000"'), encoding="utf-8")
        record = pair(new, prev, tmp_path / "adapt", themes=LIGHT)
        assert (record["status"], record["why"], pair_exit_code(record)) == ("different", "identity_light", 1)

    def test_a_failing_predecessor_is_an_error(self, tmp_path: Path) -> None:
        new, prev = tmp_path / "matplotlib.py", tmp_path / "prev" / "matplotlib.py"
        new.write_text(PASSING, encoding="utf-8")
        prev.parent.mkdir()
        prev.write_text("raise SystemExit('broken predecessor')\n", encoding="utf-8")
        record = pair(new, prev, tmp_path / "adapt", themes=LIGHT)
        assert (record["status"], record["why"], record["identity"]) == ("error", "prev_render_failed", None)
        assert pair_exit_code(record) == 2
        prev_side = record["prev"]
        assert isinstance(prev_side, dict) and "broken predecessor" in str(prev_side["error"])
        assert not (tmp_path / "adapt" / "prev" / "plot-light.png").exists()

    def test_a_non_python_library_is_an_error(self, tmp_path: Path) -> None:
        record = pair(tmp_path / "ggplot2.R", tmp_path / "prev.R", tmp_path / "adapt", themes=LIGHT)
        assert (record["status"], record["why"], pair_exit_code(record)) == ("error", "new_render_failed", 2)


class TestSelfcheck:
    def test_attempts_are_logged_and_counted(self, tmp_path: Path, passing_run: SmokeRun) -> None:
        impl = _catalogue(tmp_path, PASSING)
        log, static, smoke = tmp_path / "log.jsonl", tmp_path / "static.json", tmp_path / "smoke.json"
        for attempt in (1, 2):
            code, lines = selfcheck(impl, log=log, static_out=static, smoke_out=smoke, runner=lambda _: passing_run)
            assert code == 0
            assert lines[-1] == f"selfcheck attempt {attempt}: pass"
        entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        assert [entry["attempt"] for entry in entries] == [1, 2]
        assert entries[0]["static"] == "pass" and entries[0]["smoke"] == "pass" and entries[0]["failed"] == []
        assert entries[0]["code_sha256"] == code_sha256(PASSING)
        assert set(entries[0]) == {
            "at",
            "attempt",
            "code_sha256",
            "static",
            "classes",
            "advisory",
            "smoke",
            "failed",
            "advisory_failed",
        }
        assert json.loads(static.read_text(encoding="utf-8"))["status"] == "pass"
        assert json.loads(smoke.read_text(encoding="utf-8"))["status"] == "pass"

    def test_a_static_failure_fails_the_selfcheck(self, tmp_path: Path, passing_run: SmokeRun) -> None:
        impl = _catalogue(tmp_path, STATIC_FAILING)
        log = tmp_path / "log.jsonl"
        code, lines = selfcheck(
            impl,
            log=log,
            static_out=tmp_path / "static.json",
            smoke_out=tmp_path / "smoke.json",
            runner=lambda _: passing_run,
        )
        assert code == 1
        entry = json.loads(log.read_text(encoding="utf-8"))
        assert entry["static"] == "fail" and "palette" in entry["classes"]
        assert any(line.startswith("CQ-01 (code):") for line in lines)

    def test_a_skipped_shape_passes_but_a_failed_smoke_run_does_not(
        self, tmp_path: Path, failing_run: SmokeRun
    ) -> None:
        impl = _catalogue(tmp_path, PASSING)
        paths = {"log": tmp_path / "log.jsonl", "static_out": tmp_path / "s.json", "smoke_out": tmp_path / "m.json"}
        skipped = SmokeRun(impl, "matplotlib", LIGHT, status="skipped", why="shape:generated")
        assert selfcheck(impl, runner=lambda _: skipped, **paths)[0] == 0
        assert selfcheck(impl, runner=lambda _: failing_run, **paths)[0] == 1

    def test_an_unknown_file_name_is_an_input_error(self, tmp_path: Path) -> None:
        assert selfcheck(tmp_path / "plot.py", log=tmp_path / "log.jsonl")[0] == 2


class TestHelpers:
    def test_code_sha256_ignores_the_header(self) -> None:
        rescored = PASSING.replace("Quality: pending | Created: 2026-10-23", "Quality: 91/100 | Updated: 2026-11-02")
        assert rescored != PASSING and code_sha256(rescored) == code_sha256(PASSING)
        assert code_sha256(PASSING + "\nprint(1)\n") != code_sha256(PASSING)
        assert code_sha256("x = 1\n") == code_sha256("\n\nx = 1")

    def test_the_traceback_names_the_innermost_line_of_the_script(self, tmp_path: Path) -> None:
        script = tmp_path / "matplotlib.py"
        stderr = (
            "Traceback (most recent call last):\n"
            f'  File "{script}", line 12, in <module>\n'
            "    draw()\n"
            f'  File "{script}", line 7, in draw\n'
            "    values[3]\n"
            "    ~~~~~~^^^\n"
            '  File "/usr/lib/python3/site-packages/numpy/core.py", line 99, in f\n'
            "IndexError: list index out of range\n"
            "Exception ignored in: <function Service.__del__ at 0x7f>\n"
            "Traceback (most recent call last):\n"
            '  File "/site-packages/selenium/service.py", line 3, in __del__\n'
            "AttributeError: 'NoneType' object has no attribute 'close'\n"
        )
        assert traceback_error(stderr, script) == ("IndexError: list index out of range", 7)

    def test_a_syntax_error_has_no_traceback_header(self, tmp_path: Path) -> None:
        script = tmp_path / "matplotlib.py"
        stderr = f"  File \"{script}\", line 3\n    x = (\n        ^\nSyntaxError: '(' was never closed\n"
        assert traceback_error(stderr, script) == ("SyntaxError: '(' was never closed", 3)

    def test_without_a_traceback_the_last_line_is_the_error(self, tmp_path: Path) -> None:
        assert traceback_error("warning: x\nsmoke_run: the Data block binds no df\n", tmp_path / "a.py") == (
            "smoke_run: the Data block binds no df",
            None,
        )

    def test_line_map_shifts_the_lines_below_the_block(self) -> None:
        original = "A = 1  # role: x\n# Data\nx = 1\ny = 2\nz = 3\n# Plot\nplot()\nsave()\n"
        executed = "A = 2  # role: x\n# Data\ndf = read()\n\n# Plot\nplot()\nsave()\n"
        mapping = line_map(original, executed)
        assert mapping[6] == 7 and mapping[7] == 8  # plot() and save()
        assert mapping[2] == 2 and mapping[1] == 1
        assert 3 <= mapping[3] <= 5  # inside the replaced block

    def test_stale_labels_skip_prose_numbers_and_the_title(self) -> None:
        retired = frozenset({"Q3", "Total", "2024", "A", "Home & Garden"})
        texts = ["Near-tie in Q3", "Q30 forecast", "Total sales", "2024", "A", "Home & Garden", "x · anyplot.ai Q3"]
        assert stale_labels(texts, retired) == [("Near-tie in Q3", "Q3"), ("Home & Garden", "Home & Garden")]

    def test_the_execution_env_is_the_pipelines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PYTHONPATH", "/runner/tools")
        env = execution_env("dark")
        assert "PYTHONPATH" not in env
        assert {
            key: env[key] for key in ("ANYPLOT_THEME", "MPLBACKEND", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE")
        } == {"ANYPLOT_THEME": "dark", "MPLBACKEND": "Agg", "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}

    def test_a_timeout_kills_the_process_group(self, tmp_path: Path) -> None:
        marker = tmp_path / "survived"
        child = f"import time, pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).touch()"
        code = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(30)"
        execution = execute([sys.executable, "-c", code], tmp_path, execution_env("light"), timeout=0.5)
        assert execution.timed_out and execution.seconds < 10
        time.sleep(1.5)
        assert not marker.exists()  # the grandchild died with the group

    def test_workers_are_fewer_for_chrome_libraries(self) -> None:
        assert smoke_run.LIBRARY_WORKERS == {"bokeh": 2, "plotly": 2}
        assert smoke_run.DEFAULT_WORKERS == 4
