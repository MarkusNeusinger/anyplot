"""The Julia runtime: Makie (`runtimes.JULIA_LIBRARIES`), run as `plot.jl` by Julia's launcher in the harness's exec mode.

The Julia counterpart of `runtimes/r.py`, built on 2026-10-30 as J2b of step 5
(`agentic/specs/261024-agent-all-libraries.md`). It binds the Julia code profile of J2a
(`agents/anyplot/code/profiles/julia/`: regions, normaliser, validator, readiness, loader,
error grammar) and the language-neutral modules that take the library (the edit applier's
Julia dialect in `code/edits.py`, the export's `julia --project=. plot.jl` run line) to the
runtime interface, so the pipeline, the theme toggle, the local Docker backend and the
eval harness serve Makie as they serve the Python libraries and ggplot2.

**The command** is the renderer's Julia row (`agents/renderer/commands.py`): the
probe-less harness in exec mode in front of Julia's launcher by its path,

    python -I -X disable-remote-debug harness.py --exec -- /opt/julia-1.13.2/bin/julia
        --project=/opt/julia-project --startup-file=no --history-file=no
        --compiled-modules=strict --heap-size-hint=1536M -L /opt/anyplot/toolchain/warmup.jl plot.jl

with the precompiled depot loaded under `--compiled-modules=strict` and the precompile
workload loaded before the plot (J1, J1.1). The environment is the renderer's
`sandbox_env` for that row, key for key, as `RRuntime.env` is for R's: the theme, Julia's
own variables (`JULIA_ENV`: the locale, the caches, one thread, the stacked depot, the
offline switches), the sandbox's `PATH`, the deployed limits without `RLIMIT_AS` (the row
turns it off: LLVM reserves address space far beyond its resident set) and
`ANYPLOT_DENY_EXEC=required`, which makes the harness preload the exec filter into the
launcher. As for Python and R, the local backend leaves `RLIMIT_NPROC` to the container's
`--pids-limit`.

**Outputs.** Julia writes `plot-<theme>.png` and no probe: the host gates R1 to R3 judge
the render, and the reviewer finds the requested texts in the image (`review_texts`, owner
decision of 2026-10-29), as for R. A failed render's stderr tail keeps Julia's first
`ERROR:` line in front of the last characters (the row's `stderr_head`), and the error
summary names the working form's lines: the loader replaced the one placeholder line with
15 lines and more, which `error_summary` takes off again with the run form's loader span
(`profiles/julia/loader.loader_span`).

**Data runs and conversions** stay Python's: `run_data_code` runs the Python the root
translated, whatever the plot's language. This runtime hands them to a `PythonRuntime`
with the same CPU limit.

**The loader** is `CSV.read` typed from the column kinds (`profiles/julia/loader.py`).
Julia's `DateTime` holds milliseconds, so the loader cuts a timestamp's digits below the
millisecond (owner decision of 2026-10-29), and `loader_notes` names the columns with such
cells and their counts, which the pipeline puts first in the shipped version's "what
changed" list, with the status left as the render earns it (R's 2^53 precedent). Julia
reads both integer kinds as `Int64`, exactly, so it has no integer note. The loader reads a
timestamp with a UTC offset in UTC, as readr does, so a second line names the columns with
offsets other than zero (owner decision of 2026-10-30).

**ADAPTATION.** A dataset package (RDatasets, PalmerPenguins) brings the package's sample
data instead of the user's, so `dataset-package` joins the rules that reject the working
form (`blocking_rules`), as for R; the readiness scan still calls such a catalogue file
`coupled`. The other findings get Julia targets (`ADAPTATION_TARGETS`).

**The render reserve** (`render_p95_s`, from the command row): 25 s, J1's catalogue sweep
p95 of 20.6 s rounded up; the precompile workload cut an adapted render to about 5 s
locally, and the deployed sweep revises it.
"""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from agents.renderer.commands import EXEC_DENY_ENV, EXEC_FLAG, command_for
from agents.renderer.executor import SANDBOX_PATH

from ...code.edits import AppliedPlan, apply_plan, new_literals, restore_protected
from ...code.export import JULIA_RUN, export_code
from ...code.profiles.julia.errors import error_summary
from ...code.profiles.julia.loader import loader_span, to_run_form
from ...code.profiles.julia.normalise import normalise
from ...code.profiles.julia.readiness import scan
from ...code.profiles.julia.regions import PLACEHOLDER, Regions, find_regions
from ...code.profiles.julia.validate import validate_adaptation, validate_security
from ...code.readiness import Readiness
from ...code.validate import Finding
from ...data.kinds import ColumnKinds
from ...schemas import AdaptPlan, CodeArtifact
from ..contract import BLOCKING_RULES, Theme
from ..harness import INTERPRETER_FLAGS
from ..png import MAX_PNG_BYTES, read_output
from .notes import counted_note, offset_note
from .python import DATA_RLIMIT_AS_MB, IMAGE_HARNESS, IMAGE_PYTHON, RENDER_RLIMIT_FSIZE_MB, PythonRuntime


LANGUAGE = "julia"
DATASET_PACKAGE_RULE = "dataset-package"
ADAPTATION_TARGETS: Mapping[str, str] = MappingProxyType(
    {
        "rng": (
            "take the values from df; Random.seed! with rand, shuffle or randperm is only for jitter or subsampling"
        ),
        "literal-data": "take the values from df instead of writing them out (no dataset package)",
        "palette-prefix": (
            "keep the Imprint palette one literal vector of colorant entries, assigned once: the original entries in "
            "order, then only the next Imprint positions written out; pick colours from it under a new name "
            "(colors = IMPRINT_PALETTE[1:length(groups)]); with more than eight groups draw all but the seven "
            'largest in INK_MUTED as "Other"'
        ),
    }
)
"""The target of each soft ADAPTATION finding's defect line, in Julia (`runtimes.python.ADAPTATION_TARGETS` in
Python, `runtimes.r.ADAPTATION_TARGETS` in R)."""


class JuliaRuntime:
    """Makie plot code, run as `plot.jl` by Julia's launcher under the harness's exec mode and the exec filter."""

    language = LANGUAGE
    file_name = "plot.jl"
    code_artifact: CodeArtifact = "plot.jl"
    """The name the exported code downloads under (`schemas.CodeArtifact`)."""
    placeholder = PLACEHOLDER
    """The working form's data placeholder, `df = load_user_data()`, which the loader replaces."""
    blocking_rules: frozenset[str] = BLOCKING_RULES | {DATASET_PACKAGE_RULE}
    adaptation_targets: Mapping[str, str] = ADAPTATION_TARGETS
    text_probe = False
    """Julia writes no probe yet (module docstring, "Outputs")."""
    review_texts = True
    """Julia writes no probe, so the reviewer finds the requested texts in the image (module docstring, "Outputs")."""

    def __init__(
        self,
        *,
        library: str = "makie",
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        render_p95_s: float = 25.0,
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
        """The renderer's argv for the Julia row (`executor.build_argv`): the harness in exec mode, then the launcher."""
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
        """The renderer's `sandbox_env` for the Julia row under the deployed limits, key for key (pinned by a test),
        but for `RLIMIT_NPROC`, which the local container's `--pids-limit` replaces (`PythonRuntime.env`)."""
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
        """`CSV.read` typed from the column kinds; the parser's dtypes are pandas' and stay unread."""
        return to_run_form(working, columns=columns, kinds=kinds)

    def loader_notes(self, kinds: ColumnKinds) -> list[str]:
        """One "what changed" line for the timestamps whose digits below the millisecond the loader cuts: the total,
        then each column with its count, as many as fit a change note and the rest counted (`notes.counted_note`);
        none when no cell has such digits. Julia reads every integer exactly, so `kinds.inexact` stays unread. A
        second line for the timestamps with a UTC offset other than zero, which the loader reads in UTC through
        TimeZones (`notes.offset_note`)."""
        notes: list[str] = []
        if kinds.submillisecond:
            total = sum(kinds.submillisecond.values())
            noun = "timestamp" if total == 1 else "timestamps"
            head = f"Julia keeps time to the millisecond, so the plot cuts the digits below it from {total:,} {noun}: "
            notes.append(counted_note(head, kinds.submillisecond))
        if kinds.offset:
            notes.append(offset_note("Julia", kinds.offset))
        return notes

    def data_json(self, csv_text: str, kinds: ColumnKinds | None) -> str | None:
        """None: the run form's `CSV.read` reads `data.csv` itself."""
        return None

    def validate(self, code: str, library: str) -> list[str]:
        return [f"{finding.rule}: {finding.message}" for finding in validate_security(code)]

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        """The PNG, read without following links; Julia writes no probe."""
        return read_output(run_dir / f"plot-{theme}.png", MAX_PNG_BYTES), None

    # The code conventions of the language, for the pipeline (`agents/anyplot/code/profiles/julia/`).

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
        """The exception type, the plot's line and the function it called of a failed Julia render, never the message;
        with the run form, the line is the working form's (module docstring, "Outputs")."""
        return error_summary(stderr_tail, loader=loader_span(run_form) if run_form is not None else None)

    def export(self, run_form: str, *, spec_id: str, library_version: str | None, theme: str = "light") -> str:
        return export_code(
            run_form, spec_id=spec_id, library=self.library, library_version=library_version, theme=theme, run=JULIA_RUN
        )
