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
| `r` | `plot.R` | `harness.py --exec -- Rscript plot.R` |
| `julia` | `plot.jl` | `harness.py --exec -- julia --project=/opt/julia plot.jl` |

In exec mode (`EXEC_FLAG`) the harness prints its start line, sets the resource limits
and runs the language's own command as a child, so the launcher retry, the host
watchdog and the kill path work for every language alike. A row also says which limits
differ from the Python defaults: V8, Chromium and Julia reserve address space far
beyond their resident memory, and one Chromium render runs seven processes with 77
tasks (spike of 2026-10-24), so `RLIMIT_AS` and `RLIMIT_NPROC` are off for those rows;
the `MemAvailable` watchdog, `RLIMIT_CPU`, `RLIMIT_FSIZE` and the byte budget remain.
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


@dataclass(frozen=True)
class RuntimeCommand:
    """One row of the table: how a job of this language runs in the sandbox."""

    language: Language
    code_file: str
    argv: tuple[str, ...]
    """The language's command, run by the harness in exec mode with `code_file` appended; empty for Python,
    whose plot the harness runs in process."""
    env: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    """The row's own environment, on top of `PATH`, `HOME`, `ANYPLOT_THEME` and the limit variables."""
    toolchain: tuple[str, ...] = ()
    """Binaries the image must carry on `SANDBOX_PATH` for the row to run."""
    rlimit_as: bool = True
    """Whether the configured `RLIMIT_AS` applies; off where the runtime reserves address space it never uses."""
    rlimit_nproc: bool = True
    """Whether the configured `RLIMIT_NPROC` applies; off where one render runs more tasks than its value."""
    render_p95_s: float = 15.0
    """Seconds a repair attempt's render is budgeted at (`pipeline.RENDER_P95_S` before 2026-10-24)."""

    @property
    def in_process(self) -> bool:
        """Whether the harness runs the code itself (Python) instead of a child command."""
        return not self.argv


def _row(language: Language, library: str) -> RuntimeCommand:
    code_file = CODE_FILE_OVERRIDES.get(library, CODE_FILES[language])
    if language == "python":
        return RuntimeCommand(language, code_file, ())
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
        )
    if language == "r":
        return RuntimeCommand(
            language,
            code_file,
            ("Rscript",),
            env=MappingProxyType({"XDG_CACHE_HOME": "/tmp", "R_LIBS_USER": "/tmp/R"}),
            toolchain=("Rscript",),
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
