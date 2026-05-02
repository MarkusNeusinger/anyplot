"""Helper module for the `/regen` slash command.

Each step in `agentic/commands/regen.md` calls into this package via
`uv run python -m agentic.workflows.modules.regen <subcommand> ...`.
The behavior that used to live as inline shell + Python in the markdown
is now in named, testable functions here — same module-as-CLI pattern as
`core/images.py`.

Public dataclasses:
    PlanSpec      Identity of a regen plan (spec id, title, libraries).
    QualityEval   The structured 6-category evaluation produced in step 2f
                  and consumed by metadata + PR creation.

Both are JSON-serializable (`asdict`) so they can pass between the markdown
layer and the dispatcher via stdin/stdout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlanSpec:
    """Identity + library set for a single `/regen` plan."""

    spec_id: str
    title: str
    latest_update: str  # ISO-8601 of the latest impl-metadata `updated`/`created`
    libraries: list[str]
    plan_path: str = ".regen-plan.md"


@dataclass
class QualityEval:
    """Structured evaluation produced in step 2f of `regen.md`.

    Mirrors the shape that `impl-review.yml` would otherwise write into
    `metadata/python/{lib}.yaml`. The category subtotals (`vq` etc.) must
    sum to `score`.
    """

    score: int
    vq: int  # /30
    de: int  # /20
    sc: int  # /15
    dq: int  # /15
    cq: int  # /10
    lm: int  # /10
    image_description: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    # Per-category checklist with VQ-01…LM-02 items. Schema matches what
    # `impl-review.yml` writes; see prompts/quality-criteria.md.
    criteria_checklist: dict[str, Any] = field(default_factory=dict)
    verdict: str = "APPROVED"  # or "REJECTED"

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> QualityEval:
        return cls(
            score=int(raw["score"]),
            vq=int(raw["vq"]),
            de=int(raw["de"]),
            sc=int(raw["sc"]),
            dq=int(raw["dq"]),
            cq=int(raw["cq"]),
            lm=int(raw["lm"]),
            image_description=str(raw.get("image_description", "")).strip(),
            strengths=list(raw.get("strengths") or []),
            weaknesses=list(raw.get("weaknesses") or []),
            criteria_checklist=dict(raw.get("criteria_checklist") or {}),
            verdict=str(raw.get("verdict", "APPROVED")).upper(),
        )

    def category_breakdown(self) -> str:
        return f"VQ: {self.vq}/30 | DE: {self.de}/20 | SC: {self.sc}/15 | DQ: {self.dq}/15 | CQ: {self.cq}/10 | LM: {self.lm}/10"
