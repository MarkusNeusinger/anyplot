"""The static stage: every model-free step of the `/v1` flow, measured per case and checked against its expectations.

Run it from the repository root; it calls no model and spends no tokens:

    uv run --extra agents python -m agents.evals.matrix --cases stress --static
    uv run --extra agents python -m agents.evals.matrix --cases stress --static --renderer remote --gcloud-token

For each selected case (any case, though only the stress cases of `make_stress.py`
carry expectations) it does what the service does before and around the models:

1. **dataset**: the dataset route's size check and `parse_dataset`, timed, as the route's
   answer (`ok`, `413 too_long`, `422 unparseable`) and the parse error code;
2. **eligibility**: `opening.assess` on the case's snapshot (normalise, readiness scan);
3. **bindings**: the case's bindings, or the defaults the route proposes, through
   `check_bindings` (`complete`, `incomplete`, `invalid` as `PUT /bindings` answers);
4. **loader**: the run form's `pd.read_csv` with the loader's own dtype and date
   arguments on the canonical `data.csv`, timed; a date column that pandas leaves
   unparsed is `dates_unparsed`;
5. **prompts**: the profile as the adapter, the root and the reviewer get it, the
   dataset judge's input, and the adapter request (`pipeline.render_adapt_request`)
   in characters; with a case's `marker`, which of them carry the injected text and
   whether any of it stands outside a fence;
6. **stand-in**: with a `standin_plan.json`, the plan through `apply_plan`, the
   SECURITY and ADAPTATION validators and the literal budget, then one light render
   through the configured backend and the host gates, with the render time and the
   harness's peak memory where the backend reports it (`remote`).

A record's `status` says where the flow ended (`refused`, `not_eligible`,
`bindings_invalid`, `loader_failed`, `ready`, `rendered`, `render_failed`,
`standin_rejected`), `stage` the last step it reached, and `held` whether every
expectation in the case's `static` (and, on a real renderer, `render`) field matched;
`mismatches` names the ones that did not. `model` is `pending` for a case whose bound
needs a model run (`needs_model`). The report goes to `<out>/<date>-static.json` and
its Markdown table; the exit code is 1 when an expectation did not hold.
"""

import io
import json
import re
import secrets
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from agents.anyplot.briefs import adapter_profile, profile_json, profile_summary, spec_brief
from agents.anyplot.code.edits import MAX_NEW_LITERAL_CHARS, apply_plan, new_literal_chars
from agents.anyplot.code.loader import loader_arguments
from agents.anyplot.code.regions import find_regions
from agents.anyplot.code.validate import validate_adaptation, validate_security
from agents.anyplot.data.bindings import check_bindings, default_bindings
from agents.anyplot.data.parse import MAX_INPUT_BYTES, ParsedDataset, ParseError, parse_dataset
from agents.anyplot.opening import assess, dataset_judge_input
from agents.anyplot.pipeline import BLOCKING_RULES, render_adapt_request, render_review_request
from agents.anyplot.policy import FENCE_TAGS
from agents.anyplot.render.contract import RenderBackend, RenderJob
from agents.anyplot.render.gates import data_rows, evaluate
from agents.anyplot.render.runtimes.python import PythonRuntime
from agents.anyplot.schemas import MAX_NOTES, AdaptPlan, AdaptRequest, Binding, ReviewRequest
from agents.anyplot.session_state import SessionView
from agents.anyplot.settings import AgentSettings
from agents.evals.cases import CaseError, EvalCase
from agents.renderer.wire import MAX_DATA_CSV_CHARS


STATIC_SCHEMA = 1
STANDIN_FILE = "standin.txt"
REAL_RENDERERS = frozenset({"remote", "local"})
"""Backends whose renders run the code, so a case's `render` expectations are checked."""
STATUS_ORDER = (
    "refused",
    "not_eligible",
    "bindings_invalid",
    "loader_failed",
    "ready",
    "standin_rejected",
    "render_failed",
    "rendered",
    "error",
)
_FENCED = re.compile(r"<(" + "|".join(FENCE_TAGS) + r")>\n.*?\n</\1>", re.DOTALL)


@dataclass(frozen=True)
class StressSpec:
    """The stress fields of a case's `case.json` and its stand-in plan; all empty for an ordinary case."""

    bound_expected: str | None = None
    needs_model: bool = False
    static: dict[str, Any] = field(default_factory=dict)
    render: dict[str, Any] = field(default_factory=dict)
    marker: str | None = None
    standin: str | None = None
    """The middle of a stand-in working form, from `standin.txt` (see `compose_standin`)."""


def stress_spec(case: EvalCase) -> StressSpec:
    """Read the stress fields of `case`; CaseError for a field of the wrong type."""
    where = case.directory / "case.json"
    try:
        raw = json.loads(where.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CaseError(f"{where}: unreadable ({type(exc).__name__})") from exc
    bound, needs_model = raw.get("bound_expected"), raw.get("needs_model", False)
    static, render, marker = raw.get("static", {}), raw.get("render", {}), raw.get("marker")
    if bound is not None and not isinstance(bound, str):
        raise CaseError(f"{where}: bound_expected must be a string")
    if not isinstance(needs_model, bool):
        raise CaseError(f"{where}: needs_model must be true or false")
    if not isinstance(static, dict) or not isinstance(render, dict):
        raise CaseError(f"{where}: static and render must be objects")
    if marker is not None and (not isinstance(marker, str) or not marker):
        raise CaseError(f"{where}: marker must be a non-empty string")
    standin_file = case.directory / STANDIN_FILE
    standin = standin_file.read_text(encoding="utf-8") if standin_file.is_file() else None
    return StressSpec(bound, needs_model, static, render, marker, standin)


def compose_standin(base: str, body: str) -> str:
    """A stand-in's working form: `base` up to its protected theme block, then `body`, then `base`'s final savefig.

    The stand-in keeps the catalogue file's imports and its protected regions verbatim,
    so `apply_plan`'s drift check passes whatever a regeneration changed in the rest of
    the file. ValueError for a base without a THEME assignment or a final savefig.
    """
    regions = find_regions(base)
    savefig = regions.savefig.statement if regions.savefig is not None else None
    if regions.theme is None or savefig is None:
        raise ValueError("the catalogue file has no THEME assignment or final savefig to keep")
    head_end = max([regions.theme.span.end, *(token.span.end for token in regions.theme_tokens)])
    return f"{base[:head_end].rstrip()}\n\n{body.strip()}\n\n{base[savefig.start : savefig.end].strip()}\n"


# --- Measurements ------------------------------------------------------------------------------


def dataset_outcome(text: str) -> tuple[str, ParsedDataset | None, str | None]:
    """The dataset route's answer to `text` before its judge: `ok`, `413 too_long` or `422 unparseable`, and the parse."""
    if len(text.encode("utf-8", errors="surrogatepass")) > MAX_INPUT_BYTES:
        return "413 too_long", None, "too_long"
    try:
        parsed = parse_dataset(text)
    except ParseError as exc:
        return ("413 too_long" if exc.code == "too_long" else "422 unparseable"), None, exc.code
    return "ok", parsed, None


def loader_outcome(parsed: ParsedDataset) -> tuple[str, float]:
    """The run form's `pd.read_csv` on the canonical data: `ok`, `dates_unparsed` or the exception class; its time."""
    columns = [column.name for column in parsed.profile.columns]
    dtypes, dates = loader_arguments(columns, dict(parsed.column_dtypes), list(parsed.parse_dates))
    started = time.perf_counter()
    try:
        frame = pd.read_csv(io.StringIO(parsed.csv), dtype=dtypes, parse_dates=dates)
    except Exception as exc:  # the class is the finding; the message could quote the data
        return type(exc).__name__, (time.perf_counter() - started) * 1000
    elapsed = (time.perf_counter() - started) * 1000
    if any(not pd.api.types.is_datetime64_any_dtype(frame[name]) for name in dates):
        return "dates_unparsed", elapsed
    return "ok", elapsed


def outside_fences(text: str, marker: str) -> bool:
    """Whether any occurrence of `marker` in `text` stands outside every fenced block."""
    spans = [match.span() for match in _FENCED.finditer(text)]
    start = text.find(marker)
    while start != -1:
        if not any(low <= start and start + len(marker) <= high for low, high in spans):
            return True
        start = text.find(marker, start + 1)
    return False


def lookup(record: dict[str, Any], path: str) -> Any:
    """A dotted path into the measured fields (`standin.gates`), or None when a step is missing."""
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def mismatches(measured: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Each expectation that did not hold; a list expects each of its items in the measured list."""
    found = []
    for path, wanted in sorted(expected.items()):
        actual = lookup(measured, path)
        if isinstance(wanted, list):
            missing = [item for item in wanted if not isinstance(actual, list) or item not in actual]
            if missing:
                found.append(f"{path}: expected to contain {missing}, measured {actual!r}")
        elif actual != wanted:
            found.append(f"{path}: expected {wanted!r}, measured {actual!r}")
    return found


@dataclass
class StaticContext:
    """What every static record needs: the settings, the backend for stand-in renders and its name."""

    settings: AgentSettings
    backend: RenderBackend
    renderer: str


def base_static_record(case: EvalCase, spec: StressSpec) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "spec_id": case.spec_id,
        "library": case.library,
        "tags": list(case.tags),
        "expected": case.expected,
        "bound_expected": spec.bound_expected,
        "needs_model": spec.needs_model,
        "model": "pending" if spec.needs_model else "not_needed",
        "status": "error",
        "stage": None,
        "held": None,
        "mismatches": [],
        "render_checked": False,
        "error": None,
        "static": {},
    }


async def static_record(case: EvalCase, context: StaticContext) -> dict[str, Any]:
    """One case through every model-free step; never raises for a broken case."""
    try:
        spec = stress_spec(case)
    except CaseError as exc:
        record = base_static_record(case, StressSpec())
        record["error"] = str(exc)
        return record
    record = base_static_record(case, spec)
    try:
        await _steps(record, case, spec, context)
    except Exception as exc:  # one broken case must not end the run; the type is enough to find it
        record["status"], record["error"] = "error", type(exc).__name__
    measured = record["static"]
    found = mismatches(measured, spec.static)
    if spec.render and context.renderer in REAL_RENDERERS and "standin" in measured:
        record["render_checked"] = True
        found += mismatches(measured.get("standin") or {}, spec.render)
    record["mismatches"] = found
    if spec.static or record["render_checked"]:
        record["held"] = not found and record["status"] != "error"
    return record


async def _steps(record: dict[str, Any], case: EvalCase, spec: StressSpec, context: StaticContext) -> None:
    measured = record["static"]
    measured["bytes"] = len(case.data_text.encode("utf-8", errors="surrogatepass"))
    started = time.perf_counter()
    answer, parsed, parse_error = dataset_outcome(case.data_text)
    measured["parse_ms"] = round((time.perf_counter() - started) * 1000, 1)
    measured["dataset"], measured["parse_error"] = answer, parse_error
    record["stage"] = "dataset"
    if parsed is None:
        record["status"] = "refused"
        return
    profile = parsed.profile
    measured["rows"], measured["columns"], measured["warnings"] = (
        profile.rows,
        len(profile.columns),
        len(parsed.warnings),
    )
    measured["csv_bytes"] = len(parsed.csv.encode("utf-8"))
    measured["csv_fits_wire"] = len(parsed.csv) <= MAX_DATA_CSV_CHARS

    snapshot = case.snapshot()
    eligibility, normalised = assess(snapshot, case.library, context.settings)
    measured["eligibility"] = eligibility.status
    record["stage"] = "eligibility"
    if not eligibility.eligible:
        record["status"] = "not_eligible"
        return

    roles = snapshot.roles()
    bindings = list(case.bindings) if case.bindings is not None else default_bindings(roles, profile)
    check = check_bindings(bindings, roles, profile)
    measured["bindings"] = "complete" if check.complete else ("invalid" if check.errors else "incomplete")
    measured["binding_errors"] = len(check.errors)
    record["stage"] = "bindings"

    loader, loader_ms = loader_outcome(parsed)
    measured["loader"], measured["loader_ms"] = loader, round(loader_ms, 1)

    view = SessionView(
        spec_id=case.spec_id,
        library=case.library,
        locale=case.locale,
        snapshot=snapshot,
        normalised=normalised,
        hints=list(eligibility.hints),
        dataset_id=None,
        bindings=bindings,
    )
    _measure_prompts(measured, parsed, view, bindings, case.change_request or "", spec.marker)
    if not check.complete:
        record["status"] = "bindings_invalid"
        return
    record["stage"] = "loader"
    if loader != "ok":
        record["status"] = "loader_failed"
        return
    record["stage"] = "prompt"
    record["status"] = "ready"
    if spec.standin is not None:
        await _standin(record, case, spec.standin, parsed, normalised, context)


def _measure_prompts(
    measured: dict[str, Any],
    parsed: ParsedDataset,
    view: SessionView,
    bindings: list[Binding],
    change_request: str,
    marker: str | None,
) -> None:
    """The sizes of what each model would read, and where a marker lands."""
    profile = parsed.profile
    columns = [column.name for column in profile.columns]
    adapter_text, trimmed = adapter_profile(profile)
    request = AdaptRequest(
        code=view.normalised,
        profile=profile,
        bindings=bindings,
        loader_columns=columns,
        hints=view.hints[:MAX_NOTES],
        change_request=change_request,
    )
    adapt_text = render_adapt_request(request, view)
    judge_text = dataset_judge_input(parsed)
    review_text = render_review_request(
        ReviewRequest(
            render_id="static",
            code=view.normalised,
            bindings=bindings,
            profile_summary=profile_summary(profile),
            spec_brief=spec_brief(view),
            change_request=change_request,
        )
    )
    measured["profile_chars"] = len(profile_json(profile))
    measured["adapter_profile_chars"] = len(adapter_text)
    measured["adapter_profile_trimmed"] = trimmed
    measured["judge_chars"] = len(judge_text)
    measured["adapter_prompt_chars"] = len(adapt_text)
    measured["catalogue_code_chars"] = len(view.normalised)
    measured["reviewer_text_chars"] = len(review_text)
    if marker is None:
        return
    measured["marker_in"] = {
        "judge": marker in judge_text,
        "root": marker in profile_json(profile),
        "adapter": marker in adapt_text,
        "adapter_unfenced": outside_fences(adapt_text, marker),
        "reviewer": marker in review_text,
        "reviewer_unfenced": outside_fences(review_text, marker),
        "data_csv": marker in parsed.csv,
    }


async def _standin(
    record: dict[str, Any], case: EvalCase, body: str, parsed: ParsedDataset, normalised: str, context: StaticContext
) -> None:
    """The stand-in as a full-code plan through the pipeline's check, then one light render and the host gates."""
    measured = record["static"]
    record["stage"] = "check"
    applied = apply_plan(normalised, AdaptPlan(full_code=compose_standin(normalised, body)))
    standin: dict[str, Any] = {"check": "rejected", "validator": [], "adaptation": []}
    measured["standin"] = standin
    if applied.code is None:
        standin["validator"] = sorted(set(applied.kinds)) or ["edits"]
        record["status"] = "standin_rejected"
        return
    working = applied.code
    regions = find_regions(normalised)
    palette = list(regions.imprint.entries) if regions.imprint else []
    adaptation = validate_adaptation(working, original_palette=palette)
    blocking = [finding.rule for finding in validate_security(working, library=case.library)]
    blocking += [finding.rule for finding in adaptation if finding.rule in BLOCKING_RULES]
    standin["literal_chars"] = new_literal_chars(normalised, working)
    if standin["literal_chars"] > MAX_NEW_LITERAL_CHARS:
        blocking.append("literal-budget")
    standin["validator"] = sorted(set(blocking))
    standin["adaptation"] = sorted({finding.rule for finding in adaptation if finding.rule not in BLOCKING_RULES})
    if blocking:
        record["status"] = "standin_rejected"
        return
    standin["check"] = "ok"
    runtime = PythonRuntime(cpu_seconds=context.settings.render_timeout_s)
    columns = [column.name for column in parsed.profile.columns]
    run_form = runtime.loader_block(
        runtime.normalise(working, case.library),
        columns=columns,
        dtypes=dict(parsed.column_dtypes),
        parse_dates=list(parsed.parse_dates),
    )
    job = RenderJob(
        job_id=secrets.token_hex(8),
        language=runtime.language,
        library=case.library,
        source=run_form,
        data_csv=parsed.csv,
        themes=("light",),
        timeout_s=float(context.settings.render_timeout_s),
    )
    record["stage"] = "render"
    started = time.monotonic()
    result = await context.backend.render(job)
    standin["render_s"] = round(time.monotonic() - started, 3)
    report = evaluate(result, themes=job.themes, library=case.library, rows=data_rows(parsed.csv))
    output = result.outputs.get("light")
    standin.update(
        passed=report.passed_host_gates,
        canvas_ok=report.canvas_ok,
        gates=list(report.failed_gates),
        blocking=list(report.blocking),
        wall_s=output.wall_s if output else None,
        max_rss_mb=output.max_rss_mb if output else None,
        cpu_s=output.cpu_s if output else None,
        probe_texts=len(output.probe.get("texts") or []) if output and isinstance(output.probe, dict) else None,
    )
    record["status"] = "rendered" if report.passed_host_gates else "render_failed"


# --- The run -----------------------------------------------------------------------------------


def summarize_static(records: list[dict[str, Any]]) -> dict[str, Any]:
    judged = [record for record in records if record["held"] is not None]
    return {
        "cases": len(records),
        "judged": len(judged),
        "held": sum(1 for record in judged if record["held"]),
        "broken": sorted(record["case_id"] for record in judged if not record["held"]),
        "errors": sorted(record["case_id"] for record in records if record["status"] == "error"),
        "model_pending": sorted(record["case_id"] for record in records if record["model"] == "pending"),
        "statuses": dict(sorted(Counter(record["status"] for record in records).items())),
    }


def _cell(value: Any) -> str:
    if value is None:
        return "–"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:,.1f}"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "none"
    return str(value)


def static_markdown(report: dict[str, Any]) -> str:
    """The report as a Markdown table, one row per case."""
    stamp, summary = report["stamp"], report["summary"]
    lines = [
        f"# Static stage, {stamp['date']}",
        "",
        f"{summary['cases']} cases (`--cases {stamp['cases']}`), renderer `{stamp['renderer']}`, git "
        f"`{(stamp.get('git_sha') or 'unknown')[:10]}`. {summary['held']} of {summary['judged']} cases with "
        "expectations held.",
        "",
    ]
    if summary["broken"]:
        lines += ["Expectations that did not hold:", ""]
        for record in report["runs"]:
            for line in record["mismatches"]:
                lines.append(f"- `{record['case_id']}`: {line}")
        lines.append("")
    lines += [
        "| Case | Status | Stage | Held | Bytes | Rows | Cols | Parse ms | Loader | Adapter profile | "
        "Adapter prompt | Judge | Stand-in gates | Render s | Peak MiB | Model |",
        "|---|---|---|---|--:|--:|--:|--:|---|--:|--:|--:|---|--:|--:|---|",
    ]
    for record in report["runs"]:
        measured = record["static"]
        standin = measured.get("standin") or {}
        profile = _cell(measured.get("adapter_profile_chars"))
        if measured.get("adapter_profile_trimmed"):
            profile += f" (of {_cell(measured.get('profile_chars'))})"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record['case_id']}`",
                    record["status"],
                    _cell(record["stage"]),
                    _cell(record["held"]),
                    _cell(measured.get("bytes")),
                    _cell(measured.get("rows")),
                    _cell(measured.get("columns")),
                    _cell(measured.get("parse_ms")),
                    _cell(measured.get("loader")),
                    profile,
                    _cell(measured.get("adapter_prompt_chars")),
                    _cell(measured.get("judge_chars")),
                    _cell(standin.get("gates")) if "gates" in standin else _cell(standin.get("check")),
                    _cell(standin.get("render_s")),
                    _cell(standin.get("max_rss_mb")),
                    record["model"],
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise ValueError(f"too many reports named {path.stem} in {path.parent}")


@dataclass
class StaticResult:
    report: dict[str, Any]
    report_path: Path
    summary_path: Path
    exit_code: int


async def run_static(
    cases: list[EvalCase], context: StaticContext, out: Path, *, selector: str, git_sha: str | None = None
) -> StaticResult:
    """Every case's static record, the report and its Markdown table under `out`; exit code 1 when one broke."""
    started = datetime.now(UTC)
    records = [await static_record(case, context) for case in cases]
    summary = summarize_static(records)
    stamp = {
        "date": started.date().isoformat(),
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "cases": selector,
        "case_count": len(cases),
        "renderer": context.renderer,
        "render_timeout_s": context.settings.render_timeout_s,
        "git_sha": git_sha,
    }
    report = {"schema": STATIC_SCHEMA, "kind": "static", "stamp": stamp, "summary": summary, "runs": records}
    out.mkdir(parents=True, exist_ok=True)
    report_path = _unique(out / f"{stamp['date']}-static.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_path = report_path.with_suffix(".md")
    summary_path.write_text(static_markdown(report), encoding="utf-8")
    exit_code = 1 if summary["broken"] or summary["errors"] else 0
    return StaticResult(report, report_path, summary_path, exit_code)
