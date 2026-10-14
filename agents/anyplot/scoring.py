"""Score an adapted plot with the catalogue's rubric: the request, the system prompt, the total.

The owner's quality ladder of 2026-10-12: an agent result ships when it reaches a
score threshold, scored like the pipeline scores catalogue implementations. This
module is the model-independent half of that scorer, a pure layer with no ADK and
no client import, so the offline eval (`agents/evals/score.py`) uses it today and
the runtime reviewer can later. The model reads the rubric and returns points per
criterion and defect lines; the code checks the answer, adds up and applies the
caps, so no model ever writes a total.

**The rubric is the catalogue's, verbatim** (owner principle: agents share the
pipeline's rules, one place to change a rule). `system_prompt` joins
`agents/anyplot/prompts/scorer.md`, which says how the rubric applies to a user's
plot, with sections cut by heading from `prompts/quality-criteria.md` and
`prompts/workflow-prompts/ai-quality-review.md`. The criteria are the 16 that
describe what a user sees (`SCORED`, 75 points, scaled to 100): Visual Quality,
Design Excellence, Spec Compliance, and DQ-01 and DQ-03 of Data Quality. Left out:
DQ-02 (the realism of the scenario: the data is the user's own), Code Quality (the
catalogue's code style, inherited through the edits) and Library Mastery (a
catalogue showcase). The caps are the rubric's that concern scored items; a cap
on DQ-02 or CQ-04 cannot fire here.

A technical item (VQ, SC, DQ) below its maximum without a defect line naming it is
a *silent deduction*: the rubric forbids it, and `ScoreResult.silent` lists them so
an eval can count them. They still count as scored, as the catalogue's review gate
counts them.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.defects import CRITERIA, DEFECT_RE


REPO = Path(__file__).resolve().parents[2]
SCORER_PROMPT = Path(__file__).with_name("prompts") / "scorer.md"
CRITERIA_FILE = REPO / "prompts" / "quality-criteria.md"
REVIEW_FILE = REPO / "prompts" / "workflow-prompts" / "ai-quality-review.md"

SCORED: dict[str, int] = {
    item: points for item, points in CRITERIA.items() if item[:2] in ("VQ", "DE", "SC") or item in ("DQ-01", "DQ-03")
}
"""The criteria a user's plot is scored on and their maxima (75 points)."""
SCORED_MAX = sum(SCORED.values())
ScoredId = Literal[
    "VQ-01", "VQ-02", "VQ-03", "VQ-04", "VQ-05", "VQ-06", "VQ-07",
    "DE-01", "DE-02", "DE-03",
    "SC-01", "SC-02", "SC-03", "SC-04",
    "DQ-01", "DQ-03",
]  # fmt: skip
"""`SCORED`'s ids as a type, so a structured answer cannot name another criterion (a test holds the two equal)."""
DE_DEFAULTS: dict[str, int] = {"DE-01": 4, "DE-02": 2, "DE-03": 2}
TECHNICAL = tuple(item for item in SCORED if item[:2] in ("VQ", "SC", "DQ"))
MAX_SUGGESTIONS = 3

# The rubric sections the prompt carries, as (file, heading line). Each section runs to
# the next heading of the same or a higher level.
CRITERIA_SECTIONS = (
    "### Scoring principles",
    "## Visual Quality (30 Points)",
    "## Design Excellence (20 Points)",
    "## Spec Compliance (15 Points)",
    "## Data Quality (15 Points)",
    "## Plot-Type Characteristics (judge against the spec, not generic ideals)",
    "## Score Caps",
    "## Anti-Inflation Calibration Anchors",
)
REVIEW_SECTIONS = (
    "### 5c. MANDATORY: Theme-Readability Check (both renders)",
    "### 5d. MANDATORY: Proportional Sizing Check (both renders)",
    "### 8a. Strengths and weaknesses (every review)",
)

TOOL_NAME = "submit_score"
TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string", "enum": list(SCORED)}, "points": {"type": "integer"}},
                "required": ["id", "points"],
                "additionalProperties": False,
            },
        },
        "defects": {"type": "array", "items": {"type": "string"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"},
    },
    "required": ["items", "defects", "suggestions", "description"],
    "additionalProperties": False,
}
"""The `submit_score` tool's input. Strict tool use keeps the input schema-valid; strict
schemas take no numeric bounds, so the range of each item's points is checked in
`parse_answer`, per criterion."""

_HEADING = re.compile(r"^(#{1,6})\s")


class ScoreItem(BaseModel):
    id: ScoredId
    points: int


class ScoreAnswer(BaseModel):
    """`TOOL_SCHEMA` as a structured answer, for the pipeline's reviewer in `catalogue` mode;
    `parse_answer` checks the criteria and ranges the schema cannot."""

    items: list[ScoreItem]
    defects: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    description: str = ""


def mend_answer(answer: dict[str, Any]) -> dict[str, Any]:
    """A review answer with its formal misses mended, so `parse_answer` can read it.

    For the pipeline's reviewer only (the offline scorer retries instead): a criterion named
    twice keeps its first entry, points are clamped into the criterion's range, and a missing
    Design Excellence criterion counts at its default. A missing technical criterion stays
    missing, so `parse_answer` raises and the pipeline asks for the review again: the ship bar
    reads the technical points, and an unscored item is not a perfect one. The defect lines
    stay as written.
    """
    seen: dict[str, int] = {}
    for item in answer.get("items") or []:
        if not isinstance(item, dict) or item.get("id") not in SCORED or item["id"] in seen:
            continue
        value = item.get("points")
        if isinstance(value, int) and not isinstance(value, bool):
            seen[item["id"]] = min(max(value, 0), SCORED[item["id"]])
    for name, default in DE_DEFAULTS.items():
        seen.setdefault(name, default)
    return {**answer, "items": [{"id": name, "points": points} for name, points in seen.items()]}


class ScoreError(ValueError):
    """An answer that is not a complete score: a criterion missing or twice, points out of range."""


def section(text: str, heading: str) -> str:
    """The section of `text` that starts with the line `heading`, up to the next heading of its level or higher."""
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        raise ValueError(f"heading not found: {heading!r}") from None
    opening = _HEADING.match(heading)
    if opening is None:
        raise ValueError(f"not a heading: {heading!r}")
    level = len(opening.group(1))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = _HEADING.match(lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


HIGHLIGHT_RULE = Path(__file__).with_name("prompts") / "scorer_highlights.md"


def system_prompt(
    scorer: Path = SCORER_PROMPT,
    criteria: Path = CRITERIA_FILE,
    review: Path = REVIEW_FILE,
    highlights: bool | None = None,
) -> str:
    """`scorer.md` followed by the rubric sections it applies, cut verbatim from the catalogue's prompts.

    `highlights` (experiment; default from `AGENT_SCORER_HIGHLIGHTS=on`) adds a fifth user-plot rule:
    one data-derived highlight is not variant creep (`prompts/scorer_highlights.md`).
    """
    if highlights is None:
        highlights = os.environ.get("AGENT_SCORER_HIGHLIGHTS", "").lower() == "on"
    criteria_text = criteria.read_text(encoding="utf-8")
    review_text = review.read_text(encoding="utf-8")
    parts = [scorer.read_text(encoding="utf-8").strip()]
    if highlights:
        parts.append(HIGHLIGHT_RULE.read_text(encoding="utf-8").strip())
    parts.append("# From the catalogue rubric (prompts/quality-criteria.md)")
    parts += [section(criteria_text, heading) for heading in CRITERIA_SECTIONS]
    parts.append("# From the catalogue review (prompts/workflow-prompts/ai-quality-review.md)")
    parts += [section(review_text, heading) for heading in REVIEW_SECTIONS]
    return "\n\n".join(parts) + "\n"


@dataclass(frozen=True)
class ScoreRequest:
    """One render to score and what the scorer needs to judge it."""

    spec_text: str
    code: str
    profile_summary: str
    bindings_json: str
    png: bytes
    theme: str = "light"
    plot_language: str = "en"


def user_text(request: ScoreRequest) -> str:
    """The request's text part, each value fenced as data by `policy.fence`, which neutralises
    every fence tag inside the value, so a column name or a code comment cannot close a block."""
    from .policy import DATA_PREAMBLE, fence

    return "\n\n".join(
        [
            DATA_PREAMBLE,
            fence("spec_text", request.spec_text),
            fence("plot_code", request.code),
            fence("user_data", request.profile_summary),
            fence("user_data", request.bindings_json),
            fence("plot_language", request.plot_language),
            f"The render follows: plot-{request.theme}.png",
        ]
    )


@dataclass
class ScoreResult:
    """A checked score: points per criterion, the 0–100 score after caps, the lines."""

    points: dict[str, int]
    raw: int
    scaled: int
    score: int
    caps: list[str]
    defects: list[str]
    suggestions: list[str]
    description: str
    silent: list[str] = field(default_factory=list)
    """Technical items below their maximum that no defect line names."""
    malformed: list[str] = field(default_factory=list)
    """Defect lines that do not follow the grammar (`DEFECT_RE`)."""

    def category(self, prefix: str) -> tuple[int, int]:
        """Points and maximum of one category (`VQ`, `DE`, `SC`, `DQ`)."""
        items = [item for item in SCORED if item.startswith(prefix)]
        return sum(self.points[item] for item in items), sum(SCORED[item] for item in items)

    @property
    def technical_share(self) -> float:
        """The share of the technical points (VQ, SC, DQ) the render got."""
        return sum(self.points[item] for item in TECHNICAL) / sum(SCORED[item] for item in TECHNICAL)

    def passes(self, bar: float) -> bool:
        """The review's verdict from the points: at least `bar` of the technical points and no
        technical item at zero (the rubric's caps on VQ-02, VQ-03 and SC-01); Design Excellence
        is not part of it."""
        return self.technical_share >= bar and all(self.points[item] > 0 for item in ("VQ-02", "VQ-03", "SC-01"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "scaled": self.scaled,
            "raw": self.raw,
            "caps": self.caps,
            "points": self.points,
            "categories": {prefix: list(self.category(prefix)) for prefix in ("VQ", "DE", "SC", "DQ")},
            "defects": self.defects,
            "suggestions": self.suggestions,
            "description": self.description,
            "silent": self.silent,
            "malformed": self.malformed,
        }


def caps_for(points: dict[str, int]) -> list[tuple[str, int]]:
    """The rubric's score caps that apply, as (reason, cap)."""
    caps: list[tuple[str, int]] = []
    if points["VQ-02"] == 0:
        caps.append(("VQ-02 = 0 (severe overlap)", 49))
    if points["VQ-03"] == 0:
        caps.append(("VQ-03 = 0 (invisible elements)", 49))
    if points["SC-01"] == 0:
        caps.append(("SC-01 = 0 (wrong plot type)", 40))
    if points["DE-01"] <= 2 and points["DE-02"] <= 2:
        caps.append(("DE-01 <= 2 and DE-02 <= 2 (correct but boring)", 75))
    return caps


def parse_answer(answer: dict[str, Any]) -> ScoreResult:
    """Check the tool input and compute the score; raises `ScoreError` for an incomplete answer."""
    items = answer.get("items")
    if not isinstance(items, list):
        raise ScoreError("items is not a list")
    points: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ScoreError("an item is not an object")
        name, value = item.get("id"), item.get("points")
        if name not in SCORED:
            raise ScoreError(f"unknown criterion {name!r}")
        if name in points:
            raise ScoreError(f"criterion {name} scored twice")
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= SCORED[name]:
            raise ScoreError(f"{name}: points {value!r} outside 0..{SCORED[name]}")
        points[name] = value
    missing = [name for name in SCORED if name not in points]
    if missing:
        raise ScoreError("criteria missing: " + ", ".join(missing))
    defects = [line.strip() for line in answer.get("defects") or [] if isinstance(line, str) and line.strip()]
    suggestions = [line.strip() for line in answer.get("suggestions") or [] if isinstance(line, str) and line.strip()]
    malformed = [line for line in defects if not DEFECT_RE.match(line)]
    named = {found for line in defects if (match := DEFECT_RE.match(line)) for found in match.group("ids").split(", ")}
    silent = [item for item in TECHNICAL if points[item] < SCORED[item] and item not in named]
    ordered = {name: points[name] for name in SCORED}
    raw = sum(ordered.values())
    scaled = round(raw * 100 / SCORED_MAX)
    caps = caps_for(ordered)
    score = min([scaled, *(cap for _, cap in caps)])
    return ScoreResult(
        points=ordered,
        raw=raw,
        scaled=scaled,
        score=score,
        caps=[reason for reason, cap in caps if cap < scaled],
        defects=defects,
        suggestions=suggestions[:MAX_SUGGESTIONS],
        description=str(answer.get("description") or "").strip(),
        silent=silent,
        malformed=malformed,
    )
