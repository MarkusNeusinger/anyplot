"""Live prep eval: the root's step-1 data choices on short requests, through `/v1` in process with the real model.

Run it with the models from the settings (Claude Haiku 5.5 on Vertex AI `eu` by default):

    uv run --extra agents python -m agents.evals.prep
    uv run --extra agents python -m agents.evals.prep --provider gemini

Each case of `fixtures/prep/<id>.json` (`message`, `expected_operations`, `locale`, and
optionally `dataset_text`, `spec_id`, `library`, `tags`) opens a session on
`agents.main:app` through httpx's `ASGITransport`, as the matrix harness does, posts
the dataset when the case has one (the dataset judge runs for real), sends the message
as a free-text turn (the scope judge, then the root with its tools) and reads the
`prepare_data` and `generate_data` calls the root made from the session's events. The
pipeline never runs: no case confirms the data or asks for a plot, so no render and no
adapter call happens.

Scoring is exact operation match, order-insensitive, and every `prepare_data` and
`generate_data` call of the turn must have succeeded: the operations are applied in
order, so a list the data refuses (a column named before its rename, a type its cells
cannot take) is a miss however it reads, and so is a formula the server cannot compute
(`failed_calls`). The operations of every `prepare_data` call of the turn are taken
together (one call with two operations and two calls with one each are the same) and
each is normalised through the `Operation`
models (`canonical_operations`): a default the model left out and one it wrote are
the same, a `set_type` `decimal` equal to the dataset's own counts as left out, and
the column list of `drop_columns` and `pivot_longer` and the conditions of
`drop_rows` are sets. A `generate_data` call is one item `{"op": "generate_data",
"variables": [...], "series": [...]}`, normalised through the `generate.Generate` model
the same way for the report (defaults left out, the whitespace of every expression and
endpoint removed, the series a set; the variables keep their order, which decides the
grid's), and two calls match when they compute the same table (`comparison_key`): the
same names, points and values, so `-3.0` is `-3`, `tau` is `2*pi` and `x*x` is
`x**2`. A case with
`expected_operations: []` passes when the root made no data call: a scope refusal and
a plain reply both pass, and the report lists every tool call and the refusal, so a
false refusal stays visible. The gate is `--min-exact` (80 percent) of the answered
cases.

A case is `unavailable` when its dataset could not be stored (`503 guard_unavailable`)
or its turn ended with an `error` event (the judge down, `capacity`); it counts in no
rate, and more than `--max-unavailable` (10 percent) of them exit 4. A dataset the
judge refuses (`403 data_refused`) is a miss, because the fixtures are synthetic
tables that must pass.

A case makes about five model calls: the dataset judge, the scope judge, and the root
two or three times (a profile read, the tool call, the reply). Under the 30 requests
per minute Vertex quota for Claude Haiku in `eu` (see `scope.py`), `--calls-per-minute`
(25 by default) spaces the starts of the cases `CALLS_PER_CASE` times further apart
than the scope eval spaces its judge calls: 12 seconds at the default, so 23 cases
take about 5 minutes; the cases run one at a time. The cost is the list price of
every call the attribution log booked (`pricing.call_cost`, `pricing.judge_cost`).

It writes `<out>/<date>-prep-<model>.json` (the stamp, the gates, the summary, every
case's canonical expected and found operations, its tool calls, refusal, cost and
latency; never a dataset or a message, which stay in the fixtures) and prints a table.
The exit code is 0 when the gate holds, 1 when it does not, 2 for a setup error (a
fixture that does not load or whose expected operations fail the `Operation` or
`Generate` models, an unpriced model) and 4 for an outage.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from collections import Counter, defaultdict
from collections.abc import MutableMapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agents.evals.matrix import (
    ATTRIBUTION_LOGGER,
    EVAL_GLOBAL_DAILY_TOKENS,
    MODEL_PROVIDERS,
    PROVIDER_DEFAULTS,
    AttributionCollector,
    parse_events,
)
from agents.evals.pricing import LOCATION_SURCHARGE, UnknownPrice, call_cost, judge_cost, price_of
from agents.evals.scope import Pacer


if TYPE_CHECKING:  # importing agents.anyplot builds the agents, so the runtime imports wait for `configure`
    from agents.anyplot.services import Services
    from agents.anyplot.settings import AgentSettings
    from agents.main import Runtime


EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = EVALS_DIR / "fixtures" / "prep"
DEFAULT_OUT = EVALS_DIR / "reports"
REPORT_SCHEMA = 1
MAX_MESSAGE_CHARS = 2_000  # the /messages limit (agents/main.py)
MAX_DATASET_CHARS = 200 * 1024
CALLS_PER_CASE = 5
"""Model calls a case makes, about: the dataset judge, the scope judge, two or three root calls."""
DEFAULT_CALLS_PER_MINUTE = 25.0
DEFAULT_MIN_EXACT = 0.8
DEFAULT_MAX_UNAVAILABLE = 0.1
EXIT_OK, EXIT_FAILED, EXIT_SETUP, EXIT_OUTAGE = 0, 1, 2, 4
PREPARE_TOOL = "prepare_data"
GENERATE_TOOL = "generate_data"
DATA_TOOLS = frozenset({PREPARE_TOOL, GENERATE_TOOL})
"""The root's tools that store a dataset version; every call of them in a turn must succeed."""
SET_OPERATIONS: dict[str, str] = {"drop_columns": "columns", "pivot_longer": "columns", "drop_rows": "where"}
"""Per operation, the list field whose order carries no meaning (compared as a set)."""


class SetupError(Exception):
    """A run that cannot start: its message says what to change."""


class PrepCase(BaseModel):
    """One data request, on one small dataset or none, with the operations the root should choose."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]{1,64}$")
    dataset_text: str | None = Field(default=None, min_length=1, max_length=MAX_DATASET_CHARS)
    """Posted before the message; a formula case may leave it out (`generate_data` makes the first data)."""
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    expected_operations: list[dict[str, Any]]
    locale: str = Field(pattern=r"^[a-z]{2}$")
    spec_id: str = Field(default="scatter-basic", pattern=r"^[a-z0-9-]{1,100}$")
    library: str = Field(default="matplotlib", pattern=r"^[a-z0-9]{1,32}$")
    tags: list[str] = Field(default_factory=list)


def load_cases(directory: Path) -> list[PrepCase]:
    """Every `<id>.json` of `directory`, the id from the file name; raises `SetupError` for one that does not load."""
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise SetupError(f"{directory} holds no case")
    cases = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cases.append(PrepCase.model_validate({"id": path.stem, **data}))
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            raise SetupError(f"{path} does not load: {exc}") from exc
    return cases


def canonical_operations(operations: Sequence[dict[str, Any]], decimal: str) -> list[str]:
    """The operations as sorted JSON lines after the `Operation` and `Generate` models and the order-free normalisations.

    An item with `"op": "generate_data"` is one `generate_data` call (`canonical_generate`);
    every other item is a `prepare_data` operation. Raises `ValidationError` for an item
    the models refuse (a fixture's expectation is checked this way at setup; the root's
    own calls were checked by ToolSafety already).
    """
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation

    generated = [item for item in operations if isinstance(item, dict) and item.get("op") == GENERATE_TOOL]
    prepared = [item for item in operations if not (isinstance(item, dict) and item.get("op") == GENERATE_TOOL)]
    lines = [canonical_generate(item) for item in generated]
    for operation in TypeAdapter(list[Operation]).validate_python(prepared):
        data = operation.model_dump(exclude_none=True)
        if data["op"] == "set_type" and data.get("decimal") == decimal:
            data.pop("decimal")
        if data["op"] == "drop_rows":
            data["where"] = _sorted_conditions(data["where"])
        elif data["op"] == "classify":  # the rules keep their order (the first that holds wins), their conditions not
            for rule in data["rules"]:
                rule["where"] = _sorted_conditions(rule["where"])
        elif data["op"] in SET_OPERATIONS:
            data[SET_OPERATIONS[data["op"]]] = sorted(data[SET_OPERATIONS[data["op"]]])
        lines.append(json.dumps(data, sort_keys=True, ensure_ascii=False))
    return sorted(lines)


def _sorted_conditions(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(conditions, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))


def canonical_generate(item: dict[str, Any]) -> str:
    """One `generate_data` call as a JSON line: after the `Generate` model, defaults left out, whitespace removed.

    The whitespace of an expression or an endpoint carries no meaning (`x ** 2` is
    `x**2`); the series are a set, sorted by name; the variables keep their order. A
    JSON number as an endpoint is its text, as the model reads it. The line is for the
    report; a match compares the table the call computes (`comparison_key`). Raises
    `ValidationError`.
    """
    from agents.anyplot.data.generate import Generate

    spec = Generate.model_validate({key: value for key, value in item.items() if key != "op"})
    data = spec.model_dump(exclude_defaults=True)
    for variable in data["variables"]:
        for key in ("start", "stop"):
            variable[key] = "".join(variable[key].split())
    for series in data["series"]:
        series["expression"] = "".join(series["expression"].split())
    data["series"] = sorted(data["series"], key=lambda series: series["name"])
    return json.dumps({"op": GENERATE_TOOL, **data}, sort_keys=True, ensure_ascii=False)


def comparison_key(line: str) -> str:
    """What a canonical line is compared by: the line itself, or for a `generate_data` call the table it computes.

    Two formula calls that compute the same table (the same names, points and values at
    eight significant digits) are the same choice however the model wrote the endpoints
    or the expressions (`-3.0` and `-3`, `tau` and `2*pi`, `x*x` and `x**2`). A call the
    server cannot compute keeps its line, so it matches nothing but itself.
    """
    from agents.anyplot.data.generate import Generate, GenerateError, generate

    try:
        data = json.loads(line)
    except ValueError:
        return line
    if not isinstance(data, dict) or data.get("op") != GENERATE_TOOL:
        return line
    try:
        table = generate(Generate.model_validate({key: value for key, value in data.items() if key != "op"})).csv
    except (ValidationError, GenerateError):
        return line
    return json.dumps({"op": GENERATE_TOOL, "table": hashlib.sha256(table.encode("utf-8")).hexdigest()})


def same_operations(found: Sequence[str], expected: Sequence[str]) -> bool:
    """Whether the found canonical lines are the expected ones, compared by `comparison_key`, order-insensitive."""
    return sorted(map(comparison_key, found)) == sorted(map(comparison_key, expected))


def describe(line: str) -> str:
    """A canonical line as a short phrase for the table: `set_type Anteil number`, `aggregate Betrag sum by Datum/month`."""
    data = json.loads(line)
    op = data["op"]
    if op == GENERATE_TOOL:
        from agents.anyplot.data.generate import DEFAULT_POINTS

        spans = [
            f"{variable.get('name', 'x')} {variable['start']}..{variable['stop']} ({variable.get('points', DEFAULT_POINTS)})"
            for variable in data["variables"]
        ]
        formulas = ", ".join(f"{series['name']} = {series['expression']}" for series in data["series"])
        return f"generate_data {' x '.join(spans)}: {formulas}"
    if op == "rename":
        return f"rename {data['column']} to {data['name']}"
    if op == "drop_columns":
        return "drop_columns " + ", ".join(data["columns"])
    if op == "drop_rows":
        return "drop_rows " + _conditions(data["where"])
    if op == "classify":
        rules = "; ".join(f"{rule['label']!r} if {_conditions(rule['where'])}" for rule in data["rules"])
        otherwise = f"; else {data['otherwise']!r}" if "otherwise" in data else ""
        return f"classify {data['name']}: {rules}{otherwise}"
    if op == "set_type":
        extra = [data[key] for key in ("date_format", "decimal") if key in data]
        return f"set_type {data['column']} {data['type']}" + (f" ({', '.join(extra)})" if extra else "")
    if op == "aggregate":
        period = f"/{data['period']}" if "period" in data else ""
        return f"aggregate {data['column']} {data['how']} by {', '.join(data['by'])}{period}"
    if op == "sort":
        return f"sort {data['column']} {'desc' if data.get('descending') else 'asc'}"
    if op == "pivot_longer":
        return f"pivot_longer {', '.join(data['columns'])} into {data['names_to']}/{data['values_to']}"
    return f"pivot_wider {data['names_from']} with {data['values_from']} by {', '.join(data['index'])}"


def _conditions(conditions: list[dict[str, Any]]) -> str:
    return " and ".join(f"{c['column']} {c['test']}" + (f" {c['value']!r}" if "value" in c else "") for c in conditions)


@dataclass
class CaseResult:
    """What one case's turn did; `operations` is None when the case got no answer (`unavailable`)."""

    id: str
    operations: list[dict[str, Any]] | None
    expected: list[str]
    found: list[str] = field(default_factory=list)
    match: bool | None = None
    tool_calls: list[str] = field(default_factory=list)
    failed_calls: int = 0
    """`prepare_data` and `generate_data` calls of the turn the service refused or that failed: the case is a miss."""
    refusal: str | None = None
    llm_calls: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    cause: str | None = None


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"http {response.status_code}"
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else f"http {response.status_code}"


def _book(result: CaseResult, lines: list[dict[str, Any]], settings: AgentSettings) -> None:
    """Add one request's attribution lines to the result: model calls at list price, the judges too."""
    for line in lines:
        hook = line.get("hook")
        if hook == "model":
            result.llm_calls += 1
            result.cost_usd += call_cost(settings.model, settings.location, line)
        elif hook in ("data_judge", "scope_guard"):
            judge_in, judge_out = line.get("judge_input"), line.get("judge_output")
            judge_in = judge_in if isinstance(judge_in, int) else int(line.get("judge_tokens") or 0)
            judge_out = judge_out if isinstance(judge_out, int) else 0
            result.cost_usd += judge_cost(settings.judge_model, settings.location, judge_in, judge_out)


@dataclass
class CaseRunner:
    """Runs cases one at a time against the in-process app, the model and the judge the settings name."""

    client: httpx.AsyncClient
    runtime: Runtime
    collector: AttributionCollector
    settings: AgentSettings

    async def run(self, case: PrepCase) -> CaseResult:
        from agents.anyplot.data.parse import parse_dataset
        from agents.anyplot.dev_fixture import snapshot_from_repo

        digest = hashlib.sha256(case.id.encode()).hexdigest()
        user = f"prep_{digest[:12]}"
        tag = f"prep-{digest[:10]}"
        decimal = parse_dataset(case.dataset_text).profile.decimal if case.dataset_text else "."
        result = CaseResult(case.id, None, canonical_operations(case.expected_operations, decimal))

        def headers(step: str) -> dict[str, str]:
            return {"X-Anyplot-User": user, "X-Request-Id": f"{tag}-{step}"}

        started = time.monotonic()
        sid: str | None = None
        try:
            body = {
                "user": user,
                "spec_id": case.spec_id,
                "library": case.library,
                "locale": case.locale,
                "snapshot": snapshot_from_repo(case.spec_id, case.library).model_dump(),
            }
            opened = await self.client.post("/v1/sessions", headers=headers("s"), json=body)
            if opened.status_code != 200:
                result.cause = f"session: {_detail(opened)}"
                return result
            sid = opened.json()["session_id"]
            if case.dataset_text is not None:
                stored = await self.client.post(
                    f"/v1/sessions/{sid}/dataset", headers=headers("d"), json={"text": case.dataset_text}
                )
                _book(result, self.collector.take(f"{tag}-d"), self.settings)
                if stored.status_code != 200:
                    if stored.status_code == 403:  # the judge refused a synthetic table: a miss, not an outage
                        result.operations, result.match, result.cause = [], False, f"dataset: {_detail(stored)}"
                    else:
                        result.cause = f"dataset: {_detail(stored)}"
                    return result
            turn = await self.client.post(
                f"/v1/sessions/{sid}/messages", headers=headers("m"), json={"text": case.message}
            )
            _book(result, self.collector.take(f"{tag}-m"), self.settings)
            if turn.status_code != 200:
                result.cause = f"turn: {_detail(turn)}"
                return result
            events = parse_events([(time.monotonic(), turn.content)], started)
            for _, name, data in events:
                if name == "error":
                    result.cause = f"error: {data.get('code')}"
                    return result
                if name == "refusal":
                    result.refusal = str(data.get("code"))
            await self._read_calls(result, user, sid, decimal)
        finally:
            result.latency_s = round(time.monotonic() - started, 3)
            if sid is not None:
                try:
                    await self.client.delete(f"/v1/sessions/{sid}", headers=headers("x"))
                except Exception as exc:  # the next case opens its own session either way
                    logging.getLogger(__name__).warning(
                        "deleting the session of %s failed: %s", case.id, type(exc).__name__
                    )
            for step in ("s", "d", "m", "x"):
                self.collector.take(f"{tag}-{step}")
        return result

    async def _read_calls(self, result: CaseResult, user: str, sid: str, decimal: str) -> None:
        """The tool calls of the turn from the session's events; the data calls' operations, canonical."""
        session = await self.runtime.session(user, sid)
        operations: list[dict[str, Any]] = []
        for event in session.events:
            for call in event.get_function_calls():
                result.tool_calls.append(str(call.name))
                if call.name == PREPARE_TOOL and isinstance(call.args, dict):
                    items = call.args.get("operations")
                    if isinstance(items, list):
                        operations.extend(item for item in items if isinstance(item, dict))
                elif call.name == GENERATE_TOOL and isinstance(call.args, dict):
                    operations.append({"op": GENERATE_TOOL, **call.args})
            for response in event.get_function_responses():
                # The operations are applied in order, so a list the data refuses (a column named
                # before its rename, a type the cells cannot take) is a miss however it reads; so is
                # a formula the server cannot compute.
                if response.name in DATA_TOOLS:
                    answer = response.response if isinstance(response.response, dict) else {}
                    result.failed_calls += answer.get("status") != "ok"
        result.operations = operations
        try:
            result.found = canonical_operations(operations, decimal)
        except ValidationError:  # ToolSafety refused the call; the root got `invalid_arguments`
            result.found = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in operations]
        result.match = same_operations(result.found, result.expected) and not result.failed_calls


async def run_cases(
    cases: Sequence[PrepCase], *, runtime: Runtime, services: Services, pacer: Pacer | None = None, echo: Any = None
) -> list[CaseResult]:
    """Every case through the in-process app, one at a time and paced by `pacer`, in the case order."""
    from agents import main as service
    from agents.anyplot.services import set_services
    from agents.anyplot.settings import get_settings

    settings = get_settings()
    set_services(services)
    saved_overrides = dict(service.app.dependency_overrides)
    service.app.dependency_overrides[service.get_runtime] = lambda: runtime
    service.app.dependency_overrides[service.check_caller] = lambda: None  # in process: there is no caller to check
    collector = AttributionCollector()
    attribution_logger = logging.getLogger(ATTRIBUTION_LOGGER)
    saved_level = attribution_logger.level
    attribution_logger.setLevel(logging.INFO)
    attribution_logger.addHandler(collector)
    results: list[CaseResult] = []
    try:
        transport = httpx.ASGITransport(app=service.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://agents", timeout=None) as client:
            runner = CaseRunner(client, runtime, collector, settings)
            for index, case in enumerate(cases, start=1):
                if pacer is not None:
                    await pacer.wait()
                result = await runner.run(case)
                results.append(result)
                if echo is not None:
                    state = "unavailable" if result.operations is None else "match" if result.match else "miss"
                    echo(f"[{index}/{len(cases)}] {case.id}: {state}, ${result.cost_usd:.4f}, {result.latency_s:.1f} s")
    finally:
        attribution_logger.removeHandler(collector)
        attribution_logger.setLevel(saved_level)
        service.app.dependency_overrides.clear()
        service.app.dependency_overrides.update(saved_overrides)
    return results


def _rate(hits: int, total: int) -> float | None:
    return round(hits / total, 4) if total else None


def _block(results: Sequence[CaseResult]) -> dict[str, Any]:
    answered = [result for result in results if result.operations is not None]
    return {
        "cases": len(results),
        "unavailable": len(results) - len(answered),
        "matched": sum(1 for result in answered if result.match),
        "exact": _rate(sum(1 for result in answered if result.match), len(answered)),
    }


def score(cases: Sequence[PrepCase], results: Sequence[CaseResult]) -> dict[str, Any]:
    """The summary, the per-tag table and the misses of one run."""
    by_id = {result.id: result for result in results}
    pairs = [(case, by_id[case.id]) for case in cases if case.id in by_id]
    summary = {
        **_block([result for _, result in pairs]),
        "unavailable_rate": _rate(sum(1 for _, result in pairs if result.operations is None), len(pairs)),
        "llm_calls": sum(result.llm_calls for _, result in pairs),
        "cost_usd": round(sum(result.cost_usd for _, result in pairs), 8),
    }
    tags: dict[str, list[CaseResult]] = defaultdict(list)
    for case, result in pairs:
        for tag in [case.locale, *case.tags]:
            tags[tag].append(result)
    misses = [
        {"id": case.id, "expected": result.expected, "found": result.found, "refusal": result.refusal}
        for case, result in pairs
        if result.operations is not None and not result.match
    ]
    causes = Counter(result.cause or "unknown" for _, result in pairs if result.operations is None)
    return {
        "summary": summary,
        "per_tag": {tag: _block(items) for tag, items in sorted(tags.items())},
        "misses": misses,
        "unavailable_causes": dict(causes.most_common()),
    }


@dataclass(frozen=True)
class Gates:
    min_exact: float = DEFAULT_MIN_EXACT
    max_unavailable: float = DEFAULT_MAX_UNAVAILABLE


def verdict_of(summary: dict[str, Any], gates: Gates) -> tuple[int, list[str]]:
    """The exit code and the reasons for it: an outage first, then the exact-match gate."""
    if (summary["unavailable_rate"] or 0.0) > gates.max_unavailable:
        return EXIT_OUTAGE, [f"{summary['unavailable']} cases got no answer (more than {gates.max_unavailable:.0%})"]
    exact = summary["exact"]
    if exact is None or exact < gates.min_exact:
        return EXIT_FAILED, [f"exact match {exact} is below {gates.min_exact}"]
    return EXIT_OK, []


def table(cases: Sequence[PrepCase], results: Sequence[CaseResult]) -> str:
    """One line per case: the id, the expected operations, the found ones, the outcome."""
    by_id = {result.id: result for result in results}
    rows = [("case", "expected", "found", "result")]
    for case in cases:
        result = by_id.get(case.id)
        if result is None:
            continue
        expected = "; ".join(describe(line) for line in result.expected) or "no operation"
        if result.operations is None:
            found, outcome = result.cause or "unavailable", "unavailable"
        else:
            found = "; ".join(_safe_describe(line) for line in result.found) or (
                f"no operation (refusal {result.refusal})" if result.refusal else "no operation"
            )
            outcome = "match" if result.match else "miss"
        rows.append((case.id, expected, found, outcome))
    widths = [min(60, max(len(row[column]) for row in rows)) for column in range(4)]
    return "\n".join("  ".join(cell[: widths[i]].ljust(widths[i]) for i, cell in enumerate(row)) for row in rows)


def _safe_describe(line: str) -> str:
    try:
        return describe(line)
    except (KeyError, TypeError, ValueError):
        return line


def summary_text(scored: dict[str, Any], reasons: list[str]) -> str:
    summary = scored["summary"]
    exact = "n/a" if summary["exact"] is None else f"{summary['exact']:.1%}"
    lines = [
        f"cases {summary['cases']}, unavailable {summary['unavailable']}, matched {summary['matched']}, "
        f"exact {exact}, llm calls {summary['llm_calls']}, cost ${summary['cost_usd']:.4f}",
        "per tag: "
        + ", ".join(
            f"{tag} {block['matched']}/{block['cases'] - block['unavailable']}"
            for tag, block in scored["per_tag"].items()
        ),
    ]
    if scored["unavailable_causes"]:
        lines.append(
            "unavailable: " + ", ".join(f"{count} x {cause}" for cause, count in scored["unavailable_causes"].items())
        )
    lines.append("PASS" if not reasons else "FAIL: " + "; ".join(reasons))
    return "\n".join(lines)


# --- Command line -----------------------------------------------------------------------------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.prep",
        description="Score the root's prepare_data and generate_data choices on the prep cases.",
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="case directory (default fixtures/prep)")
    parser.add_argument("--tags", help="only the cases with any of these comma-separated tags (a locale is a tag)")
    parser.add_argument("--provider", choices=sorted(PROVIDER_DEFAULTS), help="model family (default: the settings)")
    parser.add_argument("--model", help="the root's model; the provider's default when only --provider")
    parser.add_argument("--judge-model", help="the judges' model; the provider's default when only --provider")
    parser.add_argument("--location", choices=sorted(LOCATION_SURCHARGE), help="Vertex AI location (default eu)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default agents/evals/reports)")
    parser.add_argument(
        "--calls-per-minute",
        type=float,
        default=DEFAULT_CALLS_PER_MINUTE,
        help=f"model-call starts per minute (25; a case makes about {CALLS_PER_CASE}, so cases start 60 x {CALLS_PER_CASE} / N "
        "seconds apart; 0: unpaced)",
    )
    parser.add_argument("--min-exact", type=float, default=DEFAULT_MIN_EXACT)
    parser.add_argument("--max-unavailable", type=float, default=DEFAULT_MAX_UNAVAILABLE)
    args = parser.parse_args(argv)
    if args.calls_per_minute < 0:
        parser.error("--calls-per-minute must be 0 (unpaced) or more")
    for name in ("min_exact", "max_unavailable"):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} is a fraction between 0 and 1")
    return args


def configure(args: argparse.Namespace, environ: MutableMapping[str, str]) -> None:
    """Write the flags into the `AGENT_*` environment; runs before any `agents.anyplot` import (as in scope.py)."""
    environ["PYTHON_DOTENV_DISABLED"] = "1"
    environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    environ.pop("AGENT_DEV_FIXTURE", None)
    environ.setdefault("ENVIRONMENT", "development")
    environ.setdefault("AGENT_RENDERER", "fake")  # no case renders; the fake backend needs no service
    environ["AGENT_RUNS_PER_MINUTE"] = "60"  # the pacer spaces the cases; the queue's own rate would double the wait
    environ["AGENT_GLOBAL_DAILY_TOKEN_BUDGET"] = str(EVAL_GLOBAL_DAILY_TOKENS)
    provider = args.provider
    if provider is None and args.model:
        provider = next((name for prefix, name in MODEL_PROVIDERS.items() if args.model.startswith(prefix)), None)
        if provider is None:
            raise SetupError(f"cannot tell the provider of {args.model!r}; pass --provider")
    if provider is not None:
        default_model, default_judge = PROVIDER_DEFAULTS[provider]
        environ["AGENT_PROVIDER"] = provider
        environ["AGENT_MODEL"] = args.model or default_model
        environ["AGENT_JUDGE_MODEL"] = args.judge_model or default_judge
    elif args.judge_model:
        environ["AGENT_JUDGE_MODEL"] = args.judge_model
    if args.location:
        environ["AGENT_LOCATION"] = args.location


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def stamp(settings: AgentSettings, cases: Sequence[PrepCase]) -> dict[str, Any]:
    from agents.anyplot.policy import root_instruction

    return {
        "schema": REPORT_SCHEMA,
        "date": datetime.now(UTC).date().isoformat(),
        "provider": settings.provider,
        "model": settings.model,
        "judge_model": settings.judge_model,
        "location": settings.location,
        "root_prompt_hash": _sha(root_instruction()),
        "cases_hash": _sha(json.dumps([case.model_dump() for case in cases], sort_keys=True, ensure_ascii=False)),
        "cases": len(cases),
    }


def check_cases(cases: Sequence[PrepCase]) -> None:
    """Every expected operation list passes the `Operation` and `Generate` models; raises `SetupError` otherwise."""
    for case in cases:
        try:
            canonical_operations(case.expected_operations, ".")
        except ValidationError as exc:
            raise SetupError(f"case {case.id}: expected_operations do not validate: {exc}") from exc


def main(argv: list[str] | None = None, *, runtime: Runtime | None = None, services: Services | None = None) -> int:
    """Run the eval; `runtime` and `services` replace the service's own (tests)."""
    args = parse_args(argv)
    try:
        configure(args, os.environ)
        cases = load_cases(args.cases)
        wanted: set[str] = set()
        if args.tags:
            wanted = {tag.strip() for tag in args.tags.split(",") if tag.strip()}
            cases = [case for case in cases if wanted & {case.locale, *case.tags}]
            if not cases:
                raise SetupError(f"no case carries any of the tags {', '.join(sorted(wanted))}")
        from agents import main as service
        from agents.anyplot.services import Services
        from agents.anyplot.settings import get_settings

        get_settings.cache_clear()
        settings = get_settings()
        price_of(settings.model)
        price_of(settings.judge_model)
        check_cases(cases)
    except (SetupError, UnknownPrice, ValidationError) as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return EXIT_SETUP
    pacer = Pacer(args.calls_per_minute / CALLS_PER_CASE) if args.calls_per_minute else None
    results = asyncio.run(
        run_cases(
            cases,
            runtime=runtime or service.Runtime(),
            services=services or Services(),
            pacer=pacer,
            echo=lambda text: print(text, file=sys.stderr, flush=True),
        )
    )
    scored = score(cases, results)
    gates = Gates(args.min_exact, args.max_unavailable)
    code, reasons = verdict_of(scored["summary"], gates)
    report = {
        "stamp": stamp(settings, cases),
        "calls_per_minute": args.calls_per_minute,
        "gates": asdict(gates),
        "passed": code == EXIT_OK,
        "reasons": reasons,
        **scored,
        "results": [asdict(result) for result in results],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    suffix = "-" + "-".join(sorted(wanted)) if wanted else ""
    path = args.out / f"{report['stamp']['date']}-prep-{settings.model}{suffix}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(table(cases, results))
    print(summary_text(scored, reasons))
    print(f"report: {path}")
    return code


if __name__ == "__main__":
    sys.exit(main())
