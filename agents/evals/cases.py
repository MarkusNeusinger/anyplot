"""Eval cases: loading, validation and selection for the matrix harness.

A case is a directory with `case.json`, `data.csv` and optionally `snapshot.json` and
`change_request.txt` (`agents/evals/fixtures/README.md`). `case.json` may name a
session `language` (a value of `language.LANGUAGE_PATTERN`), which the harness sets
through `PUT /v1/sessions/{sid}/language` before the first turn, as the chat header's
chip would; without it the session keeps its own default and detection. Two sources:

* `agents/evals/fixtures/cases/`: committed, synthetic only (`origin="fixtures"`);
* `agents/evals/.cases/`: promoted feedback cases, git-ignored because they hold users'
  data (`origin="promoted"`). `agents/evals/sync_cases.py` pulls the promoted cases from
  the private bucket and removes the retired ones; `agents/evals/import_case.py` writes
  one by hand from a saved session or a copied case directory. The harness reads the
  directory when it exists.

`select_cases` takes the harness's `--cases` value: `smoke` (the cases tagged `smoke`:
one generated case per spec plus the hand-written `scatter-basic-matplotlib` and
`bar-grouped-seaborn`), `full` (every case except the stress cases: the 120 generated
and the seven hand-written ones, 127 since 2026-10-15), `stress` (the
cases tagged `stress`, from `make_stress.py`), or comma-separated shell globs over case
ids (`*-seaborn-*`, `pie-basic-*`, `stress-compute-*`). The catalogue
snapshot comes from `snapshot.json` or, without it, from `plots/<spec>/` in this
checkout (`dev_fixture.snapshot_from_repo`).
"""

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from agents.anyplot.dev_fixture import CASES_DIR, snapshot_from_repo
from agents.anyplot.language import LANGUAGE_PATTERN, is_valid
from agents.anyplot.schemas import Binding
from agents.anyplot.session_state import CatalogueSnapshot
from agents.anyplot.settings import FIXTURE_PATTERN
from core.constants import SUPPORTED_LIBRARIES


PROMOTED_DIR = Path(__file__).resolve().parent / ".cases"
Expected = Literal["accepted", "rejected", "unknown"]
Origin = Literal["fixtures", "promoted"]
EXPECTED: tuple[str, ...] = ("accepted", "rejected", "unknown")
SMOKE_TAG = "smoke"
STRESS_TAG = "stress"
MAX_CHANGE_REQUEST_CHARS = 600
_CASE_ID = re.compile(FIXTURE_PATTERN)


class CaseError(ValueError):
    """A case directory that cannot be run: a missing file or an invalid field."""


@dataclass(frozen=True)
class EvalCase:
    """One runnable case."""

    case_id: str
    spec_id: str
    library: str
    locale: str
    bindings: list[Binding] | None
    expected: Expected
    tags: tuple[str, ...]
    perturbation: str | None
    source: str
    data_text: str
    origin: Origin
    directory: Path
    change_request: str | None = None
    language: str | None = None
    """The session language the harness chooses before the first turn (source `chosen`), or `None`."""
    snapshot_file: Path | None = field(default=None, repr=False)

    def snapshot(self) -> CatalogueSnapshot:
        """The catalogue snapshot the session opens with: `snapshot.json`, else the files under `plots/`."""
        if self.snapshot_file is not None:
            return CatalogueSnapshot.model_validate_json(self.snapshot_file.read_text(encoding="utf-8"))
        return snapshot_from_repo(self.spec_id, self.library)


def load_case(directory: Path, origin: Origin = "fixtures") -> EvalCase:
    """Read and validate one case directory."""
    case_id = directory.name
    if not _CASE_ID.fullmatch(case_id):
        raise CaseError(f"{directory}: not a case id ({FIXTURE_PATTERN})")
    try:
        raw: Any = json.loads((directory / "case.json").read_text(encoding="utf-8"))
        data_text = (directory / "data.csv").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise CaseError(f"{directory}: needs a readable case.json and data.csv ({type(exc).__name__})") from exc
    if not isinstance(raw, dict):
        raise CaseError(f"{directory}/case.json: not an object")
    spec_id, library = raw.get("spec_id"), raw.get("library")
    if not isinstance(spec_id, str) or not re.fullmatch(r"[a-z0-9-]{1,100}", spec_id):
        raise CaseError(f"{directory}/case.json: spec_id is missing or invalid")
    if library not in SUPPORTED_LIBRARIES:
        raise CaseError(f"{directory}/case.json: library {library!r} is not a catalogue library")
    expected = raw.get("expected", "unknown")
    if expected not in EXPECTED:
        raise CaseError(f"{directory}/case.json: expected must be one of {', '.join(EXPECTED)}")
    tags = raw.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise CaseError(f"{directory}/case.json: tags must be a list of strings")
    bindings = _bindings(raw.get("bindings"), directory)
    change_file = directory / "change_request.txt"
    change_request = change_file.read_text(encoding="utf-8").strip() if change_file.is_file() else None
    if change_request is not None and not 0 < len(change_request) <= MAX_CHANGE_REQUEST_CHARS:
        raise CaseError(f"{directory}/change_request.txt: 1 to {MAX_CHANGE_REQUEST_CHARS} characters")
    language = raw.get("language")
    if language is not None and not (isinstance(language, str) and is_valid(language)):
        raise CaseError(f"{directory}/case.json: language must match {LANGUAGE_PATTERN}")
    snapshot_file = directory / "snapshot.json"
    perturbation = raw.get("perturbation")
    return EvalCase(
        case_id=case_id,
        spec_id=spec_id,
        library=str(library),
        locale=str(raw.get("locale", "en")),
        bindings=bindings,
        expected=expected,
        tags=tuple(tags),
        perturbation=perturbation if isinstance(perturbation, str) else None,
        source=str(raw.get("source", "")),
        data_text=data_text,
        origin=origin,
        directory=directory,
        change_request=change_request,
        language=language,
        snapshot_file=snapshot_file if snapshot_file.is_file() else None,
    )


def _bindings(value: Any, directory: Path) -> list[Binding] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise CaseError(f"{directory}/case.json: bindings must be a list of {{role, column}}")
    try:
        return [Binding.model_validate(item) for item in value]
    except ValueError as exc:
        raise CaseError(f"{directory}/case.json: invalid binding ({type(exc).__name__})") from exc


def load_cases(fixtures_dir: Path = CASES_DIR, promoted_dir: Path = PROMOTED_DIR) -> list[EvalCase]:
    """Every case of both sources, sorted by case id; a case id in both is an error."""
    cases: dict[str, EvalCase] = {}
    sources: tuple[tuple[Path, Origin], ...] = ((fixtures_dir, "fixtures"), (promoted_dir, "promoted"))
    for directory, origin in sources:
        if not directory.is_dir():
            continue
        for case_dir in sorted(path for path in directory.iterdir() if path.is_dir()):
            case = load_case(case_dir, origin)
            if case.case_id in cases:
                raise CaseError(f"case id {case.case_id} exists in both {fixtures_dir} and {promoted_dir}")
            cases[case.case_id] = case
    return [cases[case_id] for case_id in sorted(cases)]


def select_cases(cases: list[EvalCase], selector: str) -> list[EvalCase]:
    """The cases `--cases` names: `smoke`, `full` (all but the stress cases), `stress`, or comma-separated globs."""
    if selector == "full":
        return [case for case in cases if STRESS_TAG not in case.tags]
    if selector == "smoke":
        return [case for case in cases if SMOKE_TAG in case.tags]
    if selector == STRESS_TAG:
        return [case for case in cases if STRESS_TAG in case.tags]
    patterns = [pattern.strip() for pattern in selector.split(",") if pattern.strip()]
    return [case for case in cases if any(fnmatch.fnmatchcase(case.case_id, pattern) for pattern in patterns)]
