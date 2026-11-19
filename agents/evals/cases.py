"""Eval cases: loading, validation and selection for the matrix harness.

A case is a directory with `case.json`, `data.csv` and optionally `snapshot.json` and
`change_request.txt` (`agents/evals/fixtures/README.md`). `case.json` may name a
session `language` (a value of `language.LANGUAGE_PATTERN`), which the harness sets
through `PUT /v1/sessions/{sid}/language` before the first turn, as the chat header's
chip would; without it the session keeps its own default and detection. It may name
`before_operations`, the data steps a user takes before the plot: lists of `prepare_data`
operations, which the harness stores as the session's next data versions right after the
paste, before the bindings and the confirmation, through the server's own code and with
no model call (`matrix.store_data_steps`). The `n5000` cases of the specs that draw one
value per key aggregate their raw records this way (`make_fixtures.py`). It may name
`before_view`, one `prepare_data` call's operations that all land in the view of the plot
(`plot_view.route`: selections and at most one top N), which the harness sets after the
confirmation, so the plot draws only those rows (`matrix.store_view`), and `view_checks`,
what such a case's runs must show (`ViewChecks`, measured by `matrix.view_record`). Two
sources:

* `agents/evals/fixtures/cases/`: committed, synthetic only (`origin="fixtures"`);
* `agents/evals/.cases/`: promoted feedback cases, git-ignored because they hold users'
  data (`origin="promoted"`). `agents/evals/sync_cases.py` pulls the promoted cases from
  the private bucket and removes the retired ones; `agents/evals/import_case.py` writes
  one by hand from a saved session or a copied case directory. The harness reads the
  directory when it exists. Such a case's `case.json` may record `sent_at`, when its
  feedback was sent (the manifest's `created_at`, `YYYY-MM-DDTHH:MM:SSZ`), `lane`, the
  BFF lane that served its chat (`admin` or `public`), and `owner_chat: true` for a case
  that holds the operator's own data; a case sent before 2026-11-19, or without
  `sent_at`, replays only on Claude through Vertex AI in `eu` unless its lane is `admin`
  or it holds the operator's own data (`agents/evals/replay.py`).

`select_cases` takes the harness's `--cases` value and the routes of every model the
caller sends the selected cases to, and refuses a pinned case those routes would take
elsewhere (`replay.check`). The value is `smoke` (the cases tagged `smoke`:
one generated matplotlib or seaborn case per spec, one plotnine and one altair case since
2026-10-25, one pygal and one lets-plot case since 2026-10-26, one ggplot2 case since
2026-10-29, one makie case and one each for chartjs, d3, echarts and highcharts since
2026-10-30, one muix case and one each for plotly and bokeh since 2026-10-31, plus the
hand-written `scatter-basic-matplotlib` and `bar-grouped-seaborn`: 25), `full` (every case
except the stress cases: the 900 generated and the fifteen hand-written ones, 915 since the four
view cases of 2026-11-16, 911 since 2026-11-01, 907 since PB-2a;
787 before plotly and bokeh, 727 before MUI X, 487 before the other JavaScript libraries, 427
before makie, 367 before ggplot2, 247 before pygal and lets-plot, 127 before plotnine and
altair), `stress` (the
cases tagged `stress`, from `make_stress.py`), or comma-separated shell globs over case
ids (`*-seaborn-*`, `pie-basic-*`, `stress-compute-*`). The catalogue
snapshot comes from `snapshot.json` or, without it, from `plots/<spec>/` in this
checkout (`dev_fixture.snapshot_from_repo`).
"""

import fnmatch
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, get_args

from agents.anyplot.dev_fixture import CASES_DIR, snapshot_from_repo
from agents.anyplot.language import LANGUAGE_PATTERN, is_valid
from agents.anyplot.schemas import Binding, ShownGroup, Theme
from agents.anyplot.session_state import CatalogueSnapshot
from agents.anyplot.settings import FIXTURE_PATTERN
from agents.evals import replay
from core.constants import SUPPORTED_LIBRARIES


PROMOTED_DIR = Path(__file__).resolve().parent / ".cases"
Expected = Literal["accepted", "rejected", "unknown"]
Origin = Literal["fixtures", "promoted"]
EXPECTED: tuple[str, ...] = ("accepted", "rejected", "unknown")
SMOKE_TAG = "smoke"
STRESS_TAG = "stress"
MAX_CHANGE_REQUEST_CHARS = 600
MAX_BEFORE_VERSIONS = 5
"""Data steps a case may take before its plot: the versions the undo history keeps, as for the prep cases."""
_CASE_ID = re.compile(FIXTURE_PATTERN)


class CaseError(ValueError):
    """A case directory that cannot be run: a missing file or an invalid field."""


@dataclass(frozen=True)
class FollowUpChecks:
    """What the version the follow-up message shipped must show (`checks` in `case.json`), measured in code.

    A combined follow-up ("make the title German and use a log scale on y") once reached the
    plot with its language part only (user test of 2026-11-01): every part of such a message
    is a check of its own. `language` and `theme` are the shipped version's plot language and
    render theme; each `code_added` pattern must match the shipped code and not the first
    version's (the change the message asked for, not a line the catalogue already had); each
    `code_kept` pattern must match both (a part the message did not ask to change, such as the
    theme tokens a dark background must keep: the theme is the run's, never colours written in);
    each role in `texts_changed` must draw other texts than in the first version (a translated
    title). Every checked follow-up also needs an empty `requested_not_found`: a text the
    root asked the plot to show is there (`matrix.follow_up_checks`).
    """

    language: str | None = None
    theme: Theme | None = None
    code_added: tuple[str, ...] = ()
    code_kept: tuple[str, ...] = ()
    texts_changed: tuple[ShownGroup, ...] = ()


MAX_CODE_PATTERNS = 5


@dataclass(frozen=True)
class ViewChecks:
    """What the runs of a case under a view of the plot (`before_view`) must show (`view_checks` in `case.json`).

    Every such case checks that the version it shipped drew the view's rows: fewer than the table's, under the view's
    own words (`drawn_rows`). `named`: a drawn text that is no axis label and no tick label (the title, a subtitle,
    the legend, an annotation, any other text) holds each part of the view in the view's own words, the N of a top N
    or a value a selection keeps (`matrix.view_tokens`), for a plot that draws a figure over several rows. `clear`:
    after the plot the harness clears the view with the page's `.show_all()` (`show_all_rows`), whose run must draw
    every row, and no such drawn text may hold those words any more. `no_dq03`: no review of the case's turns raised
    a DQ-03 line, for a control whose plot draws no figure over several rows. The results go to the run's `view`
    record and the summary's `view_check_failures`; they do not decide a pass (`matrix.view_record`).
    """

    named: bool = False
    clear: bool = False
    no_dq03: bool = False


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
    checks: FollowUpChecks | None = None
    """What the follow-up's shipped version must show; only a case with a `change_request` has them."""
    before_operations: tuple[tuple[dict[str, Any], ...], ...] = ()
    """The data steps before the plot, one `prepare_data` call's operations each, stored as a version of its own
    after the paste (`matrix.store_data_steps`); `bindings` name the columns the last one leaves."""
    before_view: tuple[dict[str, Any], ...] = ()
    """The view of the plot the harness sets after the confirmation (`matrix.store_view`): one `prepare_data` call's
    operations that all land in the view; empty for a case whose plot draws every row."""
    view_checks: ViewChecks | None = None
    """What the runs under `before_view` must show; None checks the drawn rows alone (`ViewChecks`)."""
    sent_at: datetime | None = None
    """When a promoted case's feedback was sent (`sent_at` in `case.json`); None when the case does not record it,
    which pins it (`replay.is_pinned`)."""
    lane: replay.Lane | None = None
    """The BFF lane that served the case's chat (`lane` in `case.json`); None when the case does not record it. A case
    of the `admin` lane may replay anywhere (`replay.is_pinned`)."""
    owner_chat: bool = False
    """`owner_chat: true` in `case.json`: the case holds the operator's own data and may replay anywhere."""
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
    checks = _checks(raw.get("checks"), directory)
    if checks is not None and change_request is None:
        raise CaseError(f"{directory}/case.json: checks need a change_request.txt, the follow-up they measure")
    before_operations = _before_operations(raw.get("before_operations"), directory)
    before_view = _before_view(raw.get("before_view"), directory)
    view_checks = _view_checks(raw.get("view_checks"), directory)
    if view_checks is not None and not before_view:
        raise CaseError(f"{directory}/case.json: view_checks need a before_view, the view they measure")
    if view_checks is not None and (view_checks.named or view_checks.clear) and not _view_words(before_view):
        raise CaseError(
            f"{directory}/case.json: view_checks.named and clear need a part of the view a label repeats: a "
            "selection with eq or contains, or a top N"
        )
    if view_checks is not None and view_checks.clear and change_request is not None:
        # The clearing is the case's follow-up turn; a typed follow-up as well would leave open which one it clears.
        raise CaseError(f"{directory}/case.json: view_checks.clear and a change_request.txt exclude each other")
    sent_at = _sent_at(raw.get("sent_at"), directory)
    lane = raw.get("lane")
    if lane is not None and lane not in replay.LANES:
        raise CaseError(f"{directory}/case.json: lane must be one of {', '.join(replay.LANES)}")
    owner_chat = raw.get("owner_chat", False)
    if not isinstance(owner_chat, bool):
        raise CaseError(f"{directory}/case.json: owner_chat must be true or false")
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
        checks=checks,
        before_operations=before_operations,
        before_view=before_view,
        view_checks=view_checks,
        sent_at=sent_at,
        lane=lane,
        owner_chat=owner_chat,
        snapshot_file=snapshot_file if snapshot_file.is_file() else None,
    )


def _sent_at(value: Any, directory: Path) -> datetime | None:
    """`sent_at` of `case.json` as an aware UTC time; a value in another form is a broken case, not a missing one."""
    if value is None:
        return None
    try:
        return replay.parse_sent_at(value)
    except ValueError as exc:
        raise CaseError(f"{directory}/case.json: sent_at must be a UTC time as YYYY-MM-DDTHH:MM:SSZ") from exc


def _before_operations(value: Any, directory: Path) -> tuple[tuple[dict[str, Any], ...], ...]:
    """`before_operations` of `case.json`: 1 to `MAX_BEFORE_VERSIONS` lists, each a valid argument of `prepare_data`.

    Whether they apply to the case's data shows only when the harness stores them, which raises then: a fixture bug.
    """
    from pydantic import ValidationError

    from agents.anyplot.data.prepare import PrepareArgs

    if value is None:
        return ()
    where = f"{directory}/case.json: before_operations"
    if not isinstance(value, list) or not 0 < len(value) <= MAX_BEFORE_VERSIONS:
        raise CaseError(f"{where} must be a list of 1 to {MAX_BEFORE_VERSIONS} operation lists")
    steps = []
    for operations in value:
        try:
            PrepareArgs.model_validate({"operations": operations})
        except ValidationError as exc:
            raise CaseError(
                f"{where}: an operation list that prepare_data refuses ({exc.error_count()} errors)"
            ) from exc
        steps.append(tuple(operations))
    return tuple(steps)


def _before_view(value: Any, directory: Path) -> tuple[dict[str, Any], ...]:
    """`before_view` of `case.json`: one valid `prepare_data` call whose every operation lands in the view of the plot
    as the tool routes it (`plot_view.route`, `plot_view.merged`): `keep_rows` with `where`, and at most one top N, a
    `sort` and then a `keep_rows` with `n`. Nothing for the table and no `reset_view` or `apply_view`, so the plot
    draws the view's rows of the table the case pasted. Whether it fits that table shows only when the harness stores
    it (`matrix.store_view`), which raises then: a fixture bug."""
    from pydantic import ValidationError

    from agents.anyplot.data.prepare import PrepareArgs
    from agents.anyplot.plot_view import PlotView, ViewRefused, merged, route

    if value is None:
        return ()
    where = f"{directory}/case.json: before_view"
    if not isinstance(value, list) or not value:
        raise CaseError(f"{where} must be a non-empty list of operations, one prepare_data call")
    try:
        args = PrepareArgs.model_validate({"operations": value})
        routed = route(list(args.operations))
        merged(PlotView(), routed)
    except ValidationError as exc:
        raise CaseError(f"{where}: an operation list that prepare_data refuses ({exc.error_count()} errors)") from exc
    except ViewRefused as exc:
        raise CaseError(f"{where}: a view that prepare_data refuses") from exc
    if routed.table or routed.reset or not routed.view:
        raise CaseError(
            f"{where} must land in the view of the plot alone: keep_rows with where, and at most one sort followed by "
            "keep_rows with n"
        )
    return tuple(value)


def _view_words(operations: tuple[dict[str, Any], ...]) -> bool:
    """Whether a valid `before_view` has a part a label names in the view's own words (`matrix.view_tokens`): a
    view of order conditions alone (`gt`, `le`) has none, so a check of its drawn texts would read nothing."""
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation
    from agents.anyplot.plot_view import PlotView, merged, route
    from agents.evals.matrix import view_tokens

    view = merged(PlotView(), route(TypeAdapter(list[Operation]).validate_python(list(operations))))
    return bool(view_tokens(view))


def _view_checks(value: Any, directory: Path) -> ViewChecks | None:
    """`view_checks` of `case.json` as `ViewChecks`: an object of some of its fields, each true or false."""
    if value is None:
        return None
    fields = {"named", "clear", "no_dq03"}
    if (
        not isinstance(value, dict)
        or not value
        or set(value) - fields
        or not all(isinstance(flag, bool) for flag in value.values())
    ):
        raise CaseError(
            f"{directory}/case.json: view_checks must be an object with some of {', '.join(sorted(fields))}, "
            "each true or false"
        )
    return ViewChecks(**value)


def _checks(value: Any, directory: Path) -> FollowUpChecks | None:
    """`checks` of `case.json` as `FollowUpChecks`: every field optional, but at least one, and none unknown."""
    if value is None:
        return None
    where = f"{directory}/case.json: checks"
    fields = {"language", "theme", "code_added", "code_kept", "texts_changed"}
    if not isinstance(value, dict) or not value or set(value) - fields:
        raise CaseError(f"{where} must be an object with some of {', '.join(sorted(fields))}")
    language, theme = value.get("language"), value.get("theme")
    if language is not None and not (isinstance(language, str) and is_valid(language)):
        raise CaseError(f"{where}.language must match {LANGUAGE_PATTERN}")
    if theme is not None and theme not in get_args(Theme):
        raise CaseError(f"{where}.theme must be one of {', '.join(get_args(Theme))}")
    roles = value.get("texts_changed", [])
    if not isinstance(roles, list) or not all(role in get_args(ShownGroup) for role in roles):
        raise CaseError(f"{where}.texts_changed must be a list of drawn-text roles (`PlotShows.texts`)")
    checks = FollowUpChecks(
        language=language,
        theme=theme,
        code_added=_patterns(value, "code_added", where),
        code_kept=_patterns(value, "code_kept", where),
        texts_changed=tuple(roles),
    )
    if checks == FollowUpChecks():
        # Only `shipped` and `requested_found` would be left, which a follow-up that changed nothing passes.
        raise CaseError(f"{where} must check something: a language, a theme, a code pattern or a drawn-text role")
    return checks


def _patterns(value: dict[str, Any], key: str, where: str) -> tuple[str, ...]:
    """A list of at most `MAX_CODE_PATTERNS` regular expressions that compile."""
    patterns = value.get(key, [])
    if not isinstance(patterns, list) or len(patterns) > MAX_CODE_PATTERNS:
        raise CaseError(f"{where}.{key} must be a list of at most {MAX_CODE_PATTERNS} patterns")
    for pattern in patterns:
        try:
            re.compile(pattern)
        except (TypeError, re.error) as exc:
            raise CaseError(f"{where}.{key} holds a pattern that does not compile ({type(exc).__name__})") from exc
    return tuple(patterns)


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


def select_cases(cases: list[EvalCase], selector: str, *, routes: replay.Routes) -> list[EvalCase]:
    """The cases `--cases` names: `smoke`, `full` (all but the stress cases), `stress`, or comma-separated globs.

    `routes` is every model route the caller sends the selected cases' data to (`replay.routes_of` for a matrix
    run), or `replay.NO_MODEL_CALL` for a caller that calls no model. A pinned promoted case among the selected that a
    route would take elsewhere raises `replay.ReplayRefused`: every tool that selects eval cases passes this check
    before its first model call.
    """
    if selector == "full":
        picked = [case for case in cases if STRESS_TAG not in case.tags]
    elif selector == "smoke":
        picked = [case for case in cases if SMOKE_TAG in case.tags]
    elif selector == STRESS_TAG:
        picked = [case for case in cases if STRESS_TAG in case.tags]
    else:
        patterns = [pattern.strip() for pattern in selector.split(",") if pattern.strip()]
        picked = [case for case in cases if any(fnmatch.fnmatchcase(case.case_id, pattern) for pattern in patterns)]
    replay.check(picked, routes)
    return picked
