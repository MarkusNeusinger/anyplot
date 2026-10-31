"""The renderer runs a job by its row of the command table: the argv, the environment, the limits, the toolchain check."""

import sys
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.renderer import executor as executor_module
from agents.renderer.commands import (
    EXEC_FLAG,
    JULIA_BINARY,
    JULIA_WARMUP,
    LANGUAGES,
    NODE_BINARY,
    R_BINARY,
    command_for,
)
from agents.renderer.executor import (
    DATA_JSON_ENV,
    DATA_JSON_FILE,
    SANDBOX_PATH,
    WORKDIR,
    ExecutorConfig,
    SandboxExecutor,
    build_argv,
    sandbox_env,
)
from agents.renderer.wire import (
    MAX_DATA_CSV_CHARS,
    MAX_DATA_JSON_CHARS,
    PAGE_ONLY_ENV,
    PageRequest,
    RendererStatus,
    RenderRequest,
)

from .helpers import PAGE_SNIPPET, job, page_job


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

        assert argv[argv.index(config.harness) :] == [
            config.harness,
            EXEC_FLAG,
            "--",
            R_BINARY,
            "--no-echo",
            "--no-restore",
            "--no-save",
            "--file=plot.R",
        ]
        values = envs(argv)
        assert values["ANYPLOT_THEME"] == "light" and values["PATH"] == SANDBOX_PATH
        assert "MPLBACKEND" not in values and values["XDG_CACHE_HOME"] == "/tmp"
        # The preload library goes to the child alone (`harness.main_exec`), never into the sandbox's environment.
        assert "LD_PRELOAD" not in values

    def test_a_row_without_a_code_flag_gets_the_bare_code_file(self, config: ExecutorConfig, tmp_path: Path) -> None:
        row = command_for("julia", "makie")
        argv = build_argv(config, "r-a-light", tmp_path, "light", 60, command=row)
        assert argv[argv.index(config.harness) :] == [config.harness, EXEC_FLAG, "--", *row.argv, "plot.jl"]
        assert row.argv[0] == JULIA_BINARY and "--compiled-modules=strict" in argv
        assert argv[-3:] == ["-L", JULIA_WARMUP, "plot.jl"]  # the precompile workload loads before the plot
        values = envs(argv)
        assert values["JULIA_DEPOT_PATH"] == "/tmp/depot:/opt/julia-depot" and values["LANG"] == "C.UTF-8"
        assert values["ANYPLOT_DENY_EXEC"] == "required" and "LD_PRELOAD" not in values
        assert values["PATH"] == SANDBOX_PATH and values["HOME"] == "/tmp" and "MPLBACKEND" not in values

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

    def test_an_in_process_row_brings_its_environment_and_its_own_limit(self, config: ExecutorConfig) -> None:
        """lets-plot's row: the matplotlib settings, then Arrow's system allocator and the fontconfig file, and its
        2048 MiB in place of the configured `RLIMIT_AS` (spike of 2026-10-26)."""
        limited = replace(config, rlimit_as_mb=1024, rlimit_nproc=64)
        letsplot = sandbox_env(limited, "light", 60, command=command_for("python", "letsplot"))

        assert letsplot["ANYPLOT_RLIMIT_AS_MB"] == "2048" and letsplot["ANYPLOT_RLIMIT_NPROC"] == "64"
        assert letsplot["ARROW_DEFAULT_MEMORY_POOL"] == "system"
        assert letsplot["FONTCONFIG_FILE"] == "/opt/anyplot/fonts.conf"
        assert letsplot["MPLBACKEND"] == "Agg" and letsplot["ANYPLOT_THEME"] == "light"
        assert letsplot["PATH"] == SANDBOX_PATH and letsplot["HOME"] == "/tmp"
        # pygal keeps the Python defaults: the same environment as matplotlib's, the configured limit included.
        pygal = sandbox_env(limited, "light", 60, command=command_for("python", "pygal"))
        assert pygal == sandbox_env(limited, "light", 60, command=command_for("python", "matplotlib"))
        assert pygal["ANYPLOT_RLIMIT_AS_MB"] == "1024" and "ARROW_DEFAULT_MEMORY_POOL" not in pygal

    def test_an_in_process_row_env_comes_after_the_matplotlib_keys_and_before_the_fixed_ones(
        self, config: ExecutorConfig
    ) -> None:
        """The merge order `sandbox_env` states: a row's own value replaces a matplotlib setting, and never `PATH`,
        `HOME`, the bytecode switch or a limit variable."""
        limited = replace(config, rlimit_as_mb=1024)
        row = replace(
            command_for("python", "pygal"),
            env={
                "MPLBACKEND": "svg",
                "PATH": "/opt/row/bin",
                "HOME": "/opt/row",
                "PYTHONDONTWRITEBYTECODE": "0",
                "ANYPLOT_RLIMIT_AS_MB": "0",
                "ANYPLOT_RLIMIT_CPU_S": "0",
            },
        )
        values = sandbox_env(limited, "light", 60, command=row)

        assert values["MPLBACKEND"] == "svg" and values["MPLCONFIGDIR"] == config.mplconfig
        assert values["PATH"] == SANDBOX_PATH and values["HOME"] == "/tmp"
        assert values["PYTHONDONTWRITEBYTECODE"] == "1"
        assert values["ANYPLOT_RLIMIT_AS_MB"] == "1024" and values["ANYPLOT_RLIMIT_CPU_S"] == "60"

    def test_a_row_limit_never_switches_a_configured_off_limit_on(self, config: ExecutorConfig) -> None:
        """`RENDERER_RLIMIT_AS_MB=0` turns address-space limits off for every row, lets-plot's own value included."""
        unlimited = sandbox_env(config, "dark", 60, command=command_for("python", "letsplot"))

        assert config.rlimit_as_mb == 0 and "ANYPLOT_RLIMIT_AS_MB" not in unlimited
        assert unlimited["ARROW_DEFAULT_MEMORY_POOL"] == "system"

    def test_data_runs_and_conversions_are_unchanged_by_the_python_rows(self, config: ExecutorConfig) -> None:
        limited = replace(config, rlimit_as_mb=1024, rlimit_nproc=64)

        data = sandbox_env(limited, None, 20)
        assert data["ANYPLOT_RLIMIT_AS_MB"] == "1024" and "ARROW_DEFAULT_MEMORY_POOL" not in data
        assert "FONTCONFIG_FILE" not in data and "MPLBACKEND" not in data
        convert = sandbox_env(limited, None, 20, convert=True)
        assert convert["ANYPLOT_RLIMIT_AS_MB"] == "1024" and convert["ARROW_DEFAULT_MEMORY_POOL"] == "system"
        assert "FONTCONFIG_FILE" not in convert

    def test_the_lets_plot_row_runs_the_plot_mode_command(self, config: ExecutorConfig, tmp_path: Path) -> None:
        limited = replace(config, rlimit_as_mb=1024)
        argv = build_argv(limited, "r-a-light", tmp_path, "light", 60, command=command_for("python", "letsplot"))

        assert argv[argv.index("--") :] == [
            "--",
            config.python,
            "-I",
            "-X",
            "disable-remote-debug",
            config.harness,
            "plot.py",
        ]
        values = envs(argv)
        assert values["ANYPLOT_RLIMIT_AS_MB"] == "2048" and values["ARROW_DEFAULT_MEMORY_POOL"] == "system"
        assert EXEC_FLAG not in argv

    def test_the_muix_row_writes_a_tsx_file(self, config: ExecutorConfig, tmp_path: Path) -> None:
        argv = build_argv(config, "r-a-light", tmp_path, "light", 60, command=command_for("javascript", "muix"))

        assert argv[-4:] == [NODE_BINARY, "/opt/anyplot/js-render/render.mjs", "--library=muix", "plot.tsx"]
        values = envs(argv)
        # No exec filter for Node and Chromium; the row's own environment, and the sandbox's fixed PATH and HOME.
        assert "ANYPLOT_DENY_EXEC" not in values and "LD_PRELOAD" not in values
        assert values["TZ"] == "UTC" and values["FONTCONFIG_FILE"] == "/opt/anyplot/js-fonts.conf"
        assert values["PATH"] == SANDBOX_PATH and values["HOME"] == "/tmp" and "MPLBACKEND" not in values

    def test_a_javascript_job_with_data_json_names_the_file_for_the_harness(
        self, config: ExecutorConfig, tmp_path: Path
    ) -> None:
        """JS-2: the typed table reaches the harness as `ANYPLOT_DATA_JSON`, for a JavaScript row only, and only when
        the job carries one; the row's sandbox mode is on either way."""
        row = command_for("javascript", "chartjs")
        with_data = envs(build_argv(config, "r-a-light", tmp_path, "light", 60, command=row, data_json=True))
        without = envs(build_argv(config, "r-a-light", tmp_path, "light", 60, command=row))
        assert with_data[DATA_JSON_ENV] == f"{WORKDIR}/{DATA_JSON_FILE}" == "/work/data.json"
        assert DATA_JSON_ENV not in without
        assert with_data["ANYPLOT_SANDBOX"] == without["ANYPLOT_SANDBOX"] == "1"
        assert without["ANYPLOT_NO_HTML"] == "1"
        assert without["ANYPLOT_IMPORT_ALLOWLIST"] == "/opt/anyplot/js-render/import-allowlist.json"
        for language, library in (("python", "matplotlib"), ("r", "ggplot2"), ("julia", "makie")):
            values = sandbox_env(config, "light", 60, command=command_for(language, library), data_json=True)
            assert DATA_JSON_ENV not in values and "ANYPLOT_SANDBOX" not in values, language

    async def test_the_executor_writes_data_json_next_to_the_code_file(
        self, config: ExecutorConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[tuple[list[str], bool]] = []

        async def run(self: SandboxExecutor, name: str, run_dir: Path, *args: object, **kwargs: object) -> object:
            seen.append((sorted(path.name for path in (run_dir / "work").iterdir()), bool(kwargs["data_json"])))
            return executor_module.Attempt(name=name, exit_code=0)

        monkeypatch.setattr(SandboxExecutor, "_run", run)
        executor = SandboxExecutor(config)
        payload = {**job().model_dump(), "language": "javascript", "library": "muix"}
        await executor.run_theme(
            RenderRequest.model_validate({**payload, "data_json": '{"columns":[],"data":[]}'}), "light"
        )
        await executor.run_theme(RenderRequest.model_validate(payload), "light")
        assert seen == [(["data.csv", "data.json", "plot.tsx"], True), (["data.csv", "plot.tsx"], False)]

    def test_a_page_build_switches_the_harness_to_page_only_for_the_javascript_row(
        self, config: ExecutorConfig, tmp_path: Path
    ) -> None:
        """JS-4b: `ANYPLOT_PAGE_ONLY=1` joins the JavaScript row's environment for a page build, never another row's
        and never a render's; the argv stays the row's."""
        row = command_for("javascript", "d3")
        page = build_argv(config, "r-a-page", tmp_path, "dark", 60, command=row, data_json=True, page=True)
        render = build_argv(config, "r-a-dark", tmp_path, "dark", 60, command=row, data_json=True)
        assert envs(page) == {**envs(render), PAGE_ONLY_ENV: "1"}
        assert page[page.index("--") :] == render[render.index("--") :]
        for language, library in (("python", "matplotlib"), ("r", "ggplot2"), ("julia", "makie")):
            values = sandbox_env(config, "light", 60, command=command_for(language, library), page=True)
            assert PAGE_ONLY_ENV not in values, language

    async def test_a_page_build_writes_the_code_and_the_table_and_reads_the_page(
        self, config: ExecutorConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Through the fake launcher and the real harness in exec mode, with a stand-in for Node that writes the page
        the way `render.mjs` does in page-only mode."""
        stand_in = tmp_path / "page_only.py"
        stand_in.write_text(
            "import json, os, pathlib, sys\n"
            "assert os.environ['ANYPLOT_PAGE_ONLY'] == '1' and os.environ['ANYPLOT_DATA_JSON'] == '/work/data.json'\n"
            "assert not pathlib.Path('data.csv').exists()\n"
            "columns = json.loads(pathlib.Path('data.json').read_text())['columns']\n"
            "code = pathlib.Path(sys.argv[1]).read_text()\n"
            "if 'FAIL' in code:\n"
            "    print('render: error: data DataError -: the data file is unreadable', file=sys.stderr)\n"
            "    sys.exit(1)\n"
            "theme = os.environ['ANYPLOT_THEME']\n"
            "pathlib.Path(f'plot-{theme}.html').write_text(f'<p>{theme} {columns} ü</p>' + 'x' * len(code))\n",
            encoding="utf-8",
        )
        row = replace(command_for("javascript", "chartjs"), argv=(sys.executable, str(stand_in)), env={})
        monkeypatch.setattr(executor_module, "command_for", lambda language, library: row)
        executor = SandboxExecutor(config)

        built = await executor.run_page(page_job(theme="dark"))
        failed = await executor.run_page(page_job(source="FAIL\n"))
        monkeypatch.setattr(executor_module, "MAX_PAGE_BYTES", 30)
        too_large = await executor.run_page(page_job(source="y" * 100))

        assert (built.exit_code, built.reason, built.html) == (0, None, f"<p>dark ['x'] ü</p>{'x' * len(PAGE_SNIPPET)}")
        assert failed.html is None and failed.exit_code == 1
        assert failed.stderr_tail.splitlines()[-1] == "render: error: data DataError -: the data file is unreadable"
        assert (too_large.html, too_large.reason, too_large.limit) == (None, "output_rejected", 30)
        assert too_large.measured is not None and too_large.measured > 30

    def test_a_page_that_is_no_utf8_is_refused(self, config: ExecutorConfig, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        (work / "plot-light.html").write_bytes(b"<p>\xff</p>")
        attempt = executor_module.Attempt(name="r-a-page", exit_code=0)

        SandboxExecutor(config)._collect_page(attempt, work, "light")

        assert (attempt.html, attempt.reason) == (None, "output_rejected")
        (work / "plot-light.html").unlink()
        (work / "plot-light.html").symlink_to("/etc/hostname")
        refused = executor_module.Attempt(name="r-a-page", exit_code=0)
        SandboxExecutor(config)._collect_page(refused, work, "light")
        assert (refused.html, refused.reason) == (None, "output_rejected")

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
        present = {NODE_BINARY, JULIA_BINARY}
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

    def test_data_json_is_optional_capped_and_for_javascript_only(self) -> None:
        """JS-2: the field is optional (no agent sends it before JS-4), so every request of today stays valid."""
        assert job().data_json is None and "data_json" not in job().model_fields_set
        javascript = {**job().model_dump(), "language": "javascript", "library": "d3"}
        assert RenderRequest.model_validate({**javascript, "data_json": "{}"}).data_json == "{}"
        with pytest.raises(ValidationError, match="javascript job only"):
            RenderRequest.model_validate({**job().model_dump(), "data_json": "{}"})
        with pytest.raises(ValidationError):
            RenderRequest.model_validate({**javascript, "data_json": "x" * (MAX_DATA_JSON_CHARS + 1)})
        assert MAX_DATA_JSON_CHARS == 4 * MAX_DATA_CSV_CHARS == 16 * 1024 * 1024

    def test_a_page_is_for_a_javascript_job_with_its_table(self) -> None:
        """JS-4b: `PageRequest` is the render request for one theme with `data_json` required; another language, an
        unknown field (`themes`) and a table over the cap are refused."""
        page = page_job().model_dump()
        assert PageRequest.model_validate(page).theme == "light"
        for bad in (
            {**page, "language": "python", "library": "matplotlib"},
            {**page, "language": "r", "library": "ggplot2"},
            {**page, "library": "matplotlib"},
            {**page, "themes": ["light"]},
            {**page, "data_json": "x" * (MAX_DATA_JSON_CHARS + 1)},
            {key: value for key, value in page.items() if key != "data_json"},
        ):
            with pytest.raises(ValidationError):
                PageRequest.model_validate(bad)
