"""The regression matrix: every selected eval case through the real `/v1` flow, in process.

Run it from the repository root. It calls the configured models, so it spends tokens:

    uv run --extra agents python -m agents.evals.matrix --cases smoke --renderer remote --render-url URL
    uv run --extra agents python -m agents.evals.matrix --cases full --provider gemini --renderer remote ...

Each case opens a session on `agents.main:app` through httpx's `ASGITransport`
(`POST /v1/sessions` with the catalogue snapshot, `/dataset` with `data.csv`, `PUT
/bindings` with the case's bindings, then `POST /messages {"action": "create_plot"}`,
and a free-text turn when the case has a `change_request.txt`), so the run takes the
same path as a user's: the ScopeGuard, Budget and ToolSafety plugins, the run queue,
the data judge, the pipeline and its gates. The models come from the settings, the
render backend from `AGENT_RENDERER`: `remote` renders on a deployed renderer, `local`
in Docker, `fake` returns fixture PNGs (a dry run of everything but the render; the
models are still real). Per run it records the status and reason, attempts, gate
failures by gate, validator rejections, edit-apply failures, the reviewer's verdict,
LLM calls, tokens by kind, `model_version`, the cost at list price
(`agents/evals/pricing.py`), the time to the first event, the end-to-end time, and
the render times, read from the stream and from the content-free attribution log
lines of that run's request ids. Since report schema 2 it also records where the run
stopped (`stage`, the pipeline's `Stage`, and `stages` per attempt), the shipped and
the reviewed attempt, an `attempt_log` (per attempt: the adapter's outcome, finish
reason, output tokens and plan shape, the check with its edit-failure kinds, the
render gates and the review verdict), every model call's finish reason and tokens
(`calls`, counted per agent kind in `finish_reasons`), and the edit-failure kinds.

Outputs, under `--out` (default `agents/evals/reports/`, git-ignored):

* `<date>-<model>.json`, the report (`-2`, `-3`, ... when the name is taken), and
  `<date>-<model>.md`, its Markdown summary;
* `renders/<case-id>-r<repeat>.png`, the shipped PNG of every run that shipped one;
* `gallery.html`, a blind review page with a random sample of `--gallery-size` (30)
  renders that passed the gates and an accept and reject pair each, exported as JSON
  with one button; `gallery-all.html` lists every run. Both are rewritten by the next
  run in the same directory, so give each run its own `--out` when you keep its
  gallery. `python -m agents.evals.report blind` merges two runs into one gallery that
  hides which arm made a render.

**Before the first case** the harness renders the catalogue file of the first case of
each library in the selection through the configured backend (no model call). A
backend that cannot render (unreachable, the caller refused, a library missing in the
image) ends the run with exit code 2 before any token is spent. **During the run** a
case whose pipeline ended in `RendererUnavailable` (the `error` field of its
`pipeline_result` line), or three runs in a row that ended in an error, stop the run
with exit code 4, so an outage never turns the rest of the matrix into `failed (error)`
runs. `--gcloud-token` mints the renderer's ID token with `gcloud auth
print-identity-token` and mints a new one whenever it is within 10 minutes of its
one-hour expiry, so a full run outlasts a token.

With a baseline (`--baseline FILE`, by default `agents/evals/baselines/<pinned model>.json`
when it exists) the run prints the diff table over the cases both reports hold: pass
rate, accept-match rate, cost per successful plot, latency percentiles and every case
that flipped. `--save-baseline` writes the report to
`agents/evals/baselines/<model>.json`; it refuses a run that stopped early, holds
promoted cases, or has any run that ended in an error.

Exit codes: 0 done; 1 the run did not hold: its pass rate on the shared cases fell
below the baseline's minus `--tolerance` (5 percentage points by default), or a run
crashed in the harness; 2 a setup error (settings, renderer, preflight, price, cases);
3 stopped early by `--budget-usd`; 4 stopped by an outage (see above). Ctrl-C writes
the partial report before it stops.

For its own process the harness lifts the run queue's start rate
(`AGENT_RUNS_PER_MINUTE`, `--runs-per-minute`, 60) and the service-wide daily token
budget, and gives every case and repeat its own user id, so the per-user daily
budgets never trip; the per-request limits (12 LLM calls, 80k tokens, the deadlines)
stay at their production values. It sets `ENVIRONMENT=development` for the `remote`
and `local` renderers unless it runs on Cloud Run (`K_SERVICE`), because a developer's
renderer token is accepted only in development, and defaults it to `development`
otherwise; it never loads a `.env` file, and leaves the caller check out, because the
requests never leave the process. It turns the footer strip off (`AGENT_WATERMARK=false`)
unless the environment already sets the variable, so `renders/` and the galleries hold
the raw renders the gates and the reviewer judged, comparable with the committed
baselines and with runs made before the strip existed.
"""

import argparse
import asyncio
import base64
import binascii
import codecs
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import secrets
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from agents.evals.pricing import LOCATION_SURCHARGE, TOKEN_KINDS, UnknownPrice, call_cost, judge_cost, price_of
from agents.evals.report import (
    GALLERY_SIZE,
    REPORT_SCHEMA,
    SHIPPED,
    SUPPORTED_SCHEMAS,
    Diff,
    compare,
    diff_markdown,
    gallery_all_html,
    gallery_html,
    summarize,
    summary_markdown,
)


if TYPE_CHECKING:  # importing agents.anyplot builds the agents, so the runtime imports wait for `configure`
    from agents.anyplot.services import Services
    from agents.anyplot.settings import AgentSettings
    from agents.evals.cases import EvalCase
    from agents.main import Runtime


EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[1]
DEFAULT_OUT = EVALS_DIR / "reports"
BASELINES_DIR = EVALS_DIR / "baselines"
RENDERERS: tuple[str, ...] = ("remote", "local", "fake")
PROVIDER_DEFAULTS: dict[str, tuple[str, str]] = {
    "anthropic-vertex": ("claude-haiku-5-5", "claude-haiku-5-5"),
    "gemini": ("gemini-3.8-flash", "gemini-3.5-flash-lite"),
}
MODEL_PROVIDERS: dict[str, str] = {"claude-": "anthropic-vertex", "gemini-": "gemini"}
DEFAULT_TOLERANCE = 0.05
EVAL_RUNS_PER_MINUTE = 60
EVAL_GLOBAL_DAILY_TOKENS = 1_000_000_000
ATTRIBUTION_LOGGER = "anyplot.agents.attribution"
MODEL_TOKEN_KINDS: tuple[str, ...] = ("prompt", "candidates", "thoughts", "cached", "cache_write", "tool_use_prompt")
EXIT_OK, EXIT_REGRESSION, EXIT_SETUP, EXIT_STOPPED, EXIT_OUTAGE = 0, 1, 2, 3, 4
RENDERER_OUTAGE = "RendererUnavailable"
REFUSAL_STATUSES = frozenset({403, 409, 413, 422})
"""HTTP statuses with which the service refuses a request on its merits (the data, the bindings), the case's own outcome.
Any other failure (a 5xx, a judge outage) is the service's and counts as an error (`is_error`)."""
ERROR_STATUSES = frozenset({"harness_error", "error"})
"""The pipeline's `error` class that means the renderer is down, not that the model failed."""
MAX_ERRORS_IN_A_ROW = 3
"""Runs in a row that ended in an error (pipeline or harness) before the matrix stops as an outage."""
DEVELOPER_RENDERERS: tuple[str, ...] = ("remote", "local")
GCLOUD_TOKEN_COMMAND: tuple[str, ...] = ("gcloud", "auth", "print-identity-token")
TOKEN_REFRESH_MARGIN_S = 600.0
"""`--gcloud-token` mints a new token when the current one expires within this many seconds."""
PREFLIGHT_DATA = "x\n1\n"
"""The preflight renders the normalised catalogue file, which makes its own data; this only fills the slot."""

logger = logging.getLogger("anyplot.evals")


class SetupError(Exception):
    """A harness invocation that cannot run: its message says what to change."""


# --- Configuration ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.matrix",
        description="Run eval cases through the agent network's /v1 flow and report against a baseline.",
    )
    parser.add_argument("--provider", choices=sorted(PROVIDER_DEFAULTS), help="model family (default: the settings)")
    parser.add_argument("--model", help="model of every agent; the provider's default when only --provider is given")
    parser.add_argument("--judge-model", help="model of the scope and dataset judge; the provider's default")
    parser.add_argument("--location", choices=sorted(LOCATION_SURCHARGE), help="Vertex AI location (default eu)")
    parser.add_argument(
        "--renderer",
        choices=RENDERERS,
        help="render backend (default: AGENT_RENDERER when it is one of these, else remote)",
    )
    parser.add_argument("--render-url", help="the deployed renderer's URL for --renderer remote (AGENT_RENDER_URL)")
    parser.add_argument(
        "--gcloud-token",
        action="store_true",
        help="mint AGENT_RENDER_TOKEN with `gcloud auth print-identity-token` and renew it before it expires",
    )
    parser.add_argument("--no-preflight", action="store_true", help="skip the model-free preflight render")
    parser.add_argument("--cases", default="smoke", help="smoke, full, or comma-separated globs over case ids")
    parser.add_argument("--repeats", type=int, default=1, help="runs per case (default 1)")
    parser.add_argument(
        "--budget-usd",
        type=float,
        help="stop before a case that could take the estimated list-price cost past this (spent + costliest case)",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default agents/evals/reports)")
    parser.add_argument("--baseline", type=Path, help="baseline report (default: baselines/<pinned model>.json)")
    parser.add_argument("--no-baseline", action="store_true", help="do not compare with any baseline")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="allowed pass-rate drop (0.05)")
    parser.add_argument("--save-baseline", action="store_true", help="write the report as baselines/<model>.json")
    parser.add_argument("--seed", type=int, default=0, help="seed of the gallery sample (default 0)")
    parser.add_argument("--gallery-size", type=int, default=GALLERY_SIZE, help="renders in the gallery (default 30)")
    parser.add_argument(
        "--runs-per-minute", type=int, default=EVAL_RUNS_PER_MINUTE, help="run queue start rate for this process"
    )
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if args.budget_usd is not None and args.budget_usd <= 0:
        parser.error("--budget-usd must be positive")
    if not 0 <= args.tolerance < 1:
        parser.error("--tolerance is a fraction between 0 and 1")
    if args.gallery_size < 0 or args.runs_per_minute < 1:
        parser.error("--gallery-size must be 0 or more and --runs-per-minute at least 1")
    return args


def configure(args: argparse.Namespace, environ: MutableMapping[str, str]) -> None:
    """Write the flags into the `AGENT_*` environment the settings read; runs before any `agents.anyplot` import.

    `--provider` alone selects that provider's default model and judge; `--model` alone
    implies its provider. The environment's own `AGENT_*` values stay for everything
    no flag names. With the `remote` or `local` renderer the process runs as
    `ENVIRONMENT=development` (outside Cloud Run), whatever the shell exported: only
    development accepts a developer's renderer token and the `local` backend. The footer
    strip is off unless the environment sets `AGENT_WATERMARK`, so the saved renders stay
    the raw ones the baselines were made from.
    """
    environ["PYTHON_DOTENV_DISABLED"] = "1"
    environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    environ.pop("AGENT_DEV_FIXTURE", None)
    environ.setdefault("AGENT_WATERMARK", "false")
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
    configured = environ.get("AGENT_RENDERER")
    renderer = args.renderer or (configured if configured in RENDERERS else "remote")
    environ["AGENT_RENDERER"] = renderer
    if renderer in DEVELOPER_RENDERERS and "K_SERVICE" not in environ:
        environ["ENVIRONMENT"] = "development"
    else:
        environ.setdefault("ENVIRONMENT", "development")
    if args.render_url:
        if renderer != "remote":
            raise SetupError("--render-url needs --renderer remote")
        environ["AGENT_RENDER_URL"] = args.render_url
    if args.gcloud_token and renderer != "remote":
        raise SetupError("--gcloud-token needs --renderer remote")
    environ["AGENT_RUNS_PER_MINUTE"] = str(args.runs_per_minute)
    environ["AGENT_GLOBAL_DAILY_TOKEN_BUDGET"] = str(EVAL_GLOBAL_DAILY_TOKENS)


@dataclass
class MatrixConfig:
    """What one matrix run does besides running the cases."""

    cases: str = "smoke"
    repeats: int = 1
    budget_usd: float | None = None
    out: Path = DEFAULT_OUT
    baseline: dict[str, Any] | None = None
    baseline_path: Path | None = None
    tolerance: float = DEFAULT_TOLERANCE
    seed: int = 0
    gallery_size: int = GALLERY_SIZE
    save_baseline: bool = False
    baselines_dir: Path = BASELINES_DIR
    preflight: bool = True
    render_token: "RenderToken | None" = None
    argv: list[str] = field(default_factory=list)


# --- The renderer: token and preflight -------------------------------------------------------


def token_expiry(token: str) -> float | None:
    """The `exp` claim of a JWT, read without verifying it; None when it has none."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    except (ValueError, binascii.Error):
        return None
    expiry = claims.get("exp") if isinstance(claims, dict) else None
    return float(expiry) if isinstance(expiry, int | float) and not isinstance(expiry, bool) else None


def gcloud_token() -> str:
    """A fresh ID token of your gcloud account (`gcloud auth print-identity-token`); never printed or logged."""
    try:
        done = subprocess.run(list(GCLOUD_TOKEN_COMMAND), capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SetupError(f"`gcloud auth print-identity-token` did not run ({type(exc).__name__})") from None
    token = done.stdout.strip()
    if done.returncode != 0 or token.count(".") != 2:
        raise SetupError(
            f"`gcloud auth print-identity-token` failed (exit {done.returncode}); run `gcloud auth login` first"
        )
    return token


def token_note(environ: MutableMapping[str, str], clock: Callable[[], float] = time.time) -> str | None:
    """A warning when a static `AGENT_RENDER_TOKEN` will expire during a long run."""
    token = environ.get("AGENT_RENDER_TOKEN")
    expiry = token_expiry(token) if token else None
    if expiry is None:
        return None
    minutes = max(0, int((expiry - clock()) // 60))
    return (
        f"AGENT_RENDER_TOKEN expires in {minutes} min; a run that outlasts it stops with exit code 4. "
        "Pass --gcloud-token to renew it during the run."
    )


@dataclass
class RenderToken:
    """Keeps `AGENT_RENDER_TOKEN` fresh for a run that outlasts the token's hour (`--gcloud-token`).

    Before each case `renew` checks the token's `exp`; within `margin_s` of it, it mints
    a new one, rebuilds the settings and swaps the backend inside the one
    `SerialRenderer`, so the render semaphore stays the same object.
    """

    environ: MutableMapping[str, str]
    mint: Callable[[], str] = gcloud_token
    clock: Callable[[], float] = time.time
    margin_s: float = TOKEN_REFRESH_MARGIN_S
    renewed: int = 0

    def due(self) -> bool:
        token = self.environ.get("AGENT_RENDER_TOKEN")
        expiry = token_expiry(token) if token else None
        return expiry is None or expiry - self.clock() < self.margin_s

    async def renew(self, services: "Services") -> bool:
        """Mint and install a new token when the current one is due; True when it did."""
        if not self.due():
            return False
        from agents.anyplot.settings import get_settings

        self.environ["AGENT_RENDER_TOKEN"] = await asyncio.to_thread(self.mint)
        get_settings.cache_clear()
        serial = services.backend
        old, serial.backend = serial.backend, services.backend_factory()
        close = getattr(old, "aclose", None)
        if old is not serial.backend and close is not None:
            await close()
        self.renewed += 1
        return True


async def preflight(cases: list["EvalCase"], services: "Services", echo: Callable[[str], None]) -> None:
    """Render the catalogue file of each library's first case once, before any model call; SetupError if it fails.

    The job is the normalised original (it makes its own data) in the light theme,
    through `services.backend`, the same path as the pipeline's renders. It proves the
    backend renders at all: reachable, the caller accepted, the library in the image.
    """
    from agents.anyplot.code.normalise import normalise
    from agents.anyplot.render import PythonRuntime
    from agents.anyplot.render.contract import RendererUnavailable, RenderJob
    from agents.anyplot.render.gates import error_summary
    from agents.anyplot.settings import get_settings

    firsts: dict[str, EvalCase] = {}
    for case in cases:
        firsts.setdefault(case.library, case)
    timeout = float(get_settings().render_timeout_s)
    for library, case in firsts.items():
        job = RenderJob(
            job_id=secrets.token_hex(8),
            language=PythonRuntime.language,
            library=library,
            source=normalise(case.snapshot().code, library=library),
            data_csv=PREFLIGHT_DATA,
            themes=("light",),
            timeout_s=timeout,
        )
        started = time.monotonic()
        try:
            result = await services.backend.render(job)
        except RendererUnavailable as exc:
            raise SetupError(f"preflight render of {case.spec_id} ({library}): {exc}") from None
        except Exception as exc:
            raise SetupError(f"preflight render of {case.spec_id} ({library}) failed: {type(exc).__name__}") from None
        output = result.outputs.get("light")
        if output is None or output.exit_code != 0 or not output.png:
            why = "no output" if output is None else f"exit code {output.exit_code}"
            if output is not None and output.timed_out:
                why += ", timed out"
            if output is not None and output.stderr_tail:
                why += f", {error_summary(output.stderr_tail)}"
            raise SetupError(f"preflight render of {case.spec_id} ({library}) failed: {why}")
        echo(f"preflight: {case.spec_id} ({library}) rendered in {time.monotonic() - started:.1f} s")


# --- Observation -----------------------------------------------------------------------------


class AttributionCollector(logging.Handler):
    """Collects the attribution log's JSON lines by request id (the harness sets one per request)."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.lines: dict[str, list[dict[str, Any]]] = {}

    def emit(self, record: logging.LogRecord) -> None:
        try:
            data = json.loads(record.getMessage())
        except (TypeError, ValueError):
            return
        if isinstance(data, dict) and isinstance(data.get("request_id"), str):
            self.lines.setdefault(data["request_id"], []).append(data)

    def take(self, request_id: str) -> list[dict[str, Any]]:
        return self.lines.pop(request_id, [])


class TimedApp:
    """An ASGI wrapper that timestamps every response body chunk.

    httpx's `ASGITransport` hands the client the whole body at once, so the client
    cannot see when each SSE event left the service; the wrapper can. The harness runs
    one request at a time and clears `chunks` before each streamed turn.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.chunks: list[tuple[float, bytes]] = []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def timed(message: Message) -> None:
            if message["type"] == "http.response.body" and message.get("body"):
                self.chunks.append((time.monotonic(), message["body"]))
            await send(message)

        await self.app(scope, receive, timed)


Event = tuple[float, str, dict[str, Any]]


def parse_events(chunks: list[tuple[float, bytes]], started: float) -> list[Event]:
    """The SSE events of a stream as `(seconds since started, name, data)`, each timed by the chunk that ended it."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    events: list[Event] = []
    buffer = ""
    for at, body in chunks:
        buffer += decoder.decode(body)
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            name, data = None, None
            for line in block.splitlines():
                if line.startswith("event: "):
                    name = line[len("event: ") :]
                elif line.startswith("data: "):
                    data = line[len("data: ") :]
            if name is None or data is None:
                continue
            try:
                payload = json.loads(data)
            except ValueError:
                payload = {}
            events.append((at - started, name, payload if isinstance(payload, dict) else {}))
    return events


# --- One case --------------------------------------------------------------------------------


def base_record(case: "EvalCase", repeat: int) -> dict[str, Any]:
    """A run record before the run: every field the report reads, with its empty value."""
    return {
        "case_id": case.case_id,
        "repeat": repeat,
        "spec_id": case.spec_id,
        "library": case.library,
        "perturbation": case.perturbation,
        "expected": case.expected,
        "tags": list(case.tags),
        "origin": case.origin,
        "status": "harness_error",
        "reason": None,
        "attempts": 0,
        "passed": False,
        "accepted": False,
        "accept_match": None,
        "padded": False,
        "adaptation": [],
        "advisory": [],
        "residual_defects": [],
        "gate_failures": {},
        "validator_rejections": {},
        "adapter_outcomes": {},
        "edit_apply_failures": 0,
        "reviewer": {"verdict": None, "defects": []},
        "llm_calls": 0,
        "llm_calls_by_agent": {},
        "tokens": dict.fromkeys(TOKEN_KINDS, 0),
        "model_versions": [],
        "cost_usd": 0.0,
        "ttfe_s": None,
        "e2e_s": None,
        "queue_s": None,
        "render_s": [],
        "render_wall_s": [],
        "turns": 0,
        "png": None,
        "error": None,
        "pipeline_error": None,
        # Schema 2: where the run stopped, attempt by attempt and call by call (all content-free).
        "stage": None,
        "stages": [],
        "shipped_attempt": None,
        "reviewed_attempt": None,
        "attempt_log": [],
        "calls": [],
        "finish_reasons": {},
        "edit_failure_kinds": {},
    }


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def _number(value: Any) -> float:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else 0.0


def finish_reason(value: Any) -> str:
    """A logged finish reason by its enum name; older lines wrote `FinishReason.MAX_TOKENS`, a missing one is `unknown`."""
    text = str(value).removeprefix("FinishReason.") if value else ""
    return text or "unknown"


def agent_kind(name: Any) -> str:
    """The kind of a logged agent name: `root`, `adapter` (any library) or `reviewer`."""
    text = str(name)
    if text == "anyplot":
        return "root"
    return "adapter" if text.startswith("adapter_") else text


def _attempt_entry(record: dict[str, Any], attempt: int) -> dict[str, Any]:
    """The `attempt_log` entry of the current turn's attempt, appended on first use (attempts restart per turn)."""
    turn = record["turns"]
    log: list[dict[str, Any]] = record["attempt_log"]
    for entry in log:
        if entry["turn"] == turn and entry["attempt"] == attempt:
            return entry
    entry = {"turn": turn, "attempt": attempt}
    log.append(entry)
    return entry


def _book_attempt(record: dict[str, Any], hook: str, line: dict[str, Any]) -> None:
    """Fold one `pipeline_*` line into its attempt's entry: the per-attempt view the counters lose."""
    entry = _attempt_entry(record, _int(line.get("attempt")))
    if hook == "pipeline_adapt":
        entry["adapter"] = str(line.get("outcome"))
        entry["finish_reason"] = finish_reason(line.get("finish_reason"))
        entry["candidates"], entry["thoughts"] = _int(line.get("candidates")), _int(line.get("thoughts"))
        if line.get("outcome") == "plan":
            entry["edits"], entry["full_code"] = _int(line.get("edits")), bool(line.get("full_code"))
    elif hook == "pipeline_check":
        entry["check"] = str(line.get("outcome"))
        entry["edit_failure_kinds"] = dict(line.get("edit_failure_kinds") or {})
        entry["validator"] = [str(rule) for rule in line.get("validator") or []]
        entry["adaptation"] = [str(rule) for rule in line.get("adaptation") or []]
    elif hook == "pipeline_render":
        entry["render"] = {
            "passed": bool(line.get("passed")),
            "canvas_ok": bool(line.get("canvas_ok")),
            "gates": [str(gate) for gate in line.get("gates") or []],
        }
    elif hook == "pipeline_review":
        entry["review"] = str(line.get("verdict"))
        entry["review_finish_reason"] = finish_reason(line.get("finish_reason"))


def _book_stages(record: dict[str, Any], line: dict[str, Any]) -> None:
    """The run's stage, the stage of each attempt of this turn, and the shipped and reviewed attempts."""
    stages = [str(stage) for stage in line.get("stages") or []]
    record["stage"] = str(line["stage"]) if line.get("stage") else None
    record["stages"] = stages
    record["shipped_attempt"] = _int(line.get("shipped_attempt")) or None
    record["reviewed_attempt"] = _int(line.get("reviewed_attempt")) or None
    for number, stage in enumerate(stages, start=1):
        _attempt_entry(record, number)["stage"] = stage


def book_attribution(record: dict[str, Any], lines: list[dict[str, Any]], settings: "AgentSettings") -> None:
    """Add one request's attribution lines to the run record: calls, tokens, cost, and the pipeline's findings."""
    gates: Counter[str] = Counter(record["gate_failures"])
    validator: Counter[str] = Counter(record["validator_rejections"])
    adapter: Counter[str] = Counter(record["adapter_outcomes"])
    agents: Counter[str] = Counter(record["llm_calls_by_agent"])
    kinds: Counter[str] = Counter(record["edit_failure_kinds"])
    finishes = {kind: Counter[str](reasons) for kind, reasons in record["finish_reasons"].items()}
    versions = set(record["model_versions"])
    tokens = record["tokens"]
    for line in lines:
        hook = line.get("hook")
        if hook == "model":
            record["llm_calls"] += 1
            agents[str(line.get("agent"))] += 1
            for kind in MODEL_TOKEN_KINDS:
                tokens[kind] += _int(line.get(kind))
            if line.get("model_version"):
                versions.add(str(line["model_version"]))
            record["cost_usd"] += call_cost(settings.model, settings.location, line)
            reason = finish_reason(line.get("finish_reason"))
            finishes.setdefault(agent_kind(line.get("agent")), Counter())[reason] += 1
            record["calls"].append(
                {
                    "turn": record["turns"],
                    "agent": str(line.get("agent")),
                    "finish_reason": reason,
                    **{kind: _int(line.get(kind)) for kind in ("prompt", "cached", "candidates", "thoughts")},
                }
            )
        elif hook in ("data_judge", "scope_guard"):
            judge_in, judge_out = _int(line.get("judge_input")), _int(line.get("judge_output"))
            if not judge_in and not judge_out:
                judge_in = _int(line.get("judge_tokens"))  # a line without the split prices everything as input
            tokens["judge_input"] += judge_in
            tokens["judge_output"] += judge_out
            record["cost_usd"] += judge_cost(settings.judge_model, settings.location, judge_in, judge_out)
        elif hook == "pipeline_adapt":
            adapter[str(line.get("outcome"))] += 1
            _book_attempt(record, hook, line)
        elif hook == "pipeline_check":
            record["edit_apply_failures"] += _int(line.get("edit_failures"))
            kinds.update({str(kind): _int(count) for kind, count in (line.get("edit_failure_kinds") or {}).items()})
            validator.update(str(rule) for rule in line.get("validator") or [])
            if line.get("outcome") == "loader_failed":
                validator["loader"] += 1
            _book_attempt(record, hook, line)
        elif hook == "pipeline_render":
            gates.update(str(gate) for gate in line.get("gates") or [])
            record["render_s"].append(_number(line.get("render_s")))
            wall = line.get("wall_s")
            if isinstance(wall, dict):
                record["render_wall_s"] += [_number(value) for value in wall.values()]
            _book_attempt(record, hook, line)
        elif hook == "pipeline_review":
            record["reviewer"] = {"verdict": line.get("verdict"), "defects": list(line.get("defects") or [])}
            _book_attempt(record, hook, line)
        elif hook == "pipeline_result":
            record["padded"] = bool(line.get("padded"))
            record["adaptation"] = [str(rule) for rule in line.get("adaptation") or []]
            record["advisory"] = [str(gate) for gate in line.get("advisory") or []]
            if line.get("error"):
                record["pipeline_error"] = str(line["error"])
            _book_stages(record, line)
        elif hook == "queue":
            record["queue_s"] = (record["queue_s"] or 0.0) + _number(line.get("waited_s"))
    record["gate_failures"] = dict(sorted(gates.items()))
    record["validator_rejections"] = dict(sorted(validator.items()))
    record["adapter_outcomes"] = dict(sorted(adapter.items()))
    record["llm_calls_by_agent"] = dict(sorted(agents.items()))
    record["edit_failure_kinds"] = dict(sorted((kind, count) for kind, count in kinds.items() if count))
    record["finish_reasons"] = {kind: dict(sorted(reasons.items())) for kind, reasons in sorted(finishes.items())}
    record["model_versions"] = sorted(versions)


@dataclass
class Turn:
    """One `/messages` request: its HTTP status, the error detail, and the timed events."""

    status_code: int
    detail: str | None
    events: list[Event]


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"http {response.status_code}"
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) else f"http {response.status_code}"


def book_turn(record: dict[str, Any], turn: Turn) -> dict[str, Any] | None:
    """Read one turn's stream into the record; the `plot` event's data, if there was one."""
    record["turns"] += 1
    if turn.status_code != 200:
        record["status"], record["reason"] = "error", turn.detail
        return None
    plot = refusal = error = None
    first = done = last = None
    for at, name, data in turn.events:
        last = at
        if first is None and name != "ready" and not (name == "status" and data.get("step") == "queued"):
            first = at
        if name == "plot":
            plot = data
        elif name == "refusal":
            refusal = data
        elif name == "error":
            error = data
        elif name == "done":
            done = at
    if record["turns"] == 1:
        record["ttfe_s"] = first
    elapsed = done if done is not None else last
    if elapsed is not None:
        record["e2e_s"] = (record["e2e_s"] or 0.0) + elapsed
    if plot is not None:
        record["status"] = plot.get("status")
        record["reason"] = plot.get("reason")
        record["attempts"] = int(plot.get("attempts") or 0)
        record["residual_defects"] = list(plot.get("residual_defects") or [])
        if error is not None:
            record["error"] = error.get("code")
    elif refusal is not None:
        record["status"], record["reason"] = "refused", refusal.get("code")
    elif error is not None:
        record["status"], record["reason"] = "error", error.get("code")
    else:
        record["status"], record["reason"] = "error", "no_result"
    return plot


def finish_record(record: dict[str, Any]) -> None:
    """Derive pass, the harness outcome and the accept match from the booked fields (see `report.py`)."""
    if record["status"] == "harness_error":
        return
    record["accepted"] = record["status"] == "ok"
    record["passed"] = record["status"] in SHIPPED and not record["padded"] and not record["adaptation"]
    expected = record["expected"]
    record["accept_match"] = None if expected == "unknown" else record["accepted"] == (expected == "accepted")


@dataclass
class CaseRunner:
    """Runs cases one at a time against the in-process app."""

    client: httpx.AsyncClient
    timed: TimedApp
    collector: AttributionCollector
    settings: "AgentSettings"
    renders_dir: Path

    async def run(self, case: "EvalCase", repeat: int) -> dict[str, Any]:
        """One case and repeat, from opening the session to deleting it; never raises for a broken case."""
        record = base_record(case, repeat)
        digest = hashlib.sha256(f"{case.case_id}#{repeat}".encode()).hexdigest()
        user = f"eval_{digest[:12]}_{repeat}"
        tag = f"ev-{digest[:10]}-{repeat}"
        opened: list[str] = []

        def headers(step: str) -> dict[str, str]:
            return {"X-Anyplot-User": user, "X-Request-Id": f"{tag}-{step}"}

        try:
            await self._steps(record, case, repeat, user, headers, opened)
        except Exception as exc:  # one broken case must not end the matrix; the type is enough to find it
            logger.warning("case %s failed in the harness: %s", case.case_id, type(exc).__name__)
            record["status"], record["error"] = "harness_error", type(exc).__name__
        finally:
            for sid in opened:
                try:
                    await self.client.delete(f"/v1/sessions/{sid}", headers=headers("x"))
                except Exception as exc:
                    logger.warning("deleting the session of %s failed: %s", case.case_id, type(exc).__name__)
            for step in ("s", "d", "b", "m1", "m2", "a", "x"):
                self.collector.take(f"{tag}-{step}")
        finish_record(record)
        return record

    async def _steps(
        self,
        record: dict[str, Any],
        case: "EvalCase",
        repeat: int,
        user: str,
        headers: Callable[[str], dict[str, str]],
        opened: list[str],
    ) -> None:
        sid = await self._open(record, case, user, headers("s"))
        if sid is None:
            return
        opened.append(sid)
        if not await self._dataset(record, case, sid, headers("d")):
            return
        if not await self._bindings(record, case, sid, headers("b")):
            return
        plot = await self._turn(record, sid, {"action": "create_plot"}, headers("m1"))
        if case.change_request and record["status"] in SHIPPED:
            plot = await self._turn(record, sid, {"text": case.change_request}, headers("m2"))
        if plot is not None and record["status"] in SHIPPED:
            await self._save_png(record, case, repeat, sid, plot, headers("a"))

    async def _open(self, record: dict[str, Any], case: "EvalCase", user: str, headers: dict[str, str]) -> str | None:
        body = {
            "user": user,
            "spec_id": case.spec_id,
            "library": case.library,
            "locale": case.locale,
            "snapshot": case.snapshot().model_dump(),
        }
        response = await self.client.post("/v1/sessions", headers=headers, json=body)
        if response.status_code != 200:
            detail = _detail(response)
            record["status"] = "not_eligible" if detail == "not_eligible" else "error"
            record["reason"] = detail
            return None
        session_id: str = response.json()["session_id"]
        return session_id

    async def _dataset(self, record: dict[str, Any], case: "EvalCase", sid: str, headers: dict[str, str]) -> bool:
        response = await self.client.post(f"/v1/sessions/{sid}/dataset", headers=headers, json={"text": case.data_text})
        book_attribution(record, self.collector.take(headers["X-Request-Id"]), self.settings)
        if response.status_code != 200:
            # A refusal of the data (the judge's `403 data_refused`, `413 too_long`,
            # `422 unparseable`) is the case's outcome; anything else, such as the
            # judge's own `503 guard_unavailable`, is the service's error: it counts
            # towards the outage stop and keeps the run out of a baseline.
            kind = "dataset_refused" if response.status_code in REFUSAL_STATUSES else "error"
            record["status"], record["reason"] = kind, _detail(response)
            return False
        return True

    async def _bindings(self, record: dict[str, Any], case: "EvalCase", sid: str, headers: dict[str, str]) -> bool:
        if case.bindings is None:
            return True  # the default bindings the dataset route proposed stay
        payload = [binding.model_dump() for binding in case.bindings]
        response = await self.client.put(f"/v1/sessions/{sid}/bindings", headers=headers, json=payload)
        if response.status_code != 200:
            kind = "bindings_invalid" if response.status_code in REFUSAL_STATUSES else "error"
            record["status"], record["reason"] = kind, _detail(response)
            return False
        answer = response.json()
        if not answer.get("complete"):
            record["status"] = "bindings_invalid"
            record["reason"] = "missing roles: " + ", ".join(answer.get("missing_roles") or [])
            return False
        return True

    async def _turn(
        self, record: dict[str, Any], sid: str, body: dict[str, str], headers: dict[str, str]
    ) -> dict[str, Any] | None:
        self.timed.chunks.clear()
        started = time.monotonic()
        response = await self.client.post(f"/v1/sessions/{sid}/messages", headers=headers, json=body)
        turn = Turn(
            response.status_code,
            None if response.status_code == 200 else _detail(response),
            parse_events(self.timed.chunks, started) if response.status_code == 200 else [],
        )
        plot = book_turn(record, turn)
        book_attribution(record, self.collector.take(headers["X-Request-Id"]), self.settings)
        return plot

    async def _save_png(
        self,
        record: dict[str, Any],
        case: "EvalCase",
        repeat: int,
        sid: str,
        plot: dict[str, Any],
        headers: dict[str, str],
    ) -> None:
        # A shipped result without its PNG is not a pass: the galleries could not
        # show it and a baseline must not count it, so it becomes an error.
        names = [name for name in plot.get("artifacts") or [] if str(name).endswith(".png")]
        if not names:
            record["status"], record["reason"], record["error"] = "error", "no_png", "plot_without_png"
            return
        response = await self.client.get(f"/v1/sessions/{sid}/artifacts/{names[0]}", headers=headers)
        if response.status_code != 200:
            record["status"], record["reason"], record["error"] = (
                "error",
                "no_png",
                f"artifact http {response.status_code}",
            )
            return
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{case.case_id}-r{repeat}.png"
        (self.renders_dir / file_name).write_bytes(response.content)
        record["png"] = f"{self.renders_dir.name}/{file_name}"


# --- The matrix ------------------------------------------------------------------------------


@dataclass
class MatrixResult:
    """A finished matrix run: the report, where it went, the diff and the exit code."""

    report: dict[str, Any]
    report_path: Path
    summary_path: Path
    gallery_path: Path
    diff: Diff | None
    exit_code: int
    baseline_written: Path | None = None
    notes: list[str] = field(default_factory=list)


def _echo(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def _git_sha() -> str | None:
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() or None


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def build_stamp(
    settings: "AgentSettings", config: MatrixConfig, cases: list["EvalCase"], started: datetime
) -> dict[str, Any]:
    """What produced the report: the configuration, the versions, the prompts and the prices."""
    from agents import main as service

    return {
        "run_id": hashlib.sha256(f"{started.isoformat()}-{secrets.token_hex(8)}".encode()).hexdigest()[:12],
        "date": started.date().isoformat(),
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": None,
        "provider": settings.provider,
        "model": settings.model,
        "judge_model": settings.judge_model,
        "location": settings.location,
        "renderer": settings.renderer,
        "render_url": getattr(settings, "render_url", None),
        "adk_version": _version("google-adk"),
        "anthropic_version": _version("anthropic"),
        "service_version": _version("anyplot"),
        "python": platform.python_version(),
        "git_sha": _git_sha(),
        "prompt_hashes": service._prompt_hashes(),
        "prices_usd_per_mtok": {
            model: {"input": price_of(model).input, "output": price_of(model).output}
            for model in sorted({settings.model, settings.judge_model})
        },
        "location_surcharge": LOCATION_SURCHARGE.get(settings.location, 0.0),
        "cases": config.cases,
        "case_count": len(cases),
        "repeats": config.repeats,
        "budget_usd": config.budget_usd,
        "tolerance": config.tolerance,
        "gallery_seed": config.seed,
        "baseline": str(config.baseline_path) if config.baseline_path else None,
        "argv": list(config.argv),
    }


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise SetupError(f"too many reports named {path.stem} in {path.parent}")


def is_error(run: dict[str, Any]) -> bool:
    """A run that ended in an error, which measures an outage or a bug rather than the model.

    The harness's own crash (`harness_error`), the service's refusal of a request
    (`status == "error"`: a session that could not open, a judge outage, a turn that
    ended with `capacity` or without a result, a shipped plot without its PNG), the
    pipeline's `failed (error)`, and an `error` event that came with a plot all count.
    """
    return (
        run.get("status") in ERROR_STATUSES
        or run.get("reason") == "error"
        or bool(run.get("error"))
        or bool(run.get("pipeline_error"))
    )


def write_baseline(report: dict[str, Any], baselines_dir: Path) -> tuple[Path | None, str | None]:
    """Write the report as `<baselines_dir>/<model>.json`; refused for a partial run, errors or users' cases."""
    runs = report.get("runs") or []
    if report.get("stopped"):
        return None, f"not saved as a baseline: the run stopped early ({report['stopped']})"
    if any(run.get("origin") != "fixtures" for run in runs):
        return None, "not saved as a baseline: the run includes promoted cases, which hold users' data"
    errors = sorted({str(run.get("case_id")) for run in runs if is_error(run)})
    if errors:
        return None, (
            f"not saved as a baseline: {len(errors)} cases ended in an error ({', '.join(errors[:5])}"
            + (", ..." if len(errors) > 5 else "")
            + "); rerun once the cause is fixed"
        )
    baselines_dir.mkdir(parents=True, exist_ok=True)
    path = baselines_dir / f"{report['stamp']['model']}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, None


async def run_matrix(
    cases: list["EvalCase"],
    config: MatrixConfig,
    *,
    services: "Services | None" = None,
    runtime: "Runtime | None" = None,
    echo: Callable[[str], None] = _echo,
) -> MatrixResult:
    """Run every case `config.repeats` times, write the report, the summary and the galleries, compare and decide."""
    from agents import main as service
    from agents.anyplot.services import Services, set_services
    from agents.anyplot.settings import get_settings

    settings = get_settings()
    services = services or Services()
    set_services(services)
    if config.render_token is not None:
        await config.render_token.renew(services)
    if config.preflight:
        await preflight(cases, services, echo)
    runtime = runtime or service.Runtime()
    saved_overrides = dict(service.app.dependency_overrides)
    service.app.dependency_overrides[service.get_runtime] = lambda: runtime
    service.app.dependency_overrides[service.check_caller] = lambda: None  # in process: there is no caller to check
    collector = AttributionCollector()
    attribution_logger = logging.getLogger(ATTRIBUTION_LOGGER)
    saved_level = attribution_logger.level
    attribution_logger.setLevel(logging.INFO)
    attribution_logger.addHandler(collector)
    config.out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    stamp = build_stamp(settings, config, cases, started)
    timed = TimedApp(service.app)
    runs: list[dict[str, Any]] = []
    stopped: str | None = None
    total = costliest = 0.0
    errors_in_a_row = 0
    plan = [(case, repeat) for repeat in range(1, config.repeats + 1) for case in cases]
    try:
        transport = httpx.ASGITransport(app=timed)
        async with httpx.AsyncClient(transport=transport, base_url="http://agents", timeout=None) as client:
            runner = CaseRunner(client, timed, collector, settings, config.out / "renders")
            for index, (case, repeat) in enumerate(plan, start=1):
                if config.budget_usd is not None and runs and total + costliest > config.budget_usd:
                    stopped = "budget"
                    echo(
                        f"stopped: ${total:.4f} spent, and the costliest case so far (${costliest:.4f}) "
                        f"could pass --budget-usd {config.budget_usd}"
                    )
                    break
                if config.render_token is not None:
                    try:
                        if await config.render_token.renew(services):
                            echo("renewed the renderer token")
                    except SetupError as exc:
                        stopped = "outage"
                        echo(f"stopped: the renderer token could not be renewed: {exc}")
                        break
                record = await runner.run(case, repeat)
                runs.append(record)
                total += record["cost_usd"]
                costliest = max(costliest, record["cost_usd"])
                echo(
                    f"[{index}/{len(plan)}] {case.case_id} r{repeat}: {record['status']}"
                    + (f" ({record['reason']})" if record["reason"] else "")
                    + (f" [{record['stage']}]" if record.get("stage") else "")
                    + f", {'pass' if record['passed'] else 'fail'}, attempts {record['attempts']}, "
                    f"${record['cost_usd']:.4f}, {record['e2e_s'] or 0:.1f} s (total ${total:.4f})"
                )
                errors_in_a_row = errors_in_a_row + 1 if is_error(record) else 0
                if record.get("pipeline_error") == RENDERER_OUTAGE:
                    stopped = "outage"
                    echo(
                        f"stopped: the renderer became unavailable during {case.case_id} ({RENDERER_OUTAGE}); "
                        "check its URL and your token (AGENT_RENDER_TOKEN lasts one hour; --gcloud-token renews it)"
                    )
                    break
                if errors_in_a_row >= MAX_ERRORS_IN_A_ROW:
                    stopped = "outage"
                    echo(
                        f"stopped: {errors_in_a_row} runs in a row ended in an error "
                        f"(last: {record.get('pipeline_error') or record.get('error') or record.get('reason')}); "
                        "check the models' quota and the renderer before you rerun"
                    )
                    break
                if config.budget_usd is not None and total > config.budget_usd and index < len(plan):
                    stopped = "budget"
                    echo(f"stopped: the estimated cost ${total:.4f} passed --budget-usd {config.budget_usd}")
                    break
    except asyncio.CancelledError:
        stopped = "interrupted"
    finally:
        service.app.dependency_overrides.clear()
        service.app.dependency_overrides.update(saved_overrides)
        attribution_logger.removeHandler(collector)
        attribution_logger.setLevel(saved_level)
    stamp["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    summary = summarize(runs)
    report = {"schema": REPORT_SCHEMA, "stamp": stamp, "summary": summary, "runs": runs, "stopped": stopped}
    diff = compare(config.baseline, report, tolerance=config.tolerance) if config.baseline is not None else None
    result = write_outputs(report, config, diff)
    if stopped == "interrupted":
        echo(f"interrupted: the partial report is {result.report_path}")
        raise asyncio.CancelledError
    if config.save_baseline:
        result.baseline_written, note = write_baseline(report, config.baselines_dir)
        if note:
            result.notes.append(note)
    harness_errors = summary["harness_errors"]
    if harness_errors:
        result.notes.append(
            f"{harness_errors} runs crashed in the harness (the `error` field of each run names the class); "
            "they count as failures"
        )
    if stopped == "outage":
        result.exit_code = EXIT_OUTAGE
    elif stopped:
        result.exit_code = EXIT_STOPPED
    elif (diff is not None and diff.regression) or harness_errors:
        result.exit_code = EXIT_REGRESSION
    return result


def write_outputs(report: dict[str, Any], config: MatrixConfig, diff: Diff | None) -> MatrixResult:
    """Write the JSON report, its Markdown summary and the two gallery pages under `config.out`."""
    stamp = report["stamp"]
    report_path = _unique(config.out / f"{stamp['date']}-{stamp['model']}.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_path = report_path.with_suffix(".md")
    summary_path.write_text(summary_markdown(report, diff), encoding="utf-8")
    gallery_path = config.out / "gallery.html"
    gallery_path.write_text(
        gallery_html(report, config.out, size=config.gallery_size, seed=config.seed), encoding="utf-8"
    )
    (config.out / "gallery-all.html").write_text(gallery_all_html(report), encoding="utf-8")
    return MatrixResult(report, report_path, summary_path, gallery_path, diff, EXIT_OK)


def load_baseline(path: Path) -> dict[str, Any]:
    """A saved report to compare against; refuses a schema version the diff cannot read (`SUPPORTED_SCHEMAS`)."""
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SetupError(f"cannot read the baseline {path} ({type(exc).__name__})") from exc
    if not isinstance(baseline, dict) or baseline.get("schema") not in SUPPORTED_SCHEMAS or "summary" not in baseline:
        supported = ", ".join(str(schema) for schema in sorted(SUPPORTED_SCHEMAS))
        raise SetupError(f"{path} is not a report of schema {supported}")
    return baseline


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        configure(args, os.environ)
        if args.gcloud_token:
            os.environ["AGENT_RENDER_TOKEN"] = gcloud_token()
    except SetupError as exc:
        _echo(f"setup: {exc}")
        return EXIT_SETUP
    from pydantic import ValidationError

    from agents.anyplot.settings import get_settings

    get_settings.cache_clear()
    try:
        settings = get_settings()
    except ValidationError as exc:
        _echo(f"settings: {exc}")
        return EXIT_SETUP
    try:
        result = _prepare_and_run(args, settings, argv)
    except (SetupError, UnknownPrice) as exc:
        _echo(f"setup: {exc}")
        return EXIT_SETUP
    except KeyboardInterrupt:
        return 130
    stamp_model = result.report["stamp"]["model"]
    summary = result.report["summary"]
    print(f"Report: {result.report_path}")
    print(f"Summary: {result.summary_path}")
    print(f"Gallery: {result.gallery_path}")
    if result.baseline_written:
        print(f"Baseline: {result.baseline_written}")
    for note in result.notes:
        print(note)
    rate = summary.get("pass_rate")
    print(
        f"{stamp_model}: {summary['passed']} of {summary['runs']} runs passed"
        + (f" ({rate * 100:.1f} %)" if rate is not None else "")
        + f", ${summary['cost_total_usd']:.4f} at list price"
    )
    if result.diff is not None:
        print(diff_markdown(result.diff))
    if result.exit_code == EXIT_STOPPED:
        print("Stopped early by --budget-usd: the report covers the runs that finished.")
    if result.exit_code == EXIT_OUTAGE:
        print("Stopped by an outage: the report covers the runs that finished; fix the cause and rerun.")
    return result.exit_code


def _prepare_and_run(args: argparse.Namespace, settings: "AgentSettings", argv: list[str] | None) -> MatrixResult:
    """The checks that need the settings, then the run."""
    from agents.anyplot.render import make_backend
    from agents.anyplot.render.contract import RendererUnavailable
    from agents.anyplot.settings import AgentSettings
    from agents.evals.cases import CaseError, load_cases, select_cases

    price_of(settings.model)
    price_of(settings.judge_model)
    if args.render_url and "render_url" not in AgentSettings.model_fields:
        raise SetupError(
            "this checkout's AgentSettings has no render_url, so the remote renderer is not built here; "
            "merge the renderer change first"
        )
    try:
        make_backend(settings)
    except RendererUnavailable as exc:
        raise SetupError(f"renderer {settings.renderer}: {exc}") from exc
    try:
        cases = select_cases(load_cases(), args.cases)
    except CaseError as exc:
        raise SetupError(str(exc)) from exc
    if not cases:
        raise SetupError(f"no case matches --cases {args.cases!r}")
    baseline_path: Path | None = None
    if not args.no_baseline:
        pinned = BASELINES_DIR / f"{AgentSettings.model_fields['model'].default}.json"
        baseline_path = args.baseline or (pinned if pinned.is_file() else None)
    if settings.renderer == "remote" and not args.gcloud_token and (note := token_note(os.environ)):
        _echo(note)
    config = MatrixConfig(
        cases=args.cases,
        repeats=args.repeats,
        budget_usd=args.budget_usd,
        out=args.out,
        baseline=load_baseline(baseline_path) if baseline_path else None,
        baseline_path=baseline_path,
        tolerance=args.tolerance,
        seed=args.seed,
        gallery_size=args.gallery_size,
        save_baseline=args.save_baseline,
        preflight=not args.no_preflight,
        render_token=RenderToken(os.environ) if args.gcloud_token else None,
        argv=list(sys.argv[1:] if argv is None else argv),
    )
    return asyncio.run(run_matrix(cases, config))


if __name__ == "__main__":
    raise SystemExit(main())
