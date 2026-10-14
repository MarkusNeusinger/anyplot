"""Tests for agents/renderer/wire.py and settings.py, and for what the renderer package may import."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import MAX_INPUT_BYTES
from agents.anyplot.plugins.tool_safety import MAX_DATA_CODE_CHARS
from agents.anyplot.render import contract, harness, png
from agents.anyplot.schemas import RENDER_ID_PATTERN
from agents.renderer import executor, wire
from agents.renderer.settings import RendererSettings

from .helpers import job


REPO_ROOT = Path(__file__).resolve().parents[4]


class TestContract:
    def test_limits_shared_with_the_agents_side_are_equal(self) -> None:
        """The renderer cannot import agents.anyplot (it loads ADK), so the pins live here."""
        assert wire.MAX_PNG_BYTES == png.MAX_PNG_BYTES
        assert wire.MAX_PROBE_BYTES == png.MAX_PROBE_BYTES
        assert wire.MAX_STDERR_CHARS == contract.MAX_STDERR_CHARS
        assert wire.JOB_ID_PATTERN == RENDER_ID_PATTERN
        assert wire.MAX_CSV_BYTES == MAX_INPUT_BYTES == harness.DATA_MAX_CSV_BYTES
        assert executor.OUT_FILE == harness.DATA_OUT_FILE and executor.DATA_FLAG == harness.DATA_FLAG
        assert wire.DATA_STATUS_FILE == harness.DATA_STATUS_FILE
        assert max(harness.DATA_EXIT.values()) <= wire.MAX_DATA_EXIT

    def test_the_data_status_parses_only_its_own_shape(self) -> None:
        status = wire.parse_data_status(b'{"exit": 7, "reason": "too_large", "measured": 637727, "limit": 204800}')
        assert status is not None and (status.exit, status.measured, status.limit) == (7, 637727, 204800)
        assert wire.parse_data_status(b'{"exit": 0, "reason": "ok"}') == wire.DataStatus(exit=0)
        for raw in (None, b"", b"[]", b'{"exit": "7"}', b'{"exit": -1}', b'{"exit": 1.5}', b"x" * 2000):
            assert wire.parse_data_status(raw) is None
        assert wire.MAX_DATA_SOURCE_CHARS >= MAX_DATA_CODE_CHARS
        assert wire.MAX_DATA_TIMEOUT_S == contract.MAX_DATA_TIMEOUT_S

    def test_a_data_run_request_is_bounded_and_closed(self) -> None:
        good = {"job_id": "d1", "source": "df = 1\n", "timeout_s": 10}
        assert wire.DataRunRequest.model_validate(good).timeout_s == 10
        for overrides in (
            {"timeout_s": wire.MAX_DATA_TIMEOUT_S + 1},
            {"timeout_s": 0},
            {"source": ""},
            {"source": "x" * (wire.MAX_DATA_SOURCE_CHARS + 1)},
            {"job_id": "../x"},
            {"themes": ["light"]},
            {"kind": "data"},
        ):
            with pytest.raises(ValidationError):
                wire.DataRunRequest.model_validate({**good, **overrides})

    def test_a_data_run_answer_is_closed(self) -> None:
        with pytest.raises(ValidationError):
            wire.DataRun.model_validate({"exit_code": 0, "png_base64": "x"})
        with pytest.raises(ValidationError):
            wire.DataRun.model_validate({"exit_code": 0, "csv_text": "x" * (wire.MAX_CSV_BYTES + 1)})

    def test_a_job_names_distinct_known_themes_and_a_bounded_timeout(self) -> None:
        assert job(themes=("light", "dark")).themes == ["light", "dark"]
        for overrides in ({"themes": []}, {"themes": ["light", "light"]}, {"themes": ["sepia"]}, {"timeout_s": 0}):
            with pytest.raises(ValidationError):
                wire.RenderRequest.model_validate({**job().model_dump(), **overrides})
        with pytest.raises(ValidationError):
            wire.RenderRequest.model_validate({**job().model_dump(), "timeout_s": wire.MAX_TIMEOUT_S + 1})


class TestCleanProbe:
    def test_a_harness_probe_passes_and_nan_becomes_null(self) -> None:
        raw = b'{"canvas": [3200, 1800], "texts": [{"box": [1.5, 2, NaN, Infinity]}], "tick_overlaps": 0}'

        assert wire.clean_probe(raw) == {
            "canvas": [3200, 1800],
            "texts": [{"box": [1.5, 2, None, None]}],
            "tick_overlaps": 0,
        }

    @pytest.mark.parametrize(
        "raw",
        [
            None,
            b"",
            b"[1, 2]",
            b"not json",
            b"\xff\xfe",
            b'{"a": ' + b"[" * 16 + b"]" * 16 + b"}",
            b'{"a": ' + b"[" * 5000 + b"]" * 5000 + b"}",
            b'{"big": 1' + b"0" * 400 + b"}",
            b'{"big": 1e999}',
        ],
    )
    def test_anything_the_wire_cannot_carry_is_dropped(self, raw: bytes | None) -> None:
        assert wire.clean_probe(raw) is None

    def test_a_missing_glyphs_object_passes_clean_probe(self) -> None:
        """The harness's G10 field crosses the wire unchanged."""
        raw = b'{"missing_glyphs": {"count": 3, "math": 1, "sample": [38144, 57344]}}'

        assert wire.clean_probe(raw) == {"missing_glyphs": {"count": 3, "math": 1, "sample": [38144, 57344]}}

    def test_the_depth_limit_counts_the_object_itself(self) -> None:
        nested = b'{"a": ' + b"[" * 15 + b"]" * 15 + b"}"

        assert wire.clean_probe(nested) is not None


class TestPackage:
    def test_the_renderer_imports_neither_adk_nor_the_agents_runtime_nor_core(self) -> None:
        """The image holds only `agents/renderer/` and the plotting venv: no ADK, no `agents/anyplot/`, no `core/`."""
        code = (
            "import sys\n"
            "import agents.renderer.main\n"
            "loaded = [name for name in sys.modules if name.startswith(('google.adk', 'agents.anyplot', 'core.'))\n"
            "          or name == 'core']\n"
            "assert not loaded, loaded\n"
        )
        env = {**os.environ, "PYTHON_DOTENV_DISABLED": "1"}
        done = subprocess.run(
            [sys.executable, "-c", code], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120
        )

        assert done.returncode == 0, done.stderr[-2000:]

    def test_the_renderer_directory_is_no_adk_agent(self) -> None:
        """`adk web agents` lists every subdirectory with an `__init__.py` as an agent."""
        renderer = REPO_ROOT / "agents" / "renderer"

        assert not (renderer / "__init__.py").exists() and not (renderer / "agent.py").exists()


class TestSettings:
    def test_defaults_are_the_deployed_values(self) -> None:
        settings = RendererSettings()

        assert settings.environment == "production" and not settings.is_development
        assert settings.allowed_callers == [] and settings.audiences == []
        assert settings.runs_dir == "/tmp/runs" and settings.run_budget_mb == 64
        assert settings.slot_wait_s == 30 and settings.min_mem_available_mb == 1024
        assert settings.kill_mem_available_mb == 512 and settings.runs_volume_max_mb == 1024
        assert (settings.rlimit_cpu_s, settings.rlimit_fsize_mb, settings.rlimit_as_mb, settings.rlimit_nproc) == (
            60,
            50,
            1024,
            64,
        )
        assert settings.bind_tmp is False

    def test_lists_and_values_come_from_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RENDERER_ALLOWED_CALLERS", "a@x.iam.gserviceaccount.com,,b@example.com ")
        monkeypatch.setenv("RENDERER_AUDIENCES", "")
        monkeypatch.setenv("RENDERER_RUN_BUDGET_MB", "32")
        monkeypatch.setenv("K_REVISION", "anyplot-renderer-b123")

        settings = RendererSettings()

        assert settings.allowed_callers == ["a@x.iam.gserviceaccount.com", "b@example.com"]
        assert settings.audiences == [] and settings.run_budget_mb == 32
        assert settings.revision == "anyplot-renderer-b123"

    def test_paths_must_be_absolute(self) -> None:
        with pytest.raises(ValidationError, match="absolute"):
            RendererSettings(runs_dir="runs")
