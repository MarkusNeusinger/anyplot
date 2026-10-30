"""The R runtime: ggplot2 (`runtimes.R_LIBRARIES`), run as `plot.R` by R's own binary in the harness's exec mode.

The R counterpart of `runtimes/python.py`, built on 2026-10-29 as PR 3b of the R pilot
(`agentic/specs/261024-agent-all-libraries.md`, step 2c). It binds the R code profile of
PR 3a (`agents/anyplot/code/profiles/r/`: regions, normaliser, validator, readiness,
loader, error grammar) and the language-neutral modules that take the library (the edit
applier's R dialect in `code/edits.py`, the export's `Rscript plot.R` run line) to the
runtime interface, so the pipeline, the theme toggle, the local Docker backend and the
eval harness serve ggplot2 exactly as they serve the Python libraries.

**The command** is the renderer's R row (`agents/renderer/commands.py`): the probe-less
harness in exec mode in front of R's `exec/R` binary,

    python -I -X disable-remote-debug harness.py --exec -- /opt/R/4.6.1/lib/R/bin/exec/R
        --no-echo --no-restore --no-save --file=plot.R

because `Rscript` and `bin/R` would each need a second program start, which the exec
filter kills (step 2b). The environment is the renderer's `sandbox_env` for that row,
key for key, as `PythonRuntime.env` is for a Python row: the theme, R's own variables
(`R_ENV`: `R_HOME`, the share, include and doc directories, `LD_LIBRARY_PATH`,
`LANG=C.UTF-8`, the caches under `/tmp`), the sandbox's `PATH`, the deployed limits and
`ANYPLOT_DENY_EXEC=required`, which makes the harness preload the filter into R and
prove it with a preflight before the code runs. As for Python, the local backend leaves
`RLIMIT_NPROC` to the container's `--pids-limit`.

**Outputs.** R writes `plot-<theme>.png` and no probe: the host gates R1 to R3 judge the
render, and the advisory gates (G3 to G12) have nothing to read, as for altair, pygal
and lets-plot. Nor are there drawn texts to check the user's requested texts against, so
the reviewer finds them in the image instead (`review_texts`, owner decision of
2026-10-29): a run that asks for a text is `needs_attention` only when the review cannot
find it, or when no readable review answered for it.

**Data runs and conversions** stay Python's: `run_data_code` runs the Python the root
translated, whatever the plot's language, and a conversion reads a dropped file with the
harness's Python reader. This runtime hands them to a `PythonRuntime` with the same CPU
limit.

**The loader** is `readr::read_csv` typed from the column kinds (`profiles/r/loader.py`).
`col_double()` holds integers exactly up to 2^53 only, so `loader_notes` names the
columns with integer cells beyond it and their counts, which the pipeline puts first in
the shipped version's "what changed" list (owner rule of 2026-10-15: no silent loss,
every change announced with counts). Owner decision of 2026-10-29: "what changed", not
a residual note, so the note leaves the plot's status as it is (`ok` stays `ok`).
`col_datetime()` reads a timestamp with a UTC offset in UTC, so a second line names the
columns with offsets other than zero (owner decision of 2026-10-30).

**ADAPTATION.** A dataset package (gapminder, palmerpenguins) brings the package's
sample data instead of the user's, so `dataset-package` joins the rules that reject the
working form (`blocking_rules`), next to the placeholder rules: the readiness scan, which
runs on the normalised catalogue file, still calls such a file `coupled` with a
synthetic-data hint (dendrogram-basic and scatter-categorical), and the adapter removes
the package with the data block. The other findings get R targets (`ADAPTATION_TARGETS`).

**The render reserve** (`render_p95_s`, from the command row): 15 s, as for Python. The
first R render through the deployed renderer took 5.7 s of wall time on Cloud Run
(2026-10-29), about the 5.5 s that spike X measured as the Python p95, with R and
ggplot2 loaded fresh in every render; no catalogue-wide R measurement exists yet, so the
reserve keeps Python's margin over its p95 until the matrix run measures R's.
"""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from agents.renderer.commands import EXEC_DENY_ENV, EXEC_FLAG, command_for
from agents.renderer.executor import SANDBOX_PATH

from ...code.edits import AppliedPlan, apply_plan, new_literals, restore_protected
from ...code.export import R_RUN, export_code
from ...code.profiles.r.errors import error_summary
from ...code.profiles.r.loader import to_run_form
from ...code.profiles.r.normalise import normalise
from ...code.profiles.r.readiness import scan
from ...code.profiles.r.regions import PLACEHOLDER, Regions, find_regions
from ...code.profiles.r.validate import validate_adaptation, validate_security
from ...code.readiness import Readiness
from ...code.validate import Finding
from ...data.kinds import ColumnKinds
from ...schemas import AdaptPlan, CodeArtifact
from ..contract import BLOCKING_RULES, Theme
from ..harness import INTERPRETER_FLAGS
from ..png import MAX_PNG_BYTES, read_output
from .notes import counted_note, offset_note
from .python import DATA_RLIMIT_AS_MB, IMAGE_HARNESS, IMAGE_PYTHON, RENDER_RLIMIT_FSIZE_MB, PythonRuntime


LANGUAGE = "r"
DATASET_PACKAGE_RULE = "dataset-package"
ADAPTATION_TARGETS: Mapping[str, str] = MappingProxyType(
    {
        "rng": "take the values from df; set.seed() with sample(), runif() or jitter() is only for jitter or subsampling",
        "literal-data": "take the values from df instead of writing them out (no data(), no built-in dataset)",
        "palette-prefix": (
            "keep the Imprint palette one literal c() of colour strings, assigned once: the original entries in "
            "order, then only the next Imprint positions written out; pick colours from it under a new name "
            "(colors <- IMPRINT_PALETTE[seq_along(groups)]); with more than eight groups draw all but the seven "
            'largest in INK_MUTED as "Other"'
        ),
    }
)
"""The target of each soft ADAPTATION finding's defect line, in R (`runtimes.python.ADAPTATION_TARGETS` in Python)."""


class RRuntime:
    """ggplot2 plot code, run as `plot.R` by R's binary under the harness's exec mode and the exec filter."""

    language = LANGUAGE
    file_name = "plot.R"
    code_artifact: CodeArtifact = "plot.R"
    """The name the exported code downloads under (`schemas.CodeArtifact`)."""
    placeholder = PLACEHOLDER
    """The working form's data placeholder, `df <- load_user_data()`, which the loader replaces."""
    blocking_rules: frozenset[str] = BLOCKING_RULES | {DATASET_PACKAGE_RULE}
    adaptation_targets: Mapping[str, str] = ADAPTATION_TARGETS
    review_texts = True
    """R writes no probe, so the reviewer finds the requested texts in the image (module docstring, "Outputs")."""

    def __init__(
        self,
        *,
        library: str = "ggplot2",
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        render_p95_s: float = 15.0,
    ) -> None:
        command_for(self.language, library)  # a library of another language is a caller bug: ValueError
        self.library = library
        self.python = python
        self.harness = harness
        self.cpu_seconds = cpu_seconds
        self.render_p95_s = render_p95_s
        """Seconds a repair attempt's render is budgeted at against the soft deadline (`commands.py`)."""
        self._data = PythonRuntime(python=python, harness=harness, cpu_seconds=cpu_seconds)
        """Data runs and conversions: Python's, whatever the plot's language (module docstring)."""

    def command(self, theme: Theme) -> list[str]:
        """The renderer's argv for the R row (`executor.build_argv`): the harness in exec mode, then R's binary."""
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
        """The renderer's `sandbox_env` for the R row under the deployed limits, key for key (pinned by a test), but
        for `RLIMIT_NPROC`, which the local container's `--pids-limit` replaces (`PythonRuntime.env`)."""
        row = command_for(self.language, self.library)
        env = {
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
        if row.rlimit_as:
            env["ANYPLOT_RLIMIT_AS_MB"] = str(row.rlimit_as_mb or DATA_RLIMIT_AS_MB)
        if row.exec_deny:
            env[EXEC_DENY_ENV] = "required"  # the deployed `RENDERER_EXEC_DENY`
        return env

    def data_command(self) -> list[str]:
        return self._data.data_command()

    def data_env(self, timeout_s: float | None = None) -> dict[str, str]:
        return self._data.data_env(timeout_s)

    def convert_command(self) -> list[str]:
        return self._data.convert_command()

    def convert_env(self) -> dict[str, str]:
        return self._data.convert_env()

    def normalise(self, code: str, library: str) -> str:
        return normalise(code)

    def loader_block(
        self, working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str], kinds: dict[str, str]
    ) -> str:
        """`readr::read_csv` typed from the column kinds; the parser's dtypes are pandas' and stay unread."""
        return to_run_form(working, columns=columns, kinds=kinds)

    def loader_notes(self, kinds: ColumnKinds) -> list[str]:
        """One "what changed" line for the integer cells beyond ±2^53, which `col_double()` reads as the nearest
        double: the total, then each column with its count, as many as fit a change note (`MAX_CHANGE_CHARS`) and
        the rest counted as `and N more columns`; none when there are no such cells. The first column always fits:
        a column name has at most 64 characters and a count at most six. A second line for the timestamps with a
        UTC offset other than zero, which `col_datetime()` reads in UTC (`notes.offset_note`)."""
        notes: list[str] = []
        if kinds.inexact:
            total = sum(kinds.inexact.values())
            whole, them = ("integer", "it") if total == 1 else ("integers", "them")
            head = (
                f"R reads {total:,} {whole} past ±2^53 as the nearest double, so the plot can show {them} a unit or "
                "more off: "
            )
            notes.append(counted_note(head, kinds.inexact))
        if kinds.offset:
            notes.append(offset_note("R", kinds.offset))
        return notes

    def data_json(self, csv_text: str, kinds: ColumnKinds | None) -> str | None:
        """None: the run form's `readr::read_csv` reads `data.csv` itself."""
        return None

    def validate(self, code: str, library: str) -> list[str]:
        return [f"{finding.rule}: {finding.message}" for finding in validate_security(code)]

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        """The PNG, read without following links; R writes no probe."""
        return read_output(run_dir / f"plot-{theme}.png", MAX_PNG_BYTES), None

    # The code conventions of the language, for the pipeline (`agents/anyplot/code/profiles/r/`).

    def regions(self, code: str) -> Regions:
        return find_regions(code)

    def readiness(self, normalised: str, *, spec_id: str, enabled_libraries: list[str]) -> Readiness:
        return scan(normalised, spec_id=spec_id, enabled_libraries=enabled_libraries, library=self.library)

    def security(self, code: str) -> list[Finding]:
        return validate_security(code)

    def adaptation(self, code: str, *, original_palette: list[str]) -> list[Finding]:
        return validate_adaptation(code, original_palette=original_palette)

    def apply_plan(self, working: str, plan: AdaptPlan) -> AppliedPlan:
        return apply_plan(working, plan, library=self.library)

    def restore_protected(self, base: str, code: str) -> str | None:
        return restore_protected(base, code, library=self.library)

    def new_literals(self, base: str, code: str) -> list[str]:
        return new_literals(base, code, library=self.library)

    def error_summary(self, stderr_tail: str, *, run_form: str | None = None) -> str:
        """The erroring function, its cause and layer and the last calls of a failed R render, never the message.
        R's grammar names no line, so the run form, which tells where the loader shifted the lines, goes unread."""
        return error_summary(stderr_tail)

    def export(self, run_form: str, *, spec_id: str, library_version: str | None, theme: str = "light") -> str:
        return export_code(
            run_form, spec_id=spec_id, library=self.library, library_version=library_version, theme=theme, run=R_RUN
        )
