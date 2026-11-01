"""The JavaScript runtime: Chart.js, D3, ECharts, Highcharts and MUI X (`runtimes.JAVASCRIPT_LIBRARIES`), run as
`plot.js` (`plot.tsx` for MUI X) by the catalogue's browser harness in the harness's exec mode.

The JavaScript counterpart of `runtimes/julia.py`, built on 2026-10-30 as JS-4a of step 3
(`agentic/specs/261024-agent-all-libraries.md`). It binds the JavaScript code profile of
JS-3 (`agents/anyplot/code/profiles/javascript/`: regions, normaliser, validator,
readiness, loader, error grammar) and the language-neutral modules that take the library
(the edit applier's JavaScript dialect in `code/edits.py`, the export's run line) to the
runtime interface, so the pipeline, the theme toggle, the local Docker backend and the
eval harness serve these libraries as they serve the Python libraries, ggplot2 and Makie.
MUI X joined on 2026-10-31 (JS-4c): `plot.tsx`, the TSX grammar, a module that the
harness bundles with esbuild through its closed import plugin and mounts as a React
component; a file written for MUI X 7 is `coupled` with the `deprecated-api` note, and
the adapter rewrites its imports (the plan's question 13).

**The command** is the renderer's JavaScript row (`agents/renderer/commands.py`): the
probe-less harness in exec mode in front of Node by its path,

    python -I -X disable-remote-debug harness.py --exec -- /opt/node/bin/node
        /opt/anyplot/js-render/render.mjs --library=<library> plot.js

which renders the snippet in Playwright's Chromium headless shell. The environment is the
renderer's `sandbox_env` for that row, key for key, as `JuliaRuntime.env` is for Julia's:
the theme, the row's own variables (`JS_ENV`: the browser, the packages, the fonts, UTC,
the caches and the harness's sandbox mode), the sandbox's `PATH` and the deployed limits
without `RLIMIT_AS` and `RLIMIT_NPROC` (the row turns both off: V8 and Chromium reserve
address space far beyond their resident set, and one render runs about 77 tasks), and no
exec filter (Node starts esbuild and Chromium, Chromium its own processes; the plot code
runs in the page, which has no process API). A job's `data.json` adds
`ANYPLOT_DATA_JSON`, which the backend sets where it writes the file, as the renderer's
executor does.

**The data** reaches the page as typed JSON (`data_json`, `data/typed_json.py`): Python
types the canonical CSV by its column kinds, so the canonical data keeps one reader, and
the harness injects it as `window.ANYPLOT_DATA`, one object per row with `.columns`, the
shape `d3.csvParse` returns. The loader is then one line for one line (`const data =
window.ANYPLOT_DATA;`, `profiles/javascript/loader.py`). JavaScript numbers are doubles
and a `Date` holds milliseconds, so `loader_notes` counts the integers past ±2^53 and the
timestamps whose digits below the millisecond the typing cuts, and names the timestamps
with a UTC offset other than zero, which the typing converts to UTC, as R's and Julia's
loaders do (owner decisions of 2026-10-29 and 2026-10-30: "what changed", the status left
as the render earns it).

**Outputs.** The harness writes `plot-<theme>.png`, in sandbox mode no interactive page
(`ANYPLOT_NO_HTML`), and a probe of the texts the page draws, by role (`render.mjs`,
`writeTextProbe`, since 2026-11-01), which the closing reply quotes: the host gates R1 to R3
judge the render, and the reviewer finds the requested texts in the image (`review_texts`),
as for R and Julia, since a canvas library's texts come from its chart model, which a
plugin's own drawing is not in. A
failed render ends with the harness's final error line (`render: error: <kind> <Class>
<file>:<line>: ...`), which `error_summary` reads: the class and the snippet's line, a
line on the loader named as the data loader, a line past the code's end (the harness's
wrapper, for a thrown value that is no `Error`) left out.

**Data runs and conversions** stay Python's: `run_data_code` runs the Python the root
translated, whatever the plot's language. This runtime hands them to a `PythonRuntime`
with the same CPU limit.

**ADAPTATION.** A MUI X import that the image's MUI X lacks (`unavailable-import`) fails
the bundle step before any render, so it joins the rules that reject the working form
(`blocking_rules`). The other findings get JavaScript targets (`ADAPTATION_TARGETS`).

**The render reserve** (`render_p95_s`, from the command row): 15 s, as for Python and R;
JS-1's catalogue sweep in the toolchain image took a wall p95 of 2.4 s.
"""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from agents.renderer.commands import EXEC_FLAG, command_for
from agents.renderer.executor import SANDBOX_PATH

from ...code.edits import AppliedPlan, apply_plan, new_literals, restore_protected
from ...code.export import SCRIPT_RUN, export_code
from ...code.profiles.javascript.errors import error_summary
from ...code.profiles.javascript.loader import loader_span, to_run_form
from ...code.profiles.javascript.normalise import normalise
from ...code.profiles.javascript.readiness import scan
from ...code.profiles.javascript.regions import PLACEHOLDER, Regions, find_regions
from ...code.profiles.javascript.validate import validate_adaptation, validate_security
from ...code.readiness import Readiness
from ...code.validate import Finding
from ...data.kinds import ColumnKinds
from ...data.typed_json import typed_json
from ...schemas import AdaptPlan, CodeArtifact
from ..contract import BLOCKING_RULES, Theme
from ..harness import INTERPRETER_FLAGS
from ..png import MAX_PNG_BYTES, read_output, read_probe
from .notes import counted_note, offset_note
from .python import IMAGE_HARNESS, IMAGE_PYTHON, RENDER_RLIMIT_FSIZE_MB, PythonRuntime


LANGUAGE = "javascript"
JS_HARNESS_SOURCE = Path(__file__).resolve().parents[4] / "automation" / "js-render" / "render.mjs"
"""The checkout's browser harness, which the local Docker backend mounts read-only over the image's (`JS_HARNESS`) for
every JavaScript container, renders and page builds alike, as it mounts the checkout's `harness.py`: a local run uses the
harness under development."""
UNAVAILABLE_IMPORT_RULE = "unavailable-import"
ADAPTATION_TARGETS: Mapping[str, str] = MappingProxyType(
    {
        "rng": "take the values from data; Math.random is only for jitter or subsampling",
        "literal-data": "take the values from data instead of writing them out",
        "palette-prefix": (
            "read the colours from t.palette (all eight Imprint positions, in order) and pick them under a new name "
            "(const colors = groups.map((g, i) => t.palette[i])); with more than eight groups draw all but the seven "
            'largest in INK_MUTED as "Other"'
        ),
    }
)
"""The target of each soft ADAPTATION finding's defect line, in JavaScript (`runtimes.python.ADAPTATION_TARGETS` in
Python, `runtimes.r.ADAPTATION_TARGETS` in R, `runtimes.julia.ADAPTATION_TARGETS` in Julia)."""


class JavaScriptRuntime:
    """Chart.js, D3, ECharts, Highcharts and MUI X plot code, run by the browser harness under the harness's exec mode."""

    language = LANGUAGE
    placeholder = PLACEHOLDER
    """The working form's data placeholder, `const data = loadUserData();`, which the loader replaces."""
    blocking_rules: frozenset[str] = BLOCKING_RULES | {UNAVAILABLE_IMPORT_RULE}
    adaptation_targets: Mapping[str, str] = ADAPTATION_TARGETS
    review_texts = True
    """The probe's texts are for the closing reply, so the reviewer finds the requested texts in the image (module
    docstring, "Outputs")."""

    def __init__(
        self,
        *,
        library: str = "chartjs",
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        render_p95_s: float = 15.0,
    ) -> None:
        row = command_for(self.language, library)  # a library of another language is a caller bug: ValueError
        self.library = library
        self.file_name = row.code_file
        """`plot.js`, `plot.tsx` for MUI X (`commands.CODE_FILE_OVERRIDES`)."""
        self.code_artifact: CodeArtifact = "plot.tsx" if row.code_file == "plot.tsx" else "plot.js"
        """The name the exported code downloads under (`schemas.CodeArtifact`): the code file's."""
        self.python = python
        self.harness = harness
        self.cpu_seconds = cpu_seconds
        self.render_p95_s = render_p95_s
        """Seconds a repair attempt's render is budgeted at against the soft deadline (`commands.py`)."""
        self._data = PythonRuntime(python=python, harness=harness, cpu_seconds=cpu_seconds)
        """Data runs and conversions: Python's, whatever the plot's language (module docstring)."""

    def command(self, theme: Theme) -> list[str]:
        """The renderer's argv for the JavaScript row (`executor.build_argv`): the harness in exec mode, then Node."""
        row = command_for(self.language, self.library)
        return [
            self.python,
            *INTERPRETER_FLAGS,
            self.harness,
            EXEC_FLAG,
            "--",
            *row.argv,
            f"{row.code_flag}{row.code_file}",
        ]

    def env(self, theme: Theme) -> dict[str, str]:
        """The renderer's `sandbox_env` for the JavaScript row under the deployed limits, key for key (pinned by a
        test), for a job without `data.json`: the backend that writes the file adds `ANYPLOT_DATA_JSON` (module
        docstring). The row switches `RLIMIT_AS`, `RLIMIT_NPROC` and the exec filter off, so none of their variables
        is set."""
        row = command_for(self.language, self.library)
        return {
            "ANYPLOT_THEME": theme,
            **row.env,
            "PATH": SANDBOX_PATH,
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(self.cpu_seconds),
            "ANYPLOT_RLIMIT_FSIZE_MB": str(RENDER_RLIMIT_FSIZE_MB),
        }

    def data_command(self) -> list[str]:
        return self._data.data_command()

    def data_env(self, timeout_s: float | None = None) -> dict[str, str]:
        return self._data.data_env(timeout_s)

    def convert_command(self) -> list[str]:
        return self._data.convert_command()

    def convert_env(self) -> dict[str, str]:
        return self._data.convert_env()

    def normalise(self, code: str, library: str) -> str:
        return normalise(code, library=self.library)

    def loader_block(
        self, working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str], kinds: dict[str, str]
    ) -> str:
        """`const data = window.ANYPLOT_DATA;` in place of the placeholder; the typing happens in `data_json`, so
        the parser's dtypes stay unread. Without the column kinds (a CSV that does not fit its own typing) the page
        gets no table, so the loader refuses the run form, as R's does."""
        if columns and not kinds:
            raise ValueError("the data does not fit its own column types, so the page cannot read it")
        return to_run_form(working, library=self.library)

    def loader_notes(self, kinds: ColumnKinds) -> list[str]:
        """Up to three "what changed" lines, each the total and then each column with its count, as many as fit a
        change note and the rest counted (`notes.counted_note`): the integers past ±2^53, which a JavaScript number
        holds as the nearest double; the timestamps whose digits below the millisecond the typing cuts, since a
        `Date` holds milliseconds; and the timestamps with a UTC offset other than zero, which the typing converts
        to UTC (`notes.offset_note`). None when no cell is changed."""
        notes: list[str] = []
        if kinds.inexact:
            total = sum(kinds.inexact.values())
            whole, them = ("integer", "it") if total == 1 else ("integers", "them")
            head = (
                f"JavaScript reads {total:,} {whole} past ±2^53 as the nearest double, so the plot can show {them} "
                "a unit or more off: "
            )
            notes.append(counted_note(head, kinds.inexact))
        if kinds.submillisecond:
            total = sum(kinds.submillisecond.values())
            noun = "timestamp" if total == 1 else "timestamps"
            head = (
                f"JavaScript keeps time to the millisecond, so the plot cuts the digits below it from {total:,} "
                f"{noun}: "
            )
            notes.append(counted_note(head, kinds.submillisecond))
        if kinds.offset:
            notes.append(offset_note("JavaScript", kinds.offset))
        return notes

    def data_json(self, csv_text: str, kinds: ColumnKinds | None) -> str | None:
        """The canonical CSV as typed JSON (`data/typed_json.py`), which the harness injects as `window.ANYPLOT_DATA`;
        None without the kinds, where `loader_block` refuses the run form. Raises `ValueError` for a cell the typing
        cannot hold, which a canonical CSV never has (a timestamp that UTC moves outside the years 1 to 9999): the
        pipeline then drops the kinds, so the loader refuses the run form with a line that says why, instead of a
        page without a table whose first `data.map` the repair would blame on the plot code (second opinion of
        2026-10-30)."""
        if kinds is None:
            return None
        return typed_json(csv_text, kinds)

    def validate(self, code: str, library: str) -> list[str]:
        return [f"{finding.rule}: {finding.message}" for finding in validate_security(code, library=self.library)]

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        """The PNG and the text probe, read without following links."""
        return read_output(run_dir / f"plot-{theme}.png", MAX_PNG_BYTES), read_probe(run_dir / f"probe-{theme}.json")

    # The code conventions of the language, for the pipeline (`agents/anyplot/code/profiles/javascript/`).

    def regions(self, code: str) -> Regions:
        return find_regions(code, library=self.library)

    def readiness(self, normalised: str, *, spec_id: str, enabled_libraries: list[str]) -> Readiness:
        return scan(normalised, spec_id=spec_id, enabled_libraries=enabled_libraries, library=self.library)

    def security(self, code: str) -> list[Finding]:
        return validate_security(code, library=self.library)

    def adaptation(self, code: str, *, original_palette: list[str]) -> list[Finding]:
        return validate_adaptation(code, original_palette=original_palette, library=self.library)

    def apply_plan(self, working: str, plan: AdaptPlan) -> AppliedPlan:
        return apply_plan(working, plan, library=self.library)

    def restore_protected(self, base: str, code: str) -> str | None:
        return restore_protected(base, code, library=self.library)

    def new_literals(self, base: str, code: str) -> list[str]:
        return new_literals(base, code, library=self.library)

    def error_summary(self, stderr_tail: str, *, run_form: str | None = None) -> str:
        """The kind, the class and the snippet's line of a failed render, never the message; with the run form, a
        line on the loader reads as the data loader and a line past the code's end is left out (module docstring,
        "Outputs")."""
        if run_form is None:
            return error_summary(stderr_tail)
        return error_summary(
            stderr_tail, loader=loader_span(run_form, library=self.library), line_count=len(run_form.splitlines())
        )

    def export(self, run_form: str, *, spec_id: str, library_version: str | None, theme: str = "light") -> str:
        return export_code(
            run_form,
            spec_id=spec_id,
            library=self.library,
            library_version=library_version,
            theme=theme,
            run=SCRIPT_RUN,
        )
