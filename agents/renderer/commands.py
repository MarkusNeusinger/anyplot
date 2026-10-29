"""The command table of the renderer: one fixed command per language, chosen from the job's `(language, library)`.

A render job names a language and a library (`wire.RenderRequest`). The renderer never
runs a command the request carries: it looks the pair up here, in a table it owns, and
the request's two values only select a row. The library must be one of the catalogue's
fifteen (`LIBRARY_LANGUAGES`, pinned equal to `core.constants.LIBRARY_LANGUAGES` by a
test, because the renderer image has no `core`), and the language must be the one the
catalogue files that library under.

Every row is the catalogue's own CI render command (`prompts/workflow-prompts/
impl-generate-claude.md`, Step 3; `docs/concepts/agent-network.md`, "Render"), run in the
sandbox with the probe harness in front:

| Language | Code file | Command |
|---|---|---|
| `python` | `plot.py` | `python -I -X disable-remote-debug harness.py plot.py`: the harness runs the plot in process, with the plot guard and the savefig probe |
| `javascript` | `plot.js` (`plot.tsx` for MUI X) | `harness.py --exec -- node /opt/anyplot/js-render/render.mjs --library=<library> plot.js` |
| `r` | `plot.R` | `harness.py --exec -- /opt/R/4.6.1/lib/R/bin/exec/R --no-echo --no-restore --no-save --file=plot.R` |
| `julia` | `plot.jl` | `harness.py --exec -- julia --project=/opt/julia plot.jl` |

In exec mode (`EXEC_FLAG`) the harness prints its start line, sets the resource limits
and runs the language's own command as a child, so the launcher retry, the host
watchdog and the kill path work for every language alike. R runs its binary directly
with the environment R's `bin/R` script would set (`R_ENV`), not `Rscript`, which starts
that shell script, which starts the binary: under the exec filter (`exec_deny`) every
start after the first is killed (step 2b of agentic/specs/261024-agent-all-libraries.md).
A row with `exec_deny` gets `ANYPLOT_DENY_EXEC=required` while `RENDERER_EXEC_DENY` is
`required` (`executor.sandbox_env`): a Python row's harness installs the filter itself,
an exec-mode row's harness preloads it into the child (`harness.EXEC_DENY_PRELOAD`). The
JavaScript row has it off: Node starts Chromium and Chromium starts its own processes,
while the plot code runs in the page, which has no process API. A row also says which limits
differ from the Python defaults: V8, Chromium and Julia's LLVM reserve address space far
beyond their resident memory, so `RLIMIT_AS` is off for the JavaScript and Julia rows
and for altair's Python row (vl-convert embeds V8); one Chromium render runs seven
processes with 77 tasks (spike of 2026-10-24), so `RLIMIT_NPROC` is off for the
JavaScript row alone; the `MemAvailable` watchdog, `RLIMIT_CPU`, `RLIMIT_FSIZE` and the
byte budget remain. lets-plot's Python row keeps a bound of its own instead
(`rlimit_as_mb`, 2048 MiB, with Arrow's system allocator in its environment), because
its native rasteriser needs more than the configured 1 GiB but a runaway scale must
still stop (spike of 2026-10-26). An in-process row's environment and limit reach the
sandbox like an exec-mode row's (`executor.sandbox_env`) and the local Docker backend
(`PythonRuntime.env`).
`render_p95_s` is what the agents' pipeline reserves for a repair attempt's render
when it checks its soft deadline.

A row's `toolchain` names the binaries the image must carry on `SANDBOX_PATH` for the
row to run; the renderer checks them at startup, reports them in `GET /status` and
refuses a job whose language lacks them (`503 runtime_unavailable`). The Python row
needs none beyond the interpreter the settings name.

No ADK import, no `core` import: this module is in the renderer image.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, get_args


Language = Literal["python", "javascript", "r", "julia"]
LANGUAGES: tuple[Language, ...] = get_args(Language)

EXEC_FLAG = "--exec"
"""The harness's exec-mode flag (`harness.EXEC_FLAG`): what follows `--` is the language's command."""

LIBRARY_LANGUAGES: Mapping[str, Language] = MappingProxyType(
    {
        "altair": "python",
        "bokeh": "python",
        "letsplot": "python",
        "matplotlib": "python",
        "plotly": "python",
        "plotnine": "python",
        "pygal": "python",
        "seaborn": "python",
        "chartjs": "javascript",
        "d3": "javascript",
        "echarts": "javascript",
        "highcharts": "javascript",
        "muix": "javascript",
        "ggplot2": "r",
        "makie": "julia",
    }
)
"""The catalogue's library ids and the language each is filed under (`core.constants.LIBRARY_LANGUAGES`)."""

CODE_FILES: Mapping[Language, str] = MappingProxyType(
    {"python": "plot.py", "javascript": "plot.js", "r": "plot.R", "julia": "plot.jl"}
)
"""The file a job's code is written to, per language; `CODE_FILE_OVERRIDES` names the libraries that differ."""
CODE_FILE_OVERRIDES: Mapping[str, str] = MappingProxyType({"muix": "plot.tsx"})
"""MUI X is authored as TSX (`core.constants.LIBRARY_FILE_EXTENSION_OVERRIDES`)."""

JS_HARNESS = "/opt/anyplot/js-render/render.mjs"
"""The catalogue's browser render harness (`automation/js-render/render.mjs`) inside the image."""
JULIA_PROJECT = "/opt/julia"
"""The image's Julia project (`Project.toml` and `Manifest.toml`), instantiated at build time."""
JULIA_DEPOT = "/opt/julia-depot"
"""The precompiled depot; a sandbox stacks a writable `/tmp/depot` in front of it."""
JULIA_CPU_TARGET = "generic;sandybridge,-xsaveopt,clone_all;haswell,-rdrnd,base(1)"
"""The CPU target the depot was precompiled for; the same value at run time, or Julia recompiles."""
R_HOME = "/opt/R/4.6.1/lib/R"
"""R's home in the toolchain image (Posit's build for Debian 13, agents/renderer/toolchain.Dockerfile)."""
R_BINARY = f"{R_HOME}/bin/exec/R"
"""R's own binary, which the row runs directly: `Rscript` and `bin/R` would each need another program start."""
R_ENV: Mapping[str, str] = MappingProxyType(
    {
        "R_HOME": R_HOME,
        "R_SHARE_DIR": f"{R_HOME}/share",
        "R_INCLUDE_DIR": f"{R_HOME}/include",
        "R_DOC_DIR": f"{R_HOME}/doc",
        # Posit's layout puts libR.so on no system path (`etc/ldpaths`).
        "LD_LIBRARY_PATH": f"{R_HOME}/lib",
        # The sandbox sets no locale, and R, unlike Python, does not coerce C to UTF-8: ragg would draw non-ASCII
        # labels wrong. The catalogue's runner renders under C.UTF-8 too.
        "LANG": "C.UTF-8",
        "XDG_CACHE_HOME": "/tmp",
        "R_LIBS_USER": "/tmp/R",
    }
)
"""What R's `bin/R` script would set before it starts the binary, plus the locale and the caches."""
FONTCONFIG_FILE = "/opt/anyplot/fonts.conf"
"""The image's minimal fontconfig file (`agents/renderer/fonts.conf`: one font directory, no cache directory) for
the fontconfig that lets-plot's native bridge links, which finds no configuration of its own in the image."""
EXEC_DENY_ENV = "ANYPLOT_DENY_EXEC"
"""With `required`, the harness refuses to run code in process when its kernel filter against program starts is not
in place (`harness.EXEC_DENY_ENV`, `install_exec_deny`). `executor.sandbox_env` sets it for every in-process run
while `RENDERER_EXEC_DENY` is `required` (lets-plot's row alone until 2026-10-28)."""


@dataclass(frozen=True)
class RuntimeCommand:
    """One row of the table: how a job of this language runs in the sandbox."""

    language: Language
    code_file: str
    argv: tuple[str, ...]
    """The language's command, run by the harness in exec mode with `code_flag` and `code_file` appended as one
    argument; empty for Python, whose plot the harness runs in process."""
    code_flag: str = ""
    """What precedes the code file in its argument: `--file=` for R's binary, which takes no bare file name."""
    env: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    """The row's own environment, after `ANYPLOT_THEME` and a Python row's matplotlib settings, whose values it may
    replace, and before `PATH`, `HOME` and the limit variables, which it never replaces (`executor.sandbox_env`)."""
    toolchain: tuple[str, ...] = ()
    """Binaries the image must carry on `SANDBOX_PATH` for the row to run."""
    rlimit_as: bool = True
    """Whether the configured `RLIMIT_AS` applies; off where the runtime reserves address space it never uses."""
    rlimit_as_mb: int | None = None
    """The row's own `RLIMIT_AS` in MiB, in place of the configured one, where the runtime needs more address space
    than the configured limit gives yet still a bound; None keeps the configured one. The renderer's switch still
    rules: a configured limit of 0 (off) keeps the row unlimited too."""
    rlimit_nproc: bool = True
    """Whether the configured `RLIMIT_NPROC` applies; off where one render runs more tasks than its value."""
    render_p95_s: float = 15.0
    """Seconds a repair attempt's render is budgeted at (`pipeline.RENDER_P95_S` before 2026-10-24)."""
    exec_deny: bool = True
    """Whether the run needs the exec filter (`ANYPLOT_DENY_EXEC=required` while `RENDERER_EXEC_DENY` is
    `required`): in the harness's process for an in-process row, preloaded into the child for an exec-mode row.
    Off for the JavaScript row alone, whose Node and Chromium start their own processes."""

    def __post_init__(self) -> None:
        if self.rlimit_as_mb is not None and (not self.rlimit_as or self.rlimit_as_mb <= 0):
            raise ValueError("a row's own RLIMIT_AS needs rlimit_as on and a positive size")

    @property
    def in_process(self) -> bool:
        """Whether the harness runs the code itself (Python) instead of a child command."""
        return not self.argv


def _row(language: Language, library: str) -> RuntimeCommand:
    code_file = CODE_FILE_OVERRIDES.get(library, CODE_FILES[language])
    if language == "python":
        if library == "letsplot":
            # lets-plot rasterises in its Kotlin/Native bridge (ImageMagick linked in). An allocation it cannot
            # make under RLIMIT_AS kills the process ("Out of memory trying to allocate ... Aborting."): by
            # SIGABRT (exit 134) on a developer machine and by SIGSEGV (exit 139) in the renderer image, with
            # either Arrow pool (measured on 2026-10-26). pyarrow's mimalloc pool reserves a 1 GiB arena on the
            # first pandas string column, which kills even a minimal 3200x1800 chart at 1024 and 1536 MiB, so
            # the row takes Arrow's system allocator, as conversions do. With it, 18 of the spike's 42
            # canvas-size renders still die at the configured 1 GiB; 2048 MiB held all 42 renders of the spike
            # of 2026-10-26 up to 4800x2700 and 3600x3600 (VmPeak 1697 MiB) and still stops a 6400x3600 one
            # (2580 MiB). In the renderer image with this row the canvas-size renders took a wall p95 of 7.69 s
            # (max 15.5 s); the guarded host sweep of the 284 eligible catalogue files, canvas rewrite applied,
            # 12.5 s. The bridge's ImageMagick starts its delegates from native code, which the audit hook cannot
            # see; the harness's kernel filter against program starts, which every in-process run requires
            # (`executor.sandbox_env`), refuses them.
            return RuntimeCommand(
                language,
                code_file,
                (),
                env=MappingProxyType({"ARROW_DEFAULT_MEMORY_POOL": "system", "FONTCONFIG_FILE": FONTCONFIG_FILE}),
                rlimit_as_mb=2048,
                render_p95_s=15.0,
            )
        # altair renders in vl-convert's embedded V8, which reserves address space the way the JavaScript
        # row's Chromium does: under RLIMIT_AS up to 64 GiB it aborts at start ("Check failed: Start()",
        # SIGTRAP), measured on 2026-10-25 through the harness; its resident set is about 270 MiB and the
        # MemAvailable watchdog, RLIMIT_CPU, RLIMIT_FSIZE and the byte budget remain. plotnine fits 1 GiB,
        # and so does pygal: its heaviest catalogue render (bifurcation-basic) peaks at 682 MB resident, and
        # cairo reserves no address space beyond its resident set; the 273 catalogue files that rendered under
        # the guard took a wall p95 of 3.75 s and a p99 of 13.95 s (spike of 2026-10-26).
        return RuntimeCommand(language, code_file, (), rlimit_as=library != "altair")
    if language == "javascript":
        return RuntimeCommand(
            language,
            code_file,
            ("node", JS_HARNESS, f"--library={library}"),
            env=MappingProxyType(
                {
                    "PLAYWRIGHT_BROWSERS_PATH": "/opt/pw-browsers",
                    "ANYPLOT_NODE_MODULES": "/opt/anyplot/node_modules",
                    "ANYPLOT_NO_HTML": "1",
                    "XDG_CACHE_HOME": "/tmp",
                }
            ),
            toolchain=("node",),
            rlimit_as=False,
            rlimit_nproc=False,
            render_p95_s=20.0,
            exec_deny=False,
        )
    if language == "r":
        # The spike's renders (scatter, bar, heatmap) peaked at 294 MiB and passed under the Python defaults,
        # RLIMIT_AS 1 GiB and RLIMIT_NPROC 64, as root and as an unprivileged user (2026-10-24). The repair reserve
        # is Python's 15 s: the first deployed R render took 5.7 s of wall time on Cloud Run (2026-10-29), about the
        # Python p95 of spike X (5.5 s), with R and ggplot2 loaded fresh each time; the eval matrix measures R's p95.
        return RuntimeCommand(
            language,
            code_file,
            (R_BINARY, "--no-echo", "--no-restore", "--no-save"),
            code_flag="--file=",
            env=R_ENV,
            toolchain=(R_BINARY,),
            render_p95_s=15.0,
        )
    return RuntimeCommand(
        language,
        code_file,
        ("julia", f"--project={JULIA_PROJECT}"),
        env=MappingProxyType(
            {
                "JULIA_DEPOT_PATH": f"/tmp/depot:{JULIA_DEPOT}",
                "JULIA_CPU_TARGET": JULIA_CPU_TARGET,
                "JULIA_PKG_OFFLINE": "true",
                "JULIA_PKG_PRECOMPILE_AUTO": "0",
            }
        ),
        toolchain=("julia",),
        rlimit_as=False,
        render_p95_s=45.0,
    )


def command_for(language: str, library: str) -> RuntimeCommand:
    """The row of a job; `ValueError` for a library outside the catalogue or filed under another language."""
    expected = LIBRARY_LANGUAGES.get(library)
    if expected is None:
        raise ValueError(f"no runtime command for the library {library!r}")
    if language != expected:
        raise ValueError(f"{library} is a {expected} library, not {language}")
    return _row(expected, library)


def code_file(language: str, library: str) -> str:
    """The file the code of a job is written to (`plot.py`, `plot.js`, `plot.tsx`, `plot.R`, `plot.jl`)."""
    return command_for(language, library).code_file


def toolchains() -> dict[Language, tuple[str, ...]]:
    """The binaries each language needs on `SANDBOX_PATH`, for the renderer's startup check."""
    return {language: _row(language, _first_library(language)).toolchain for language in LANGUAGES}


def _first_library(language: Language) -> str:
    return next(library for library, filed in LIBRARY_LANGUAGES.items() if filed == language)
