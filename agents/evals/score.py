"""Score a matrix run's renders with the catalogue rubric: step 1 of the owner's quality ladder.

The owner's decision of 2026-10-12 (memory `project_agent_quality_ladder`): an agent
result should ship only once it reaches a score threshold, scored like the pipeline
scores catalogue implementations, and the escalation ladder (Haiku repair, then a
Sonnet and an Opus advisor) is designed from measurements first. This script measures
without changing the agent: it reads a matrix report that ran with `--keep-attempts`,
scores each run's first render and its shipped render with `agents.anyplot.scoring`
(the catalogue rubric's 16 user-visible criteria, Claude Opus by default, the
pipeline's review model), and writes `<report>-scores.json` and `<report>-scores.md`
next to the report: the score distributions, what repair 1 gained, the top deductions,
the runs whose gates were clean but whose score is low, and the cost and latency of
today's runs and of the scoring.

    uv run --extra agents python -m agents.evals.score \
        agents/evals/reports/<run>/<date>-claude-haiku-5-5.json

Before any scoring call the script probes the model with a 5-token request and stops
with exit code 2 when the model is not reachable (for example a 404 while the model is
not enabled in Vertex AI's Model Garden). It never falls back to another model: a score
from a weaker judge is a different measurement.

Which render is which: the harness keeps every render a turn sends to the renderer, in
order (`attempt_renders`). The first render is the first one of the first turn. The
shipped render is the one of the shipped attempt in the last turn, counted over the
attempts that reached the renderer (an attempt that failed its check renders nothing).
When both are the same render it is scored once and counts for both.
"""

import argparse
import asyncio
import base64
import io
import json
import statistics
import sys
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.anyplot.scoring import (
    SCORED,
    TOOL_NAME,
    TOOL_SCHEMA,
    ScoreError,
    ScoreRequest,
    ScoreResult,
    parse_answer,
    system_prompt,
    user_text,
)


DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_LOCATION = "eu"
DEFAULT_EFFORT = "high"
DEFAULT_CALLS_PER_MINUTE = 2.0
"""One scoring call carries about 25,000 input tokens; a new model's default per-minute quota can be small."""
CLI_CALLS_PER_MINUTE = 30.0
"""On the claude-cli transport the subscription's limits apply, not a Vertex AI quota; the CLI client
runs at most `cli_transport.DEFAULT_CONCURRENCY` calls at once."""
MAX_TOKENS = 16_000
MAX_IMAGE_BYTES = 3_500_000
"""A PNG above this is re-encoded smaller; the API refuses images above 5 MB."""
THRESHOLDS = (90, 85, 80)
TYPICAL_CALL_TOKENS: dict[str, int] = {"prompt": 24_600, "cached": 17_800, "candidates": 1_400}
"""One scoring call as measured on 2026-10-12 (Opus 5.5, high effort): the rubric prefix cached
(about 17,800 tokens), the request and the image uncached, about 1,400 output tokens."""


def estimate_usd(model: str, location: str, calls: int) -> float:
    """The list-price estimate of `calls` scoring calls, the first one writing the cache."""
    from agents.evals.pricing import call_cost

    if calls <= 0:
        return 0.0
    warm = call_cost(model, location, TYPICAL_CALL_TOKENS)
    first = call_cost(
        model, location, {**TYPICAL_CALL_TOKENS, "cached": 0, "cache_write": TYPICAL_CALL_TOKENS["cached"]}
    )
    return first + warm * (calls - 1)


NO_RENDER_STAGES = frozenset(
    {"adapter_schema", "adapter_truncated", "adapter_full_code", "edit_apply", "validator", "loader"}
)
"""Attempt stages that end before the renderer: such an attempt leaves no render behind."""
REPO = Path(__file__).resolve().parents[2]


class SetupError(Exception):
    """The model or the report cannot be used; exit code 2."""


@dataclass
class Target:
    """One render to score, with what identifies it in the report."""

    run: str
    case_id: str
    spec_id: str
    library: str
    role: str
    """`first`, `shipped`, or `both` when the first render is also the shipped one."""
    png: Path
    code: Path
    data: Path
    theme: str
    language: str
    bindings: list[dict[str, str]] | None


@dataclass
class Scored:
    target: Target
    result: ScoreResult | None
    error: str | None = None
    cost_usd: float = 0.0
    latency_s: float = 0.0
    tokens: dict[str, int] = field(default_factory=dict)


# --- Which renders ------------------------------------------------------------------------------


def shipped_render_index(record: dict[str, Any]) -> int | None:
    """The 1-based index, among the last turn's renders, of the shipped attempt's render."""
    shipped = record.get("shipped_attempt")
    stages = record.get("stages") or []
    if not isinstance(shipped, int) or shipped < 1 or len(stages) < shipped:
        return None
    rendered = [stage not in NO_RENDER_STAGES for stage in stages[:shipped]]
    return sum(rendered) if rendered[-1] else None


def targets_of(record: dict[str, Any], base: Path) -> list[Target]:
    """The first and the shipped render of one run record (one target when they are the same)."""
    every = list(record.get("attempt_renders") or [])
    entries = [entry for entry in every if entry.get("png")]
    if not entries:
        return []
    run = f"{record['case_id']}#r{record.get('repeat', 1)}"
    language = (record.get("language") or {}).get("language") if isinstance(record.get("language"), dict) else None

    def target(entry: dict[str, Any], role: str) -> Target:
        return Target(
            run=run,
            case_id=record["case_id"],
            spec_id=record["spec_id"],
            library=record["library"],
            role=role,
            png=base / entry["png"],
            code=base / entry["code"],
            data=base / entry["data"],
            theme=entry.get("theme", "light"),
            language=language or "en",
            bindings=None,
        )

    first_turn = entries[0]["turn"]
    first = entries[0]
    shipped: dict[str, Any] | None = None
    if record.get("status") in ("ok", "needs_attention"):
        # Every render of the last turn counts, one without a PNG too: the index counts the attempts
        # that reached the renderer, whatever came out. Only the selected one must have a PNG.
        last_turn = every[-1]["turn"]
        turn_entries = [entry for entry in every if entry["turn"] == last_turn]
        index = shipped_render_index(record)
        if index is not None and 1 <= index <= len(turn_entries) and turn_entries[index - 1].get("png"):
            shipped = turn_entries[index - 1]
    if shipped is not None and shipped["turn"] == first_turn and shipped["render"] == first["render"]:
        return [target(first, "both")]
    found = [target(first, "first")]
    if shipped is not None:
        found.append(target(shipped, "shipped"))
    return found


# --- Requests -----------------------------------------------------------------------------------


def spec_text(spec_id: str) -> str:
    """The spec as the catalogue review reads it: the whole `specification.md`."""
    return (REPO / "plots" / spec_id / "specification.md").read_text(encoding="utf-8")


def request_for(target: Target, case_bindings: list[dict[str, str]] | None) -> ScoreRequest:
    """The scorer's request: the spec, the code, the data's profile and bindings, the PNG."""
    from agents.anyplot.briefs import profile_summary
    from agents.anyplot.data.bindings import default_bindings
    from agents.anyplot.data.parse import MAX_CANONICAL_BYTES, parse_dataset
    from agents.anyplot.dev_fixture import snapshot_from_repo

    # The case's data.csv is the render job's canonical CSV, which may be up to `MAX_CANONICAL_BYTES` (a 1 MB
    # paste grows to about 3.8 MB in the stress case `stress-csv-expansion`).
    parsed = parse_dataset(target.data.read_text(encoding="utf-8"), max_bytes=MAX_CANONICAL_BYTES)
    if case_bindings is None:
        roles = snapshot_from_repo(target.spec_id, target.library).roles()
        case_bindings = [binding.model_dump() for binding in default_bindings(roles, parsed.profile)]
    return ScoreRequest(
        spec_text=spec_text(target.spec_id),
        code=target.code.read_text(encoding="utf-8"),
        profile_summary=profile_summary(parsed.profile),
        bindings_json=json.dumps(case_bindings, ensure_ascii=False),
        png=target.png.read_bytes(),
        theme=target.theme,
        plot_language=target.language,
    )


def image_block(png: bytes) -> dict[str, Any]:
    """The PNG as a base64 image block, re-encoded smaller when it is too large for the API."""
    if len(png) > MAX_IMAGE_BYTES:
        from PIL import Image

        with Image.open(io.BytesIO(png)) as image:
            image.thumbnail((1600, 1600))
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            png = buffer.getvalue()
    data = base64.standard_b64encode(png).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}


def tool() -> dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "description": "Submit the score of the attached render: points per criterion, defect lines, suggestions.",
        "input_schema": TOOL_SCHEMA,
        "strict": True,
    }


# --- Calls --------------------------------------------------------------------------------------


@dataclass
class Scorer:
    model: str
    location: str
    effort: str
    project: str = "anyplot"
    system: str = field(default_factory=system_prompt)
    client: Any = None

    def __post_init__(self) -> None:
        if self.client is None:
            from agents.anyplot.models import make_anthropic_client

            # No SDK retries: a 429 must reach `score_all`, which stops instead of retrying blindly.
            self.client = make_anthropic_client(self.project, self.location, max_retries=0)

    async def probe(self) -> None:
        """A 5-token request; SetupError when the model cannot be reached."""
        import anthropic

        try:
            await self.client.messages.create(
                model=self.model, max_tokens=5, messages=[{"role": "user", "content": "ok"}]
            )
        except anthropic.NotFoundError as exc:
            raise SetupError(f"{self.model} on {self.location}: not found or not enabled ({exc.status_code})") from None
        except anthropic.APIStatusError as exc:
            raise SetupError(f"{self.model} on {self.location}: HTTP {exc.status_code}") from None

    async def score(self, request: ScoreRequest) -> tuple[ScoreResult, dict[str, int], float]:
        """One scoring call, retried once when the answer is not a complete score."""
        content = [{"type": "text", "text": user_text(request)}, image_block(request.png)]
        messages: list[dict[str, Any]] = [{"role": "user", "content": content}]
        tokens: dict[str, int] = Counter()
        started = time.monotonic()
        last: str = "no answer"
        for _ in range(2):
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
                tools=[tool()],
                tool_choice={"type": "auto"},
                output_config={"effort": self.effort},
                messages=messages,
            )
            usage = response.usage
            cache_read = usage.cache_read_input_tokens or 0
            cache_write = usage.cache_creation_input_tokens or 0
            tokens["prompt"] += usage.input_tokens + cache_read + cache_write
            tokens["cached"] += cache_read
            tokens["cache_write"] += cache_write
            tokens["candidates"] += usage.output_tokens
            call = next((block for block in response.content if block.type == "tool_use"), None)
            if call is None:
                last = f"no {TOOL_NAME} call (stop reason {response.stop_reason})"
            else:
                try:
                    return parse_answer(dict(call.input)), dict(tokens), time.monotonic() - started
                except ScoreError as exc:
                    last = str(exc)
            # Same model, same conversation: the answer and the correction are appended, never edited.
            messages = [
                *messages,
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": _correction(call, last)},
            ]
        raise ScoringFailed(last, dict(tokens), time.monotonic() - started)


class ScoringFailed(ScoreError):
    """Two answers without a complete score; carries the billed tokens, so the spend still counts."""

    def __init__(self, message: str, tokens: dict[str, int], latency_s: float) -> None:
        super().__init__(message)
        self.tokens = tokens
        self.latency_s = latency_s


def _correction(call: Any, problem: str) -> list[dict[str, Any]]:
    text = f"That was not a complete score: {problem}. Call {TOOL_NAME} once with all 16 criteria."
    if call is None:
        return [{"type": "text", "text": text}]
    return [{"type": "tool_result", "tool_use_id": call.id, "is_error": True, "content": text}]


@dataclass
class Outcome:
    """What a scoring run did: the scored renders and why it stopped early, if it did."""

    scored: list[Scored]
    stopped: str | None = None


async def score_all(
    scorer: Scorer,
    jobs: Sequence[tuple[Target, ScoreRequest]],
    *,
    calls_per_minute: float = DEFAULT_CALLS_PER_MINUTE,
    budget_usd: float | None = None,
    echo: Any = print,
    sleep: Any = asyncio.sleep,
    clock: Any = time.monotonic,
) -> Outcome:
    """Score the jobs one at a time, starts spaced by `calls_per_minute`.

    A new base model's per-minute token quota can be small, so the calls are paced and a
    429 is never retried: it stops the run, and the message names the quota. The run also
    stops before a call that could take the list-price spend past `budget_usd` (the spend
    so far plus the costliest call so far).
    """
    import anthropic

    from agents.evals.pricing import call_cost

    interval = 60.0 / calls_per_minute if calls_per_minute > 0 else 0.0
    results: list[Scored] = []
    spent = costliest = 0.0
    next_start = clock()
    for index, (target, request) in enumerate(jobs, start=1):
        if budget_usd is not None and results and spent + costliest > budget_usd:
            return Outcome(results, f"budget: ${spent:.2f} spent, the next call could pass ${budget_usd:.2f}")
        wait = next_start - clock()
        if wait > 0:
            await sleep(wait)
        next_start = clock() + interval
        try:
            result, tokens, latency = await scorer.score(request)
            cost = call_cost(scorer.model, scorer.location, tokens)
            item = Scored(target, result, None, cost, latency, tokens)
        except anthropic.RateLimitError as exc:
            return Outcome(results, f"rate limited (429) at render {index}: {str(exc)[:300]}")
        except ScoringFailed as exc:  # billed calls without a score: priced, so the budget sees them
            cost = call_cost(scorer.model, scorer.location, exc.tokens)
            item = Scored(target, None, f"ScoringFailed: {str(exc)[:200]}", cost, exc.latency_s, exc.tokens)
        except Exception as exc:  # one failed call must not end the run; the type and message name it
            item = Scored(target, None, f"{type(exc).__name__}: {str(exc)[:200]}")
        results.append(item)
        spent += item.cost_usd
        costliest = max(costliest, item.cost_usd)
        shown = item.result.score if item.result else "error"
        echo(f"[{index}/{len(jobs)}] {target.run} {target.role}: {shown} (${spent:.2f})")
    return Outcome(results)


# --- The report ---------------------------------------------------------------------------------


def _stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    shares = {f"share_ge_{bar}": round(sum(value >= bar for value in values) / len(values), 3) for bar in THRESHOLDS}
    deciles = statistics.quantiles(ordered, n=10) if len(ordered) > 1 else [ordered[0]] * 9
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 1),
        "median": statistics.median(values),
        "p10": round(deciles[0], 1),
        "p90": round(deciles[-1], 1),
        "min": ordered[0],
        "max": ordered[-1],
        **shares,
    }


def summarize(scored: list[Scored], records: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """The numbers of the baseline: distributions, repair gain, deductions, clean-but-low runs, cost."""
    by_run: dict[str, dict[str, Scored]] = {}
    for item in scored:
        roles = ("first", "shipped") if item.target.role == "both" else (item.target.role,)
        for role in roles:
            by_run.setdefault(item.target.run, {})[role] = item
    ok = [item for item in scored if item.result]
    firsts = [runs["first"].result.score for runs in by_run.values() if "first" in runs and runs["first"].result]
    shipped = [runs["shipped"].result.score for runs in by_run.values() if "shipped" in runs and runs["shipped"].result]
    gains: list[int] = []
    for runs in by_run.values():
        first, last = runs.get("first"), runs.get("shipped")
        if first and last and first is not last and first.result and last.result:
            gains.append(last.result.score - first.result.score)
    lost: Counter[str] = Counter()
    named: Counter[str] = Counter()
    for item in ok:
        assert item.result is not None
        for criterion, points in item.result.points.items():
            lost[criterion] += SCORED[criterion] - points
        for line in item.result.defects:
            for criterion in line.split(" (", 1)[0].split(", "):
                named[criterion] += 1
    record_by_run = {f"{record['case_id']}#r{record.get('repeat', 1)}": record for record in records}
    clean_low = []
    for run, runs in sorted(by_run.items()):
        final = runs.get("shipped")
        record = record_by_run.get(run, {})
        if final and final.result and record.get("passed") and not record.get("advisory") and final.result.score < 80:
            clean_low.append({"run": run, "score": final.result.score, "defects": final.result.defects[:3]})
    ladder = {}
    # Runs with both scores only: a failed scoring call stays in `score_errors`, never in the ladder.
    both = [
        (runs["first"].result.score, runs["shipped"].result.score)
        for runs in by_run.values()
        if "first" in runs and "shipped" in runs and runs["first"].result and runs["shipped"].result
    ]
    for bar in THRESHOLDS:
        first_hit = sum(1 for first, _ in both if first >= bar)
        repair_hit = sum(1 for first, shipped in both if first < bar <= shipped)
        ladder[str(bar)] = {
            "runs": len(both),
            "first_try": first_hit,
            "after_repair_1": repair_hit,
            "would_need_advisor": len(both) - first_hit - repair_hit,
        }
    run_costs = [record["cost_usd"] for record in records if record.get("status") in ("ok", "needs_attention")]
    run_times = [record["e2e_s"] for record in records if isinstance(record.get("e2e_s"), int | float)]
    return {
        "scorer_model": model,
        "renders_scored": len(ok),
        "score_errors": [f"{item.target.run} {item.target.role}: {item.error}" for item in scored if item.error],
        "first": _stats(firsts),
        "shipped": _stats(shipped),
        "repair_gain": {
            "runs_repaired": len(gains),
            "improved": sum(gain > 0 for gain in gains),
            "same": sum(gain == 0 for gain in gains),
            "worse": sum(gain < 0 for gain in gains),
            "mean": round(statistics.fmean(gains), 1) if gains else None,
            "median": statistics.median(gains) if gains else None,
        },
        "points_lost": dict(lost.most_common()),
        "defect_lines_by_criterion": dict(named.most_common()),
        "silent_deductions": sum(len(item.result.silent) for item in ok if item.result),
        "clean_gates_low_score": clean_low,
        "ladder": ladder,
        "agent_cost_usd": {
            "median": round(statistics.median(run_costs), 4) if run_costs else None,
            "mean": round(statistics.fmean(run_costs), 4) if run_costs else None,
        },
        "agent_e2e_s": {
            "median": round(statistics.median(run_times), 1) if run_times else None,
            "p90": round(statistics.quantiles(run_times, n=10)[-1], 1) if len(run_times) > 1 else None,
        },
        "scoring_cost_usd": {
            "per_render": round(statistics.fmean([item.cost_usd for item in ok]), 4) if ok else None,
            # Every billed call, failed scores included; `per_render` stays the successful ones.
            "total": round(sum(item.cost_usd for item in scored), 4),
        },
        "scoring_latency_s": {"median": round(statistics.median([item.latency_s for item in ok]), 1) if ok else None},
    }


def markdown(summary: dict[str, Any]) -> str:
    """The summary as a short Markdown page."""

    def row(name: str, stats: dict[str, Any]) -> str:
        if not stats.get("n"):
            return f"| {name} | 0 | | | | | | |"
        return (
            f"| {name} | {stats['n']} | {stats['mean']} | {stats['median']} | {stats['p10']}–{stats['p90']} | "
            f"{stats['share_ge_90']:.0%} | {stats['share_ge_85']:.0%} | {stats['share_ge_80']:.0%} |"
        )

    gain = summary["repair_gain"]
    lines = [
        f"# Score baseline ({summary['scorer_model']})",
        "",
        "| Render | n | Mean | Median | p10–p90 | ≥ 90 | ≥ 85 | ≥ 80 |",
        "|---|---|---|---|---|---|---|---|",
        row("first", summary["first"]),
        row("shipped", summary["shipped"]),
        "",
        f"Repair 1 ran on {gain['runs_repaired']} runs: {gain['improved']} better, {gain['same']} same, "
        f"{gain['worse']} worse; mean gain {gain['mean']}, median {gain['median']}.",
        "",
        "| Threshold | Runs | First try | After repair 1 | Would need an advisor |",
        "|---|---|---|---|---|",
    ]
    for bar, ladder in summary["ladder"].items():
        lines.append(
            f"| {bar} | {ladder['runs']} | {ladder['first_try']} | {ladder['after_repair_1']} | "
            f"{ladder['would_need_advisor']} |"
        )
    lines += ["", "Points lost by criterion: " + ", ".join(f"{k} {v}" for k, v in summary["points_lost"].items())]
    lines.append(
        f"Agent run: median ${summary['agent_cost_usd']['median']}, median {summary['agent_e2e_s']['median']} s; "
        f"scoring: ${summary['scoring_cost_usd']['per_render']} and "
        f"{summary['scoring_latency_s']['median']} s per render."
    )
    if summary["clean_gates_low_score"]:
        lines += ["", "Clean gates, score below 80:"]
        lines += [f"- {item['run']}: {item['score']}" for item in summary["clean_gates_low_score"]]
    if summary["score_errors"]:
        lines += ["", f"Scoring errors: {len(summary['score_errors'])}"]
    return "\n".join(lines) + "\n"


# --- Main ---------------------------------------------------------------------------------------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m agents.evals.score", description=__doc__.splitlines()[0])
    parser.add_argument("report", type=Path, help="a matrix report (.json) of a run with --keep-attempts")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"scorer model (default {DEFAULT_MODEL})")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help=f"Vertex AI location (default {DEFAULT_LOCATION})")
    parser.add_argument("--effort", default=DEFAULT_EFFORT, help=f"output effort (default {DEFAULT_EFFORT})")
    parser.add_argument(
        "--transport",
        choices=("vertex", "claude-cli"),
        default="vertex",
        help="vertex (default), or claude-cli: score through the local Claude Code CLI on your subscription",
    )
    parser.add_argument(
        "--calls-per-minute",
        type=float,
        help=f"scoring calls started per minute (default {DEFAULT_CALLS_PER_MINUTE:g} on Vertex AI, "
        f"{CLI_CALLS_PER_MINUTE:g} on the CLI)",
    )
    parser.add_argument("--budget-usd", type=float, help="stop before the list-price spend could pass this")
    parser.add_argument(
        "--sample", type=positive_int, help="score this many runs (1 or more), spread evenly over the report's runs"
    )
    parser.add_argument("--estimate-only", action="store_true", help="print the job count and cost estimate, then stop")
    parser.add_argument(
        "--tag",
        type=lambda value: value if value.replace("-", "").isalnum() else parser.error(f"bad --tag {value!r}"),
        help="write <report>-scores-<tag>.{json,md}, for a second judge next to the first",
    )
    return parser.parse_args(argv)


def positive_int(value: str) -> int:
    """An argparse type: a whole number of at least 1 (`--sample 0` would otherwise read as no sample)."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a whole number, got {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def spread(items: list[Any], count: int) -> list[Any]:
    """`count` items spread evenly over `items`, keeping their order (all of them when there are fewer)."""
    if count >= len(items):
        return list(items)
    step = len(items) / count
    return [items[int(index * step)] for index in range(count)]


def main(argv: list[str] | None = None) -> int:
    from agents.evals.cases import load_cases

    args = parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read {args.report}: {exc}", file=sys.stderr)
        return 2
    records = [record for record in report.get("runs", []) if record.get("attempt_renders")]
    if not records:
        print("the report holds no run with attempt_renders; run the matrix with --keep-attempts", file=sys.stderr)
        return 2
    if args.sample is not None:
        records = spread(records, args.sample)
    cases = {case.case_id: case for case in load_cases()}
    jobs: list[tuple[Target, ScoreRequest]] = []
    for record in records:
        case = cases.get(record["case_id"])
        bindings = [binding.model_dump() for binding in case.bindings] if case and case.bindings else None
        for target in targets_of(record, args.report.parent):
            if target.png.is_file():
                jobs.append((target, request_for(target, bindings)))
    estimate = estimate_usd(args.model, args.location, len(jobs))
    print(f"{len(jobs)} renders of {len(records)} runs; estimated ${estimate:.2f} at list price on {args.model}")
    if args.estimate_only:
        return 0
    client = None
    calls_per_minute = args.calls_per_minute or DEFAULT_CALLS_PER_MINUTE
    if args.transport == "claude-cli":
        from agents.anyplot.cli_transport import ClaudeCliClient

        # No fallback: a scoring call the CLI cannot answer must fail, never reach Vertex AI.
        client = ClaudeCliClient()
        calls_per_minute = args.calls_per_minute or CLI_CALLS_PER_MINUTE
    scorer = Scorer(args.model, args.location, args.effort, client=client)
    try:
        asyncio.run(scorer.probe())
    except SetupError as exc:
        print(f"setup: {exc}", file=sys.stderr)
        return 2
    outcome = asyncio.run(score_all(scorer, jobs, calls_per_minute=calls_per_minute, budget_usd=args.budget_usd))
    scored = outcome.scored
    summary = summarize(scored, records, args.model)
    summary["stopped"] = outcome.stopped
    out = {
        "report": args.report.name,
        "summary": summary,
        "renders": [
            {
                "run": item.target.run,
                "role": item.target.role,
                "png": str(item.target.png.relative_to(args.report.parent)),
            }
            | ({"result": item.result.as_dict()} if item.result else {"error": item.error})
            | {"cost_usd": round(item.cost_usd, 5), "latency_s": round(item.latency_s, 1), "tokens": item.tokens}
            for item in scored
        ],
    }
    stem = args.report.with_suffix("")
    suffix = f"-scores-{args.tag}" if args.tag else "-scores"
    stem.with_name(stem.name + suffix + ".json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    stem.with_name(stem.name + suffix + ".md").write_text(markdown(summary), encoding="utf-8")
    print(markdown(summary))
    if outcome.stopped:
        print(f"stopped early: {outcome.stopped}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
