"""The switch eval: the owner's five decisions survive a library switch (owner decisions of 2026-11-02).

Run it from the repository root. It calls the configured models and the deployed renderer, so it spends tokens:

    uv run --extra agents python -m agents.evals.carry --targets plotly ggplot2

Per target it opens a session in `--source` (matplotlib) on `scatter-basic` through the real `/v1`
flow in process (`agents.main:app` over httpx's `ASGITransport`, as `matrix.py` does), pastes a
small time series, confirms it, seeds the plot memory with the owner's own examples of tuning
(`OWNER_EXAMPLES`: a horizontal line at 7, an annotation with a LaTeX formula, outliers as red
stars, the x-axis label 'Zeit (h)', x limits 0 to 100), switches to the target and sends the
page's `carry_plot` action, the one run the switch offers. What shipped is then checked in code,
never by a model (`check_code`): the label is not among the shipped result's
`requested_not_found`, and the exported code carries each intent in the target's own API
(`CHECKS`), the equivalent where the library has no such feature (ggplot2 typesets a formula
with plotmath, and its star is shape 8). The exit code is 0 only when every check of every
target passed and the spend stayed under `--cap`.

The models are the settings' (Claude Haiku on Vertex in `eu` by default); the renderer is the deployed
one (`AGENT_RENDER_URL`, or `gcloud run services describe anyplot-renderer`, a read), called with the
developer's Application Default Credentials. The cost is priced from the content-free attribution
lines (`agents/evals/pricing.py`). The renders land under `--out` for a look.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SPEC_ID = "scatter-basic"
USER = "adm_carryeval0000000"
DATA = (
    "Zeit,Messwert\n"
    + "\n".join(
        f"{hour},{value}"
        for hour, value in zip(
            range(0, 100, 4),
            [
                5.1,
                5.4,
                5.9,
                6.2,
                6.0,
                6.6,
                7.1,
                6.8,
                7.4,
                12.6,
                7.9,
                8.1,
                7.7,
                8.4,
                8.8,
                8.5,
                9.0,
                1.2,
                9.3,
                9.1,
                9.6,
                9.9,
                10.2,
                9.8,
                10.4,
            ],
            strict=True,
        )
    )
    + "\n"
)
"""Hours 0 to 96 and a measurement that climbs from about 5 to 10, with two outliers (12.6 at 36 h, 1.2 at 68 h)."""

OWNER_EXAMPLES: list[dict[str, Any]] = [
    {"kind": "reference_line", "text": "horizontal reference line at y = 7"},
    {"kind": "annotation", "text": "annotation top left: the formula $y = ax^2 + b$ typeset as LaTeX"},
    {"kind": "marker", "text": "outliers (values far from the trend) as red star markers"},
    {"kind": "axis_label", "target": "x", "text": "x-axis label: 'Zeit (h)'", "expected_text": "Zeit (h)"},
    {"kind": "limits", "target": "x", "text": "x limits 0 to 100"},
]
"""The owner's own examples of what the memory must hold across a switch (2026-11-02)."""
LABEL = "Zeit (h)"


@dataclass(frozen=True)
class Check:
    """One intent and the patterns that find it in the exported code: any one of them is enough."""

    name: str
    patterns: tuple[str, ...]

    def found(self, code: str) -> bool:
        return any(re.search(pattern, code, re.IGNORECASE | re.DOTALL) for pattern in self.patterns)


_SEVEN = r"7(?:\.0+)?\b"
_FORMULA = r"x\s*\^\s*\{?\s*2"
_ZERO_TO_HUNDRED = r"[\[(]\s*0(?:\.0+)?\s*,\s*100(?:\.0+)?\s*[\])]"


def _key(name: str) -> str:
    """A keyword argument or a dict key: `symbol="star"` and `{"symbol": "star"}` are the same intent in plotly."""
    return rf"""["']?{name}["']?\s*[:=]\s*"""


CHECKS: dict[str, list[Check]] = {
    "plotly": [
        Check(
            "reference_line",
            (
                rf"add_hline\([^)]*y\s*=\s*{_SEVEN}",
                rf"{_key('y0')}{_SEVEN}.*{_key('y1')}{_SEVEN}",
                rf"{_key('y')}[\[(]\s*{_SEVEN}\s*,\s*{_SEVEN}\s*[\])]",  # a line trace from x0 to x1 at y = 7
            ),
        ),
        # The renderer's browser loads no MathJax, so `$...$` is drawn as typed: plotly typesets with HTML tags.
        Check("latex_annotation", (r"x\s*<sup>\s*2\s*</sup>", r"x²")),
        Check("star_markers", (rf"{_key('(?:marker_)?symbol')}['\"]star",)),
        Check("label_text", (re.escape(LABEL),)),
        Check("x_limits", (rf"{_key('(?:xaxis_)?range')}{_ZERO_TO_HUNDRED}",)),
    ],
    "ggplot2": [
        Check("reference_line", (rf"geom_hline\([^)]*yintercept\s*=\s*{_SEVEN}",)),
        Check(
            "latex_annotation",
            (
                rf"(?:expression|bquote|TeX|latex2exp)\s*\(.*{_FORMULA}",
                rf"parse\s*=\s*TRUE.*{_FORMULA}|{_FORMULA}.*parse\s*=\s*TRUE",
            ),
        ),
        Check("star_markers", (r"shape\s*=\s*(?:8L?\b|['\"](?:\*|★|\\u2605)['\"])",)),
        Check("label_text", (re.escape(LABEL),)),
        Check(
            "x_limits",
            (
                r"xlim\s*\(\s*0(?:\.0+)?\s*,\s*100",
                r"limits\s*=\s*c\(\s*0(?:\.0+)?\s*,\s*100",
                r"xlim\s*=\s*c\(\s*0(?:\.0+)?\s*,\s*100",
            ),
        ),
    ],
    # seaborn draws on matplotlib's axes: a mathtext string is matplotlib's LaTeX, `*` its star marker.
    "seaborn": [
        Check("reference_line", (rf"axhline\(\s*(?:y\s*=\s*)?{_SEVEN}", rf"hlines\(\s*(?:y\s*=\s*)?{_SEVEN}")),
        Check("latex_annotation", (rf"(?:text|annotate)\(.*\$[^$\n]*{_FORMULA}[^$\n]*\$",)),
        Check("star_markers", (r"marker\s*=\s*['\"]\*['\"]", r"['\"]marker['\"]\s*:\s*['\"]\*['\"]")),
        Check("label_text", (re.escape(LABEL),)),
        Check(
            "x_limits",
            (
                r"set_xlim\(\s*(?:left\s*=\s*)?0(?:\.0+)?\s*,\s*(?:right\s*=\s*)?100",
                r"xlim\(\s*0(?:\.0+)?\s*,\s*100",
                rf"xlim\s*=\s*{_ZERO_TO_HUNDRED}",
            ),
        ),
    ],
}
"""Per target library, every intent of `OWNER_EXAMPLES` in that library's own API."""

TUNE_MESSAGE = (
    "Bitte eine horizontale Referenzlinie bei y = 7, oben links eine Annotation mit der Formel $y = ax^2 + b$ in "
    "LaTeX, die Ausreißer als rote Sterne, die x-Achse mit 'Zeit (h)' beschriften und die x-Achse von 0 bis 100."
)
"""The owner's five examples as one chat message in the source library (`--via chat`)."""
SWITCH_MESSAGE = "Erstelle den Plot bitte in {library}."
"""The switch asked for in the chat (`--via chat`), as the owner wrote it on 2026-11-02."""


def check_code(library: str, code: str) -> dict[str, bool]:
    """Which intents the exported code of `library` carries (`CHECKS`)."""
    return {check.name: check.found(code) for check in CHECKS[library]}


@dataclass
class Outcome:
    """One target's run: the shipped status, the checks, and what it cost."""

    library: str
    status: str = "not_run"
    version: int | None = None
    checks: dict[str, bool] = field(default_factory=dict)
    requested_not_found: list[str] = field(default_factory=list)
    residual: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    note: str = ""
    via: str = "memory"
    remembered: int = 0
    """`--via chat`: the memory entries the tuning turn left (the root's `remember` items, stored once it shipped)."""
    switch: dict[str, Any] | None = None
    """`--via chat`: the switch the switch turn's `done` carried (the root's `switch_plot`)."""

    @property
    def passed(self) -> bool:
        asked = self.via != "chat" or (self.switch is not None and self.switch.get("library") == self.library)
        return (
            asked
            and self.status in ("ok", "needs_attention")
            and bool(self.checks)
            and all(self.checks.values())
            and LABEL not in self.requested_not_found
        )


def done_of(stream: str) -> dict[str, Any]:
    """The `done` event's data of an SSE turn, or {} without one."""
    for block in stream.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        if fields.get("event") == "done":
            data = json.loads(fields.get("data", "{}"))
            return data if isinstance(data, dict) else {}
    return {}


class _Lines(logging.Handler):
    """Collects the attribution lines (JSON) for the cost."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.lines: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.lines.append(json.loads(record.getMessage()))
        except ValueError:
            pass


def setup_env(source: str, targets: list[str], model: str | None, location: str | None) -> None:
    """Development settings with the remote renderer and every library of the run enabled."""
    os.environ.setdefault("PYTHON_DOTENV_DISABLED", "1")
    os.environ["ENVIRONMENT"] = "development"
    os.environ["AGENT_RENDERER"] = "remote"
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "anyplot")
    os.environ["AGENT_LIBRARIES"] = ",".join(dict.fromkeys([source, *targets]))
    if model:
        os.environ["AGENT_MODEL"] = model
    if location:
        os.environ["AGENT_LOCATION"] = location
    from agents.evals.ladder_lab import renderer_url

    renderer_url()


async def run_target(library: str, source: str, out: Path, lines: _Lines, via: str = "memory") -> Outcome:
    """One session: paste, confirm, seed the memory in `source`, switch to `library`, `carry_plot`, check.

    With `via="chat"` the memory is not seeded: the first plot in `source`, then the owner's
    examples as one chat message (`TUNE_MESSAGE`), whose run the root hands its decisions to, then
    the switch asked for in the chat (`SWITCH_MESSAGE`), carried out as the page does: the switch
    route with `source: chat`, then `carry_plot`.
    """
    import httpx

    from agents.anyplot.dev_fixture import snapshot_from_repo
    from agents.anyplot.memory import memory_delta, plan, read_memory
    from agents.anyplot.schemas import RememberItem
    from agents.anyplot.services import get_services
    from agents.anyplot.settings import get_settings
    from agents.evals.pricing import call_cost, judge_cost
    from agents.main import app, get_runtime

    settings = get_settings()
    outcome = Outcome(library, via=via)
    headers = {"X-Anyplot-User": USER, "X-Anyplot-Tier": "admin", "X-Request-Id": f"carry-{library}"}
    start = len(lines.lines)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agents", timeout=600
    ) as client:
        body = {
            "user": USER,
            "spec_id": SPEC_ID,
            "library": source,
            "locale": "de",
            "snapshot": snapshot_from_repo(SPEC_ID, source).model_dump(),
        }
        opened = await client.post("/v1/sessions", headers=headers, json=body)
        opened.raise_for_status()
        sid = opened.json()["session_id"]
        pasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=headers, json={"text": DATA})
        pasted.raise_for_status()
        (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=headers)).raise_for_status()
        runtime = get_runtime()
        switch_body: dict[str, Any] = {
            "library": library,
            "snapshot": snapshot_from_repo(SPEC_ID, library).model_dump(),
        }
        if via == "chat":
            for turn_body in ({"action": "create_plot"}, {"text": TUNE_MESSAGE}):
                sent = await client.post(f"/v1/sessions/{sid}/messages", headers=headers, json=turn_body)
                sent.raise_for_status()
            outcome.remembered = len(read_memory((await runtime.session(USER, sid)).state))
            asked = await client.post(
                f"/v1/sessions/{sid}/messages", headers=headers, json={"text": SWITCH_MESSAGE.format(library=library)}
            )
            asked.raise_for_status()
            switch = done_of(asked.text).get("switch")
            outcome.switch = switch if isinstance(switch, dict) else None
            if outcome.switch is None or outcome.switch.get("library") != library:
                outcome.note = "the switch turn asked for no switch to this library"
                return outcome
            switch_body["source"] = "chat"
        else:
            items = [RememberItem.model_validate(item) for item in OWNER_EXAMPLES]
            planned = plan([], items, seq=1, turn=1)
            await runtime.write_state(await runtime.session(USER, sid), memory_delta(planned.entries, planned.seq))
        switched = await client.post(f"/v1/sessions/{sid}/library", headers=headers, json=switch_body)
        switched.raise_for_status()
        if not switched.json()["carry"]["offer"]:
            outcome.note = "the switch offered no carry run"
            return outcome
        turn = await client.post(f"/v1/sessions/{sid}/messages", headers=headers, json={"action": "carry_plot"})
        turn.raise_for_status()
        version = get_services().versions.latest_rendered(sid, target=(SPEC_ID, library))
        if version is None:
            outcome.status = "failed"
            outcome.note = "nothing shipped"
        else:
            outcome.status = version.result.status
            outcome.version = version.number
            outcome.checks = check_code(library, version.export)
            shows = version.result.shows
            outcome.requested_not_found = list(shows.requested_not_found) if shows is not None else []
            outcome.residual = list(version.result.residual_defects)
            folder = out / library
            folder.mkdir(parents=True, exist_ok=True)
            (folder / version.code_artifact).write_text(version.export, encoding="utf-8")
            png = await client.get(
                f"/v1/sessions/{sid}/artifacts/plot-{version.theme}.png", headers=headers, params={"v": version.number}
            )
            if png.is_success:
                (folder / f"plot-{version.theme}.png").write_bytes(png.content)
        await client.delete(f"/v1/sessions/{sid}", headers=headers)
    for line in lines.lines[start:]:
        if line.get("hook") == "model":
            outcome.cost_usd += call_cost(settings.model, settings.location, line)
        elif "judge_input" in line:
            outcome.cost_usd += judge_cost(
                settings.judge_model, settings.location, line.get("judge_input", 0), line.get("judge_output", 0)
            )
    return outcome


async def main_async(args: argparse.Namespace) -> int:
    from agents.anyplot import telemetry
    from agents.anyplot.plugins.ledger import ATTRIBUTION_LOGGER

    lines = _Lines()
    logger = logging.getLogger(ATTRIBUTION_LOGGER)
    logger.addHandler(lines)
    logger.setLevel(logging.INFO)
    out = Path(args.out)
    outcomes: list[Outcome] = []
    spent = 0.0
    with telemetry.harness():
        for library in args.targets:
            if spent >= args.cap:
                outcomes.append(Outcome(library, note=f"skipped: the cap of ${args.cap:.2f} was reached"))
                continue
            outcome = await run_target(library, args.source, out, lines, args.via)
            spent += outcome.cost_usd
            outcomes.append(outcome)
            print(json.dumps({**outcome.__dict__, "passed": outcome.passed}, ensure_ascii=False), flush=True)
    print(f"total ${spent:.3f} of ${args.cap:.2f}", flush=True)
    return 0 if outcomes and all(outcome.passed for outcome in outcomes) and spent <= args.cap else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", default="matplotlib")
    parser.add_argument("--targets", nargs="+", default=["plotly", "ggplot2"], choices=sorted(CHECKS))
    parser.add_argument(
        "--via",
        default="memory",
        choices=["memory", "chat"],
        help="memory: seed the owner's examples; chat: tune and switch through chat turns, as a user does",
    )
    parser.add_argument("--model", default=None, help="AGENT_MODEL (default: the settings', claude-haiku-5-5)")
    parser.add_argument("--location", default=None, help="AGENT_LOCATION (default: the settings', eu)")
    parser.add_argument("--cap", type=float, default=1.5, help="USD; a target after the cap is skipped")
    parser.add_argument("--out", default="agents/evals/reports/carry")
    args = parser.parse_args()
    setup_env(args.source, args.targets, args.model, args.location)
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
