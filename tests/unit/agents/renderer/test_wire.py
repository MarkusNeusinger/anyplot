"""Tests for agents/renderer/wire.py and settings.py, and for what the renderer package may import."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.anyplot.render import contract, png
from agents.anyplot.schemas import RENDER_ID_PATTERN
from agents.renderer import wire
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

    def test_a_job_names_distinct_known_themes_and_a_bounded_timeout(self) -> None:
        assert job(themes=("light", "dark")).themes == ["light", "dark"]
        for overrides in ({"themes": []}, {"themes": ["light", "light"]}, {"themes": ["sepia"]}, {"timeout_s": 0}):
            with pytest.raises(ValidationError):
                wire.RenderRequest.model_validate({**job().model_dump(), **overrides})
        with pytest.raises(ValidationError):
            wire.RenderRequest.model_validate({**job().model_dump(), "timeout_s": wire.MAX_TIMEOUT_S + 1})


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
