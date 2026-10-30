"""The renderer's command table (agents/renderer/commands.py): one fixed command per language, pinned to the catalogue."""

import re
from pathlib import Path

import pytest

from agents.renderer import commands
from agents.renderer.commands import (
    EXEC_FLAG,
    LANGUAGES,
    LIBRARY_LANGUAGES,
    RuntimeCommand,
    code_file,
    command_for,
    toolchains,
)
from agents.renderer.executor import SANDBOX_PATH
from core.constants import LIBRARY_LANGUAGES as CATALOGUE_LANGUAGES
from core.constants import SUPPORTED_LANGUAGES, SUPPORTED_LIBRARIES, library_file_extension


class TestTable:
    def test_the_table_is_the_catalogue(self) -> None:
        """The renderer image has no `core`, so the table keeps its own copy of the catalogue's filing."""
        assert dict(LIBRARY_LANGUAGES) == CATALOGUE_LANGUAGES
        assert set(LIBRARY_LANGUAGES) == SUPPORTED_LIBRARIES
        assert set(LANGUAGES) == SUPPORTED_LANGUAGES

    @pytest.mark.parametrize("library", sorted(SUPPORTED_LIBRARIES))
    def test_every_library_has_a_row_with_the_catalogue_file_extension(self, library: str) -> None:
        row = command_for(LIBRARY_LANGUAGES[library], library)
        assert isinstance(row, RuntimeCommand)
        assert row.code_file == f"plot{library_file_extension(library)}"
        assert code_file(row.language, library) == row.code_file

    def test_python_runs_in_process_and_keeps_every_limit(self) -> None:
        row = command_for("python", "matplotlib")
        assert row.in_process and row.argv == () and row.toolchain == ()
        assert row.rlimit_as and row.rlimit_nproc and row.render_p95_s == 15.0
        assert command_for("python", "plotnine").rlimit_as
        altair = command_for("python", "altair")  # vl-convert's V8 reserves address space like Chromium's
        assert altair.in_process and not altair.rlimit_as and altair.rlimit_nproc
        for library in ("matplotlib", "seaborn", "plotnine", "altair", "pygal"):
            row = command_for("python", library)
            assert row.env == {} and row.rlimit_as_mb is None and row.render_p95_s == 15.0, library

    def test_pygal_keeps_the_python_defaults(self) -> None:
        """cairo reserves no address space beyond its resident set; the heaviest catalogue render peaks at 682 MB."""
        assert command_for("python", "pygal") == command_for("python", "matplotlib")

    def test_lets_plot_has_its_own_address_space_limit_and_environment(self) -> None:
        """The native bridge needs more than the configured 1 GiB, with Arrow's system allocator (spike 2026-10-26)."""
        row = command_for("python", "letsplot")
        assert row.in_process and row.argv == () and row.code_file == "plot.py" and row.toolchain == ()
        assert row.rlimit_as and row.rlimit_as_mb == 2048 and row.rlimit_nproc and row.render_p95_s == 15.0
        assert dict(row.env) == {"ARROW_DEFAULT_MEMORY_POOL": "system", "FONTCONFIG_FILE": "/opt/anyplot/fonts.conf"}
        assert commands.FONTCONFIG_FILE == "/opt/anyplot/fonts.conf"

    def test_no_row_carries_the_exec_filter_requirement_itself(self) -> None:
        """Every in-process run requires the harness's filter (`executor.sandbox_env`), so no row names it."""
        from agents.anyplot.render import harness

        assert commands.EXEC_DENY_ENV == harness.EXEC_DENY_ENV
        for library, language in LIBRARY_LANGUAGES.items():
            assert commands.EXEC_DENY_ENV not in command_for(language, library).env, library

    @pytest.mark.parametrize(
        ("rlimit_as", "rlimit_as_mb"),
        [
            pytest.param(False, 2048, id="with RLIMIT_AS off"),
            pytest.param(True, 0, id="zero"),
            pytest.param(True, -1, id="negative"),
        ],
    )
    def test_a_row_limit_needs_rlimit_as_on_and_a_positive_size(self, rlimit_as: bool, rlimit_as_mb: int) -> None:
        with pytest.raises(ValueError, match="own RLIMIT_AS"):
            RuntimeCommand("python", "plot.py", (), rlimit_as=rlimit_as, rlimit_as_mb=rlimit_as_mb)

    def test_the_image_carries_the_fontconfig_file_the_row_names(self) -> None:
        """`agents/renderer/fonts.conf` is copied to `FONTCONFIG_FILE` by the Dockerfile: one font directory, no
        cache directory, so the bridge's fontconfig never writes."""
        renderer = Path(commands.__file__).parent
        conf = (renderer / "fonts.conf").read_text(encoding="utf-8")
        assert re.findall(r"<dir>([^<]*)</dir>", conf) == ["/usr/share/fonts"] and "<cachedir" not in conf
        dockerfile = (renderer / "Dockerfile").read_text(encoding="utf-8")
        assert f"COPY agents/renderer/fonts.conf {commands.FONTCONFIG_FILE}\n" in dockerfile

    def test_the_other_languages_run_the_ci_command_through_exec_mode(self) -> None:
        js = command_for("javascript", "chartjs")
        assert js.argv == (commands.NODE_BINARY, commands.JS_HARNESS, "--library=chartjs")
        assert js.toolchain == (commands.NODE_BINARY,)
        assert not js.rlimit_as and not js.rlimit_nproc  # V8 reservations; 77 tasks per render (spike 2026-10-24)
        assert not js.exec_deny  # Node starts Chromium, Chromium its own processes
        assert command_for("javascript", "muix").code_file == "plot.tsx"
        r = command_for("r", "ggplot2")
        # R's binary directly: Rscript starts bin/R, a shell script, which starts the binary, and the exec filter
        # kills every program start after the first.
        assert r.argv == (commands.R_BINARY, "--no-echo", "--no-restore", "--no-save") and r.code_flag == "--file="
        assert r.toolchain == (commands.R_BINARY,) and r.rlimit_as and r.rlimit_nproc and r.exec_deny
        assert r.env["R_HOME"] == commands.R_HOME and r.env["LD_LIBRARY_PATH"] == f"{commands.R_HOME}/lib"
        assert r.env["LANG"] == "C.UTF-8"
        assert EXEC_FLAG == "--exec"

    def test_julia_runs_its_launcher_under_the_exec_filter_with_strict_package_images(self) -> None:
        """Step 5 after the second opinion of 2026-10-29: the launcher by its path (not on `SANDBOX_PATH`), the
        preloaded exec filter, and `--compiled-modules=strict`, which fails a cache miss in about a second where
        `existing` would load the package from source for minutes with exit 0."""
        julia = command_for("julia", "makie")
        assert commands.JULIA_BINARY == f"{commands.JULIA_HOME}/bin/julia" and commands.JULIA_BINARY.startswith("/")
        assert julia.argv == (
            commands.JULIA_BINARY,
            f"--project={commands.JULIA_PROJECT}",
            "--startup-file=no",
            "--history-file=no",
            "--compiled-modules=strict",
            "--heap-size-hint=1536M",
            "-L",
            commands.JULIA_WARMUP,
        )
        assert not any(
            flag.startswith("--compiled-modules=") and flag != "--compiled-modules=strict" for flag in julia.argv
        )
        assert julia.code_file == "plot.jl" and julia.code_flag == ""
        assert julia.render_p95_s == 25.0  # J1's sweep: wall p95 20.6 s at 2 CPUs
        assert julia.toolchain == (commands.JULIA_BINARY,) and julia.exec_deny
        assert not julia.rlimit_as and julia.rlimit_as_mb is None and julia.rlimit_nproc  # LLVM dies under 1 GiB
        assert dict(julia.env) == {
            "LANG": "C.UTF-8",
            "XDG_CACHE_HOME": "/tmp",
            "JULIA_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "JULIA_DEPOT_PATH": f"/tmp/depot:{commands.JULIA_DEPOT}",
            "JULIA_CPU_TARGET": commands.JULIA_CPU_TARGET,
            "JULIA_PKG_OFFLINE": "true",
            "JULIA_PKG_PRECOMPILE_AUTO": "0",
        }
        assert "LD_PRELOAD" not in julia.env  # the harness hands the preload to the child alone

    def test_javascript_runs_node_by_its_path_with_the_rows_environment(self) -> None:
        """JS-1 of step 3: Node by its path (`delegates.py` refuses a `node` on `SANDBOX_PATH`), the library from the
        closed set, and an environment that names the packages, the headless shell, the row's fonts and UTC."""
        assert commands.NODE_BINARY == f"{commands.NODE_HOME}/bin/node" == "/opt/node/bin/node"
        assert commands.NODE_HOME not in SANDBOX_PATH.split(":") and f"{commands.NODE_HOME}/bin" not in SANDBOX_PATH
        for library in ("chartjs", "d3", "echarts", "highcharts", "muix"):
            row = command_for("javascript", library)
            assert row.argv == (commands.NODE_BINARY, commands.JS_HARNESS, f"--library={library}"), library
            assert row.code_flag == "" and row.env is commands.JS_ENV
            assert row.render_p95_s == 15.0  # JS-1's sweep: wall p95 2.4 s at 2 CPUs; Python's and R's reserve
        assert dict(commands.JS_ENV) == {
            "PLAYWRIGHT_BROWSERS_PATH": "/opt/pw-browsers",
            "ANYPLOT_NODE_MODULES": "/opt/anyplot/node_modules",
            "FONTCONFIG_FILE": "/opt/anyplot/js-fonts.conf",
            "TZ": "UTC",
            "LANG": "C.UTF-8",
            "XDG_CACHE_HOME": "/tmp",
            "XDG_CONFIG_HOME": "/tmp",
        }
        # The sandbox's fixed keys come after a row's environment and win (`executor.sandbox_env`).
        assert not {"PATH", "HOME", "LD_PRELOAD", "NODE_OPTIONS"} & set(commands.JS_ENV)

    def test_the_image_carries_the_javascript_rows_fonts_and_harness(self) -> None:
        """The toolchain copies the row's fontconfig file and the harness where the row names them; the file adds
        the Liberation directory to the system configuration and nothing else, so no other row sees those fonts."""
        renderer = Path(commands.__file__).parent
        conf = (renderer / "toolchain" / "js-fonts.conf").read_text(encoding="utf-8")
        assert re.findall(r"<dir>([^<]*)</dir>", conf) == ["/opt/anyplot/js-fonts"]
        assert re.findall(r"<include[^>]*>([^<]*)</include>", conf) == ["/etc/fonts/fonts.conf"]
        dockerfile = (renderer / "toolchain.Dockerfile").read_text(encoding="utf-8")
        assert f"COPY agents/renderer/toolchain/js-fonts.conf {commands.JS_FONTCONFIG_FILE}\n" in dockerfile
        assert "COPY --from=node /opt/anyplot/js-fonts /opt/anyplot/js-fonts\n" in dockerfile
        assert "COPY automation/js-render/ /opt/anyplot/js-render/\n" in dockerfile
        assert commands.JS_HARNESS == "/opt/anyplot/js-render/render.mjs"
        assert f"COPY --from=node {commands.JS_NODE_MODULES} {commands.JS_NODE_MODULES}\n" in dockerfile
        assert f"COPY --from=node {commands.PLAYWRIGHT_BROWSERS} {commands.PLAYWRIGHT_BROWSERS}\n" in dockerfile
        assert f"COPY --from=node {commands.NODE_HOME} {commands.NODE_HOME}\n" in dockerfile
        # No other row's font path reaches the directory: lets-plot's file names /usr/share/fonts alone.
        assert "/opt/anyplot/js-fonts" not in (renderer / "fonts.conf").read_text(encoding="utf-8")

    def test_the_harness_reads_the_packages_from_the_rows_variable(self) -> None:
        """In a checkout the harness finds node_modules two levels up; in the image only `ANYPLOT_NODE_MODULES`
        names it, and without the variable the pipeline's behaviour is unchanged."""
        harness = (Path(commands.__file__).parents[2] / "automation" / "js-render" / "render.mjs").read_text(
            encoding="utf-8"
        )
        assert (
            'const NODE_MODULES = process.env.ANYPLOT_NODE_MODULES || path.join(REPO_ROOT, "node_modules");' in harness
        )

    def test_julia_loads_the_precompile_workload_right_before_the_plot(self) -> None:
        """J1.1: the workload's native code is used only while its package is loaded, so `-L` loads it before the
        plot, which stays the program (`julia ... -L warmup.jl plot.jl`), from the toolchain's own directory."""
        julia = command_for("julia", "makie")
        assert julia.argv[-2:] == ("-L", commands.JULIA_WARMUP) and julia.argv.count("-L") == 1
        assert commands.JULIA_WARMUP == "/opt/anyplot/toolchain/warmup.jl"
        assert julia.code_flag == "" and julia.code_file == "plot.jl"

    def test_a_pair_outside_the_table_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no runtime command"):
            command_for("python", "excel")
        with pytest.raises(ValueError, match="python library, not r"):
            command_for("r", "matplotlib")
        with pytest.raises(ValueError, match="javascript library, not python"):
            command_for("python", "chartjs")

    def test_toolchains_name_one_binary_set_per_language(self) -> None:
        needed = toolchains()
        assert set(needed) == set(LANGUAGES)
        assert needed["python"] == () and needed["r"] == (commands.R_BINARY,)
        assert needed["javascript"] == (commands.NODE_BINARY,) and needed["julia"] == (commands.JULIA_BINARY,)

    def test_rows_are_frozen(self) -> None:
        row = command_for("r", "ggplot2")
        with pytest.raises(AttributeError):
            row.argv = ("sh",)  # type: ignore[misc]
        with pytest.raises(TypeError):
            row.env["PATH"] = "/x"  # type: ignore[index]
