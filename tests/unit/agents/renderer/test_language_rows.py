"""The renderer runs a job by its row of the command table: the argv, the environment, the limits, the toolchain check."""

from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.renderer import executor as executor_module
from agents.renderer.commands import EXEC_FLAG, LANGUAGES, command_for
from agents.renderer.executor import SANDBOX_PATH, ExecutorConfig, SandboxExecutor, build_argv, sandbox_env
from agents.renderer.wire import RendererStatus, RenderRequest

from .helpers import job


def envs(argv: list[str]) -> dict[str, str]:
    return dict(argv[index + 1].split("=", 1) for index, part in enumerate(argv) if part == "--env")


class TestRows:
    def test_a_python_row_is_the_plot_mode_command_as_before(self, config: ExecutorConfig, tmp_path: Path) -> None:
        with_row = build_argv(config, "r-a-light", tmp_path, "light", 60, command=command_for("python", "seaborn"))
        without = build_argv(config, "r-a-light", tmp_path, "light", 60)

        assert with_row == without
        assert with_row[-1] == "plot.py" and EXEC_FLAG not in with_row

    def test_a_non_python_row_runs_its_command_through_exec_mode(self, config: ExecutorConfig, tmp_path: Path) -> None:
        argv = build_argv(config, "r-a-light", tmp_path, "light", 60, command=command_for("r", "ggplot2"))

        assert argv[argv.index(config.harness) :] == [config.harness, EXEC_FLAG, "--", "Rscript", "plot.R"]
        values = envs(argv)
        assert values["ANYPLOT_THEME"] == "light" and values["PATH"] == SANDBOX_PATH
        assert "MPLBACKEND" not in values and values["XDG_CACHE_HOME"] == "/tmp"

    def test_a_row_switches_the_limits_it_cannot_live_under(self, config: ExecutorConfig) -> None:
        limited = replace(config, rlimit_as_mb=1024, rlimit_nproc=64)

        r = sandbox_env(limited, "dark", 60, command=command_for("r", "ggplot2"))
        assert r["ANYPLOT_RLIMIT_AS_MB"] == "1024" and r["ANYPLOT_RLIMIT_NPROC"] == "64"
        js = sandbox_env(limited, "dark", 60, command=command_for("javascript", "muix"))
        assert "ANYPLOT_RLIMIT_AS_MB" not in js and "ANYPLOT_RLIMIT_NPROC" not in js
        assert js["PLAYWRIGHT_BROWSERS_PATH"] == "/opt/pw-browsers" and js["ANYPLOT_RLIMIT_CPU_S"] == "60"
        julia = sandbox_env(limited, "dark", 60, command=command_for("julia", "makie"))
        assert "ANYPLOT_RLIMIT_AS_MB" not in julia and julia["ANYPLOT_RLIMIT_NPROC"] == "64"
        altair = sandbox_env(limited, "dark", 60, command=command_for("python", "altair"))
        assert "ANYPLOT_RLIMIT_AS_MB" not in altair and altair["ANYPLOT_RLIMIT_NPROC"] == "64"
        assert altair["MPLBACKEND"] == "Agg"  # a Python row keeps the Python environment
        # Data runs and conversions never carry a row and keep every limit.
        data = sandbox_env(limited, None, 20)
        assert data["ANYPLOT_RLIMIT_AS_MB"] == "1024" and "ANYPLOT_THEME" not in data

    def test_the_muix_row_writes_a_tsx_file(self, config: ExecutorConfig, tmp_path: Path) -> None:
        argv = build_argv(config, "r-a-light", tmp_path, "light", 60, command=command_for("javascript", "muix"))

        assert argv[-4:] == ["node", "/opt/anyplot/js-render/render.mjs", "--library=muix", "plot.tsx"]

    def test_the_forbidden_flags_assertion_holds_for_every_row(self, config: ExecutorConfig, tmp_path: Path) -> None:
        for language, library in (("python", "matplotlib"), ("javascript", "d3"), ("r", "ggplot2"), ("julia", "makie")):
            argv = build_argv(config, "r-a-light", tmp_path, "light", 60, command=command_for(language, library))
            assert "--write" not in argv and not any(part.startswith("--allow-egress") for part in argv)


class TestToolchains:
    def test_the_executor_reports_every_language_and_always_python(self, config: ExecutorConfig) -> None:
        languages = SandboxExecutor(config).languages()

        assert set(languages) == set(LANGUAGES) and languages["python"] is True
        assert all(isinstance(value, bool) for value in languages.values())

    def test_a_language_is_available_when_its_binaries_are_on_the_sandbox_path(
        self, config: ExecutorConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        present = {"node", "julia"}
        monkeypatch.setattr(
            executor_module.shutil,
            "which",
            lambda binary, path=None: f"/usr/bin/{binary}" if binary in present else None,
        )

        languages = SandboxExecutor(config).languages()

        assert languages == {"python": True, "javascript": True, "r": False, "julia": True}

    def test_the_status_carries_the_languages(self) -> None:
        status = RendererStatus(
            version="1",
            in_flight=0,
            waiting=0,
            stuck=0,
            mem_available_mb=None,
            sandbox=False,
            languages={"python": True},
        )
        assert status.languages == {"python": True}
        assert (
            RendererStatus(version="1", in_flight=0, waiting=0, stuck=0, mem_available_mb=None, sandbox=False).languages
            == {}
        )


class TestWire:
    def test_a_job_names_a_row_of_the_table(self) -> None:
        accepted = RenderRequest.model_validate({**job().model_dump(), "language": "r", "library": "ggplot2"})
        assert (accepted.language, accepted.library) == ("r", "ggplot2")
        for language, library in (("r", "matplotlib"), ("python", "chartjs"), ("python", "excel")):
            with pytest.raises(ValidationError):
                RenderRequest.model_validate({**job().model_dump(), "language": language, "library": library})
        with pytest.raises(ValidationError):
            RenderRequest.model_validate({**job().model_dump(), "language": "cobol"})
