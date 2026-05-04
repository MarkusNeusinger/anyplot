"""Tests for the regen package's PlanSpec and QualityEval dataclasses."""

from __future__ import annotations

import pytest

from agentic.workflows.modules.regen import PlanSpec, QualityEval


def test_plan_spec_is_frozen():
    from dataclasses import FrozenInstanceError

    spec = PlanSpec(
        spec_id="scatter-basic", title="Basic Scatter", latest_update="2026-01-01T00:00:00Z", libraries=["altair"]
    )
    with pytest.raises(FrozenInstanceError):
        spec.spec_id = "other"  # type: ignore[misc]


def test_quality_eval_from_json_round_trips():
    payload = {
        "score": 87,
        "vq": 30,
        "de": 13,
        "sc": 15,
        "dq": 14,
        "cq": 10,
        "lm": 5,
        "image_description": "A clean scatter plot",
        "strengths": ["clean code"],
        "weaknesses": ["could use color"],
        "criteria_checklist": {"visual_quality": {"score": 30}},
        "verdict": "approved",
    }
    quality = QualityEval.from_json(payload)
    assert quality.score == 87
    assert quality.vq == 30
    assert quality.verdict == "APPROVED"  # normalized to upper
    assert quality.criteria_checklist == {"visual_quality": {"score": 30}}


def test_quality_eval_category_breakdown():
    quality = QualityEval(score=87, vq=30, de=13, sc=15, dq=14, cq=10, lm=5, image_description="")
    line = quality.category_breakdown()
    assert "VQ: 30/30" in line
    assert "DE: 13/20" in line
    assert "LM: 5/10" in line


def test_quality_eval_from_json_missing_required_key():
    with pytest.raises(KeyError):
        QualityEval.from_json({"score": 87})  # missing vq, de, etc.
