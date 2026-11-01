"""The Python runtime: matplotlib, seaborn, plotnine, altair, pygal, lets-plot, plotly and bokeh (`PYTHON_LIBRARIES`).

The command is the catalogue's CI render command (`MPLBACKEND=Agg
ANYPLOT_THEME=<theme> python plot.py`) with the isolated interpreter (no remote
debugging either, `harness.INTERPRETER_FLAGS`) and the probe harness in front. The environment is complete, never inherited: the theme, the Agg
backend, a writable matplotlib cache and `HOME` under `/tmp` (the root filesystem is
read-only), the harness's resource limits, and the library's row of the renderer's command
table (`agents/renderer/commands.py`): its own environment and its own `RLIMIT_AS` where it
has one (lets-plot), as the renderer's `sandbox_env` passes them. The library picks the code conventions
(`regions.SAVE_RULES`: the save call, altair's second `plot-<theme>.html` file and its
PIL padding) and the validator profile; plotnine draws through matplotlib and so gets a
probe, altair renders in vl-convert's V8, pygal through cairosvg and lets-plot in its native
bridge, and those three get a probe of their drawn texts alone (`harness.install_text_probes`,
since 2026-11-01), for the closing reply; the advisory gates have nothing to read there.

plotly and bokeh (PB-2a of step 4, 2026-10-31) run in the row's two steps (`FIGURE_FLAG`,
`RuntimeCommand.figure`): the harness forks the plot, which writes its figure as JSON through
the pinned save (`code/figure.py`), then draws it with the JavaScript row's harness in
Chromium, so the command carries that row's argv after `--` and the environment its `JS_ENV`
after the Python settings, as the renderer's `sandbox_env` builds them. The screenshot step
writes the text probe of what the page draws (`render.mjs`, `writeTextProbe`), nothing more;
a failure ends with the figure mode's final error line (`gates.figure_error_summary`); the
export swaps the JSON save for the library's normal save (the plan's question 10).

`normalise`, `loader_block`, `validate` and the rest (`regions`, `readiness`, `security`,
`adaptation`, `apply_plan`, `restore_protected`, `new_literals`, `error_summary`, `export`)
are the deterministic code modules in `agents/anyplot/code/` and the error grammar of
`render/gates.py`; this class only binds them to the runtime interface, for one library.
pandas reads every cell of `data.csv` exactly (`code/loader.py`), so `loader_notes` has
nothing to say; the column kinds `loader_block` takes are R's (`runtimes/r.py`).

The ADAPTATION rules that reject the code (`contract.BLOCKING_RULES`) and the targets of
the soft ones (`ADAPTATION_TARGETS`) were the pipeline's until 2026-10-29, when R brought
its own; the Python values are unchanged.
"""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from agents.renderer.commands import EXEC_DENY_ENV, FIGURE_FLAG, command_for
from agents.renderer.executor import SANDBOX_PATH
from agents.renderer.wire import run_cpu_seconds

from ...code.edits import AppliedPlan, apply_plan, new_literals, restore_protected
from ...code.export import export_code
from ...code.figure import export_form
from ...code.loader import to_run_form
from ...code.normalise import normalise
from ...code.readiness import Readiness, scan
from ...code.regions import PLACEHOLDER, Regions, find_regions, save_rule
from ...code.validate import Finding, validate_adaptation, validate_security
from ...data.kinds import ColumnKinds
from ...schemas import AdaptPlan, CodeArtifact
from ..contract import BLOCKING_RULES, Theme
from ..gates import error_summary, figure_error_summary
from ..harness import CONVERT_FLAG, DATA_FLAG, INTERPRETER_FLAGS
from ..png import MAX_PNG_BYTES, read_output, read_probe


IMAGE_PYTHON = "/app/.venv/bin/python"
IMAGE_HARNESS = "/opt/anyplot/harness.py"
MPL_SEED = "/opt/mplconfig"
HARNESS_SOURCE = Path(__file__).resolve().parents[1] / "harness.py"
IMAGE_CONVERTER = "/opt/anyplot/convert.py"
CONVERTER_SOURCE = HARNESS_SOURCE.with_name("convert.py")
CONVERT_INPUT_NAME = "input.bin"
"""A conversion's file (the renderer's `wire.CONVERT_INPUT_FILE`)."""
DATA_FILE_NAME = "snippet.py"
"""A data run's code file (the renderer's `executor.SNIPPET_FILE`); `gates.error_summary` finds its frames by it."""
DATA_RLIMIT_AS_MB = 1024
DATA_RLIMIT_NPROC = 64
"""The renderer's deployed `RENDERER_RLIMIT_AS_MB` and `RENDERER_RLIMIT_NPROC` (pinned by a test), which the local
backend's data runs apply as well, and its renders the address-space limit."""
RENDER_RLIMIT_FSIZE_MB = 50
"""The renderer's deployed `RENDERER_RLIMIT_FSIZE_MB` (pinned by a test), which the local backend's renders apply."""
ADAPTATION_TARGETS: Mapping[str, str] = MappingProxyType(
    {
        "rng": "take the values from df; a seeded np.random.default_rng(<int>) is only for jitter or subsampling",
        "literal-data": "take the values from df instead of writing them out",
        "palette-prefix": (
            "keep the Imprint palette one literal list of colour strings, assigned once: the original entries in "
            "order, then only the next Imprint positions written out; pick colours from it under a new name "
            "(colors = IMPRINT[: len(groups)]); with more than eight groups draw all but the seven largest in "
            'INK_MUTED as "Other"'
        ),
    }
)
"""The target of each soft ADAPTATION finding's defect line, matching the rule the validator checks.

The palette rule wants a literal list (`code/validate.py`, "Palette"), so its target
never says "derive it": in spike X, 9 of Claude's 14 palette-prefix lines reported a
computed palette list, the fix the old shared target ("derive it from df and the
Imprint palette") suggested."""


REVIEWED_TEXT_LIBRARIES = frozenset({"altair", "pygal", "letsplot", "plotly", "bokeh"})
"""The Python libraries that render without matplotlib: their probe reports the drawn texts alone, read from the
library's own roles for the closing reply, so the reviewer checks the user's requested texts in the image
(`PythonRuntime.review_texts`)."""


class PythonRuntime:
    """Python plot code (matplotlib, seaborn, plotnine, altair, pygal, lets-plot, plotly, bokeh), run as `plot.py`
    under the probe harness, plotly and bokeh in its figure mode."""

    language = "python"
    file_name = "plot.py"
    code_artifact: CodeArtifact = "plot.py"
    """The name the exported code downloads under (`schemas.CodeArtifact`)."""
    placeholder = PLACEHOLDER
    """The working form's data placeholder, which the loader replaces."""
    blocking_rules: frozenset[str] = BLOCKING_RULES
    adaptation_targets: Mapping[str, str] = ADAPTATION_TARGETS

    @property
    def review_texts(self) -> bool:
        """matplotlib, seaborn and plotnine draw through matplotlib's probe, which reports the drawn texts the
        requested ones are checked against, as before 2026-10-29. altair, pygal, lets-plot, plotly and bokeh report
        their drawn texts for the reply only (`REVIEWED_TEXT_LIBRARIES`), so their reviewer finds the requested texts
        in the image, as R's does."""
        return self.library in REVIEWED_TEXT_LIBRARIES

    def __init__(
        self,
        *,
        library: str = "matplotlib",
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        mplconfig: str = "/tmp/mplconfig",
        render_p95_s: float = 15.0,
    ) -> None:
        self.library = library
        self.python = python
        self.harness = harness
        self.cpu_seconds = cpu_seconds
        self.mplconfig = mplconfig
        self.render_p95_s = render_p95_s
        """Seconds a repair attempt's render is budgeted at against the soft deadline (`commands.py`)."""

    @property
    def figure(self) -> str:
        """The package of a two-step row (plotly, bokeh: `RuntimeCommand.figure`), empty for every other library."""
        return command_for(self.language, self.library).figure

    def command(self, theme: Theme) -> list[str]:
        """The renderer's argv for the library's row (`executor.build_argv`): the harness in plot mode, or for plotly
        and bokeh in figure mode, with the row's screenshot command after `--`."""
        row = command_for(self.language, self.library)
        if row.figure:
            return [
                self.python,
                *INTERPRETER_FLAGS,
                self.harness,
                FIGURE_FLAG,
                row.figure,
                self.file_name,
                "--",
                *row.argv,
            ]
        return [self.python, *INTERPRETER_FLAGS, self.harness, self.file_name]

    def env(self, theme: Theme) -> dict[str, str]:
        """A render's environment in the local Docker backend, its one caller: the renderer's `sandbox_env` for the
        library's command row under the deployed limits, key for key (pinned by a test). The matplotlib settings,
        then the row's own variables, then the fixed keys no row replaces: `PATH` is the sandbox's, the path the
        image build's delegate check reads (`agents/renderer/delegates.py`), and the limits are the deployed ones,
        the row's own `RLIMIT_AS` where it has one and none where the row switches it off (altair).

        One limit stays out: the container runs as the developer's user (`--user`), and Linux counts that user's
        processes on the whole machine against `RLIMIT_NPROC`, so 64 would stop lets-plot's threads on a busy
        desktop; the container's `--pids-limit` bounds the processes instead. Until 2026-10-26 a local render also
        kept the image's `PATH`, no `RLIMIT_AS` and the harness's default file size (the Copilot review of #12405).
        """
        row = command_for(self.language, self.library)
        env = {
            "ANYPLOT_THEME": theme,
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": self.mplconfig,
            # The renderer image's baked font cache; the harness copies it into
            # MPLCONFIGDIR and skips the copy where the directory does not exist.
            "ANYPLOT_MPL_SEED": MPL_SEED,
            **row.env,
            "PATH": SANDBOX_PATH,
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(self.cpu_seconds),
            "ANYPLOT_RLIMIT_FSIZE_MB": str(RENDER_RLIMIT_FSIZE_MB),
            EXEC_DENY_ENV: "required",  # the deployed `RENDERER_EXEC_DENY`
        }
        if row.rlimit_as:
            env["ANYPLOT_RLIMIT_AS_MB"] = str(row.rlimit_as_mb or DATA_RLIMIT_AS_MB)
        return env

    def data_command(self) -> list[str]:
        return [self.python, *INTERPRETER_FLAGS, self.harness, DATA_FLAG, DATA_FILE_NAME]

    def data_env(self, timeout_s: float | None = None) -> dict[str, str]:
        """A data run's environment: the renderer's `sandbox_env` limits for a data run, address space and processes
        included (inside Docker `RLIMIT_NPROC` counts the user's processes on the host, which one BLAS thread keeps
        far below the limit). With the run's `timeout_s`, the CPU cap is clamped to it as the renderer's executor
        clamps it (`wire.run_cpu_seconds`): a 20-second data run gets 20 CPU seconds, not the render's 60."""
        cpu_seconds = self.cpu_seconds if timeout_s is None else run_cpu_seconds(self.cpu_seconds, timeout_s)
        return {
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(cpu_seconds),
            "ANYPLOT_RLIMIT_AS_MB": str(DATA_RLIMIT_AS_MB),
            "ANYPLOT_RLIMIT_NPROC": str(DATA_RLIMIT_NPROC),
            EXEC_DENY_ENV: "required",
        }

    def convert_command(self) -> list[str]:
        """A conversion: the harness in convert mode on the file written as `input.bin`."""
        return [self.python, *INTERPRETER_FLAGS, self.harness, CONVERT_FLAG, CONVERT_INPUT_NAME]

    def convert_env(self) -> dict[str, str]:
        """A data run's environment, with Arrow's system allocator (the renderer's `sandbox_env` for a conversion)."""
        return {**self.data_env(), "ARROW_DEFAULT_MEMORY_POOL": "system"}

    def normalise(self, code: str, library: str) -> str:
        return normalise(code, library=library)

    def loader_block(
        self, working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str], kinds: dict[str, str]
    ) -> str:
        """pandas' `read_csv` from the parser's dtypes; the kinds are for typed readers of other languages."""
        return to_run_form(working, columns=columns, dtypes=dtypes, parse_dates=parse_dates)

    def loader_notes(self, kinds: ColumnKinds) -> list[str]:
        """None: `Int64`, `float64` with `float_precision="round_trip"` and the parsed datetimes keep every cell."""
        return []

    def data_json(self, csv_text: str, kinds: ColumnKinds | None) -> str | None:
        """None: the plot code reads `data.csv` itself."""
        return None

    def validate(self, code: str, library: str) -> list[str]:
        return [f"{finding.rule}: {finding.message}" for finding in validate_security(code, library=library)]

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        return read_output(run_dir / f"plot-{theme}.png", MAX_PNG_BYTES), read_probe(run_dir / f"probe-{theme}.json")

    # The code conventions of the language, for the pipeline (`agents/anyplot/code/`).

    def regions(self, code: str) -> Regions:
        return find_regions(code, library=self.library)

    def readiness(self, normalised: str, *, spec_id: str, enabled_libraries: list[str]) -> Readiness:
        return scan(normalised, spec_id=spec_id, library=self.library, enabled_libraries=enabled_libraries)

    def security(self, code: str) -> list[Finding]:
        return validate_security(code, library=self.library)

    def adaptation(self, code: str, *, original_palette: list[str]) -> list[Finding]:
        return validate_adaptation(code, original_palette=original_palette)

    def apply_plan(self, working: str, plan: AdaptPlan) -> AppliedPlan:
        return apply_plan(working, plan, library=self.library)

    def restore_protected(self, base: str, code: str) -> str | None:
        return restore_protected(base, code, library=self.library)

    def new_literals(self, base: str, code: str) -> list[str]:
        return new_literals(base, code)

    def error_summary(self, stderr_tail: str, *, run_form: str | None = None) -> str:
        """The exception class and the `plot.py` line of a failed render, never the message (`gates.error_summary`);
        for plotly and bokeh the figure mode's final error line (`gates.figure_error_summary`). The line counts the run
        form, as it always has; the run form goes unread."""
        if self.figure:
            return figure_error_summary(stderr_tail, code_file=self.file_name)
        return error_summary(stderr_tail, code_file=self.file_name)

    def export(self, run_form: str, *, spec_id: str, library_version: str | None, theme: str = "light") -> str:
        """The run form under the attribution header (`code/export.py`); for plotly and bokeh with the figure's JSON
        save swapped for the library's normal save (`code/figure.py`, the plan's question 10)."""
        rule = save_rule(self.library)
        code = export_form(run_form, rule.figure) if rule.figure is not None else run_form
        return export_code(code, spec_id=spec_id, library=self.library, library_version=library_version, theme=theme)
