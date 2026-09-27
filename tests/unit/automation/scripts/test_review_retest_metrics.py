"""Tests for automation.scripts.review_retest_metrics — pure metric functions."""

from __future__ import annotations

import math

import pytest

from automation.scripts import review_retest_metrics as m


def _checklist(**scores: tuple[int, int, str]) -> dict:
    return {cid.replace("_", "-"): {"score": s, "max": mx, "comment": c} for cid, (s, mx, c) in scores.items()}


def _rec(item: str, run: int, score: int, *, kind: str = "fresh", order: str | None = None, **extra) -> dict:
    record = {
        "cell": f"{item}__{order or ''}__r{run}",
        "item": item,
        "kind": kind,
        "order": order,
        "run": run,
        "model": extra.pop("model", "claude-opus-5-5"),
        "ok": True,
        "error_class": "",
        "score_typed": score,
        "checklist_sum": extra.pop("checklist_sum", score),
        "checklist": extra.pop("checklist", {}),
        "weaknesses": extra.pop("weaknesses", []),
        "gate": extra.pop("gate", None),
        "regen": extra.pop("regen", None),
        "cost_usd": extra.pop("cost_usd", 1.0),
        "harness_version": "1",
        "action_sha": "a" * 40,
        "set": "v1",
    }
    record.update(extra)
    return record


class TestStatistics:
    def test_pooled_sd(self):
        # var([1,3]) = 2, var([5,5]) = 0 -> sqrt(1)
        assert m.pooled_sd([[1, 3], [5, 5], [7]]) == pytest.approx(1.0)
        assert m.pooled_sd([[1], [2]]) is None

    def test_flip_rate(self):
        assert m.flip_rate([[90, 90], [88, 90], [70]]) == 0.5
        assert m.flip_rate([[1]]) is None

    def test_bootstrap_is_deterministic(self):
        units = [1.0, 2.0, 3.0, 4.0, 10.0]
        a = m.bootstrap_ci(units, m.mean, seed=7)
        b = m.bootstrap_ci(units, m.mean, seed=7)
        assert a == b
        assert a is not None and a[0] <= m.mean(units) <= a[1]
        assert m.bootstrap_ci([1.0], m.mean) is None


class TestTextHeuristics:
    def test_topics(self):
        assert {"legend", "marker_visibility"} <= m.topics("Size legend circles are invisible in the dark render")
        assert "overlap" in m.topics("Labels overlap the curve")
        assert "displacement" in m.topics("forceCollide moves bubbles off their true value")

    def test_jaccard(self):
        assert m.jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)
        assert m.jaccard(set(), set()) is None
        assert m.mean_pairwise_jaccard([{"a"}, {"a"}, {"b"}]) == pytest.approx(1 / 3)

    def test_criterion_ids(self):
        assert m.review_criterion_ids(["VQ-03: legend invisible", "no id here", "**SC-01** donut"]) == {
            "VQ-03",
            "SC-01",
        }

    def test_add_and_limiting(self):
        assert m.is_add_weakness("Add a subtitle")
        assert m.is_add_weakness("DE-01: consider adding annotations")
        assert not m.is_add_weakness("The legend is small")
        assert m.has_limiting_word("Good, but the legend is small")
        assert not m.has_limiting_word("Excellent execution")

    def test_criteria_ids_are_the_24(self):
        assert len(m.CRITERIA_IDS) == 24
        assert m.CRITERIA_IDS[0] == "VQ-01" and m.CRITERIA_IDS[-1] == "LM-02"


class TestFreshMetrics:
    def test_totals_verdicts_and_criteria(self):
        records = [
            _rec("a", 1, 89, checklist=_checklist(VQ_01=(8, 8, "ok"), VQ_02=(5, 6, "slight overlap"))),
            _rec("a", 2, 91, checklist=_checklist(VQ_01=(7, 8, "Excellent"), VQ_02=(5, 6, "slight overlap"))),
            _rec("b", 1, 80, checklist_sum=82, checklist=_checklist(VQ_01=(8, 8, "ok"))),
            _rec("b", 2, 80, checklist=_checklist(VQ_01=(8, 8, "ok"))),
        ]
        group = m.group_metrics(records, {})
        typed = group["total"]["typed"]
        assert typed["mean"] == pytest.approx(85.0)
        assert typed["sd"] == pytest.approx(math.sqrt((2 + 0) / 2))
        assert group["total"]["typed_ne_sum"] == 0.25
        assert group["verdicts"]["typed"]["straddle"] == 0.5
        assert group["verdicts"]["typed"]["disagreement"] == 0.5
        vq01 = group["criteria"]["VQ-01"]
        assert vq01["at_max"] == 0.75
        assert vq01["flip"] == 0.5
        assert group["weaknesses"]["below_max_without_limiting_word"] == pytest.approx(1 / 3)
        assert group["noisiest_criteria"][0]["id"] == "VQ-01"

    def test_auto_reject_units_are_reported_apart(self):
        records = [_rec("a", 1, 0), _rec("a", 2, 90), _rec("b", 1, 88), _rec("b", 2, 90)]
        total = m.group_metrics(records, {})["total"]
        assert total["auto_reject_units"] == ["a"]
        assert total["typed"]["mean"] == pytest.approx(89.0)

    def test_weakness_agreement(self):
        records = [
            _rec("a", 1, 90, weaknesses=["VQ-03: legend circles invisible", "Add a subtitle"]),
            _rec("a", 2, 90, weaknesses=["VQ-03: size legend glyphs faint"]),
        ]
        w = m.group_metrics(records, {})["weaknesses"]
        assert w["count_mean"] == 1.5
        assert w["id_jaccard"] == 1.0
        assert w["add_share"] == pytest.approx(1 / 3)
        assert 0 < w["topic_jaccard"] <= 1


class TestLabels:
    LABELS = {
        "a": {
            "defects": [{"id": "D1", "criteria": ["VQ-03"], "match": r"legend"}],
            "permitted": [{"id": "A1", "criteria": ["VQ-02"], "match": r"overlap"}],
        }
    }

    def test_defect_hit_needs_deduction_and_match(self):
        label = self.LABELS["a"]["defects"][0]
        caught = _rec("a", 1, 88, checklist=_checklist(VQ_03=(4, 6, "size legend invisible")))
        named_only = _rec("a", 2, 88, weaknesses=["legend invisible"], checklist=_checklist(VQ_03=(6, 6, "fine")))
        deducted_elsewhere = _rec("a", 3, 88, checklist=_checklist(VQ_03=(5, 6, "markers small")))
        assert m.defect_hit(label, caught)
        assert not m.defect_hit(label, named_only)
        assert not m.defect_hit(label, deducted_elsewhere)

    def test_defect_and_probe_rates(self):
        records = [
            _rec("a", 1, 88, weaknesses=["legend invisible"], checklist=_checklist(VQ_03=(4, 6, "x"))),
            _rec("a", 2, 90, weaknesses=["bubbles overlap"], checklist=_checklist(VQ_03=(6, 6, "x"))),
        ]
        d = m.group_metrics(records, self.LABELS)["defects"]
        assert (d["defect_runs"], d["defect_misses"]) == (2, 1)
        assert d["miss_rate"] == 0.5
        assert d["detected_every_run"] == 0.0
        assert d["never_detected"] == []
        assert (d["probe_runs"], d["false_alarms"]) == (2, 1)

    def test_never_detected_is_flagged(self):
        records = [_rec("a", r, 90, checklist=_checklist(VQ_03=(6, 6, "x"))) for r in (1, 2)]
        assert m.group_metrics(records, self.LABELS)["defects"]["never_detected"] == ["a/D1@a"]

    def test_no_labels_means_no_rates(self):
        d = m.group_metrics([_rec("a", 1, 90)], {})["defects"]
        assert d["miss_rate"] is None and d["false_alarm_rate"] is None


def _regen_rec(item: str, order: str, run: int, score: int, prev: int, verdict: str, visible: int = 0) -> dict:
    return _rec(
        item,
        run,
        score,
        kind="regen",
        order=order,
        model="claude-sonnet-5",
        gate={"verdict": verdict, "prev_rescored": prev, "code": "x"},
        regen={"improvements": [{"ref": "new", "what": "x", "where_visible": "legend"}] * visible},
    )


class TestGateMetrics:
    def test_order_bias_sign(self):
        # A blind 90 but re-scored 87 as predecessor; B blind 88, re-scored 85.
        records = [_regen_rec("p", "forward", 1, 90, 85, "merge"), _regen_rec("p", "reversed", 1, 88, 87, "keep")]
        gate = m.group_metrics(records, {})["gate"]
        assert gate["order_bias"] == pytest.approx(((87 - 90) + (85 - 88)) / 2)
        assert gate["order_bias_items"] == 1

    def test_flip_accuracy_and_calibration(self):
        labels = {"p": {"expected": {"forward": "keep", "reversed": "keep"}, "class": "identity"}}
        records = [
            _regen_rec("p", "forward", 1, 90, 90, "keep"),
            _regen_rec("p", "forward", 2, 88, 91, "merge", visible=1),
            _regen_rec("p", "reversed", 1, 90, 90, "keep"),
        ]
        gate = m.group_metrics(records, labels)["gate"]
        assert gate["verdict_flip"] == 1.0  # the forward unit flipped; reversed has one run
        assert gate["accuracy"] == pytest.approx(2 / 3)
        identity = gate["calibration"]["identity"]
        assert identity["below_tolerance"] == pytest.approx(1 / 3)
        assert identity["visible_claims"] == pytest.approx(1 / 3)
        assert gate["calibration"]["near-identical"]["n"] == 0
        assert gate["permission_cited"] is None and gate["permission_cited_n"] == 0  # no regen_counts

    def test_visible_claims_count_only_what_the_gate_counts(self):
        """regen_counts (the gate record's semantics) wins over the raw where_visible count."""
        labels = {"p": {"class": "identity"}}
        cited = _regen_rec("p", "forward", 1, 90, 90, "keep", visible=1)
        cited["regen_counts"] = {"total": 1, "visible": 0, "permission": 1}
        real = _regen_rec("p", "forward", 2, 90, 90, "merge", visible=1)
        real["regen_counts"] = {"total": 1, "visible": 1, "permission": 0}
        gate = m.group_metrics([cited, real], labels)["gate"]
        assert gate["calibration"]["identity"]["visible_claims"] == pytest.approx(1 / 2)
        assert gate["permission_cited"] == pytest.approx(1 / 2)
        assert gate["permission_cited_n"] == 2


class TestArm:
    def test_cells_errors_and_groups(self):
        records = [
            _rec("a", 1, 90),
            _rec("a", 2, 88),
            {**_rec("a", 3, 0), "ok": False, "error_class": "quota", "score_typed": None},
            _regen_rec("p", "forward", 1, 90, 88, "merge"),
        ]
        arm = m.arm_metrics(records, {})
        assert arm["cells"] == {"total": 4, "ok": 3, "errors": {"quota": 1}}
        assert set(arm["groups"]) == {"fresh|claude-opus-5-5", "regen|claude-sonnet-5"}
        assert arm["cost_usd"] == pytest.approx(4.0)

    def test_model_label_never_shows_an_alias_as_an_id(self):
        assert m.model_label({"model": "claude-opus-5-5", "model_alias": "opus"}) == "claude-opus-5-5"
        assert m.model_label({"model": None, "model_alias": "opus"}) == "unresolved (opus)"
        assert m.model_label({"model": "n/a", "model_alias": "sonnet"}) == "unresolved (sonnet)"
        assert m.model_label({"model": ""}) == "unresolved"
        records = [_rec("a", 1, 90), _rec("a", 2, 88, model=None, model_alias="opus")]
        arm = m.arm_metrics(records, {})
        assert set(arm["groups"]) == {"fresh|claude-opus-5-5", "fresh|unresolved (opus)"}
        assert arm["models"] == ["claude-opus-5-5", "unresolved (opus)"]
        assert arm["groups"]["fresh|unresolved (opus)"]["model"] == "unresolved (opus)"


class TestCompare:
    def test_paired_deltas_and_flags(self):
        base = [
            _rec(i, r, s)
            for i, scores in {"a": (88, 92), "b": (80, 84), "c": (90, 90)}.items()
            for r, s in enumerate(scores, 1)
        ]
        cand = [
            {**_rec(i, r, s), "model": "claude-opus-6"}
            for i, scores in {"a": (86, 86), "b": (80, 80), "c": (89, 89)}.items()
            for r, s in enumerate(scores, 1)
        ]
        result = m.compare_arms(base, cand, {})
        fresh = result["kinds"]["fresh"]
        assert fresh["paired_units"] == 3
        assert fresh["delta_mean"] == pytest.approx(((86 - 90) + (80 - 82) + (89 - 90)) / 3)
        assert fresh["delta_sd"] < 0
        assert fresh["delta_mean_ci"] is not None
        assert "model changed" in result["flags"]
        assert not any(f.startswith("noise up") for f in result["flags"])

    def test_noise_up_flag(self):
        base = [_rec(i, r, 90) for i in "abcd" for r in (1, 2)]
        cand = [_rec(i, r, s) for i in "abcd" for r, s in ((1, 84), (2, 94))]
        assert "noise up (fresh)" in m.compare_arms(base, cand, {})["flags"]

    def test_unresolved_models_flag_even_when_the_aliases_match(self):
        base = [_rec(i, r, 90, model=None, model_alias="opus") for i in "ab" for r in (1, 2)]
        cand = [_rec(i, r, 90, model=None, model_alias="opus") for i in "ab" for r in (1, 2)]
        assert "model changed" in m.compare_arms(base, cand, {})["flags"]
        resolved = [_rec(i, r, 90) for i in "ab" for r in (1, 2)]
        assert "model changed" not in m.compare_arms(resolved, resolved, {})["flags"]


class TestGateMonitor:
    def _record(self, i: int, **overrides) -> dict:
        record = {
            "spec": "s",
            "lib": "altair",
            "model": "claude-sonnet-5",
            "prev_model": "claude-sonnet-5",
            "criteria_version": "qc-a.aqr-b.sg-c",
            "prev_criteria_version": "qc-a.aqr-b.sg-c",
            "prev_stored": 92,
            "prev_rescored": 90,
            "new": 90,
            "verdict": "keep",
            "code": "no_visible_improvement",
            "at": f"2026-10-{(i % 28) + 1:02d}T02:00:00Z",
        }
        record.update(overrides)
        return record

    def test_aggregates_and_alarms(self):
        records = [self._record(i) for i in range(20)] + [
            self._record(20 + i, verdict="merge", code="merge", new=93, prev_rescored=91, model="claude-sonnet-6")
            for i in range(10)
        ]

        def comparable(record: dict) -> bool:
            return record["model"] == record["prev_model"]

        report = m.gate_monitor(records, comparable)
        assert report["n"] == 30
        assert report["merge_rate"] == pytest.approx(1 / 3)
        assert report["codes"] == {"no_visible_improvement": 20, "merge": 10}
        assert report["drift_comparable"]["n"] == 20
        assert report["drift_comparable"]["mean"] == pytest.approx(-2.0)
        assert report["margin_within_tolerance"] == pytest.approx(20 / 30)
        assert any("contrast bias" in a for a in report["alarms"])
        assert report["weekly"]

    def test_invalid_json_alarm(self):
        records = [self._record(i, code="regen_json_invalid", prev_rescored=None) for i in range(3)] + [
            self._record(i) for i in range(7)
        ]
        report = m.gate_monitor(records, lambda r: False)
        assert any("regen_json_invalid" in a for a in report["alarms"])

    @staticmethod
    def _improvements(visible: int, permission: int | None, total: int = 2) -> dict:
        counts = {"total": total, "visible": visible, "W": 1, "P": 0, "C": total - 1, "new": 0}
        if permission is not None:
            counts["permission"] = permission
        return counts

    def test_improvements_use_the_gate_counted_semantics(self):
        records = [
            # Permission-only: the gate counted nothing visible and kept.
            self._record(0, improvements=self._improvements(0, 1)),
            self._record(1, verdict="merge", code="merge", improvements=self._improvements(2, 0)),
            # Permission cited next to a counted improvement: merged, not a permission-only keep.
            self._record(2, verdict="merge", code="merge", improvements=self._improvements(1, 1)),
            # A record without the permission key stays out of the permission share.
            self._record(3, improvements=self._improvements(0, None)),
            # The crash fallback's minimal record carries no counts at all.
            self._record(4, code="script_crashed", prev_rescored=None, new=None),
        ]
        imp = m.gate_monitor(records, lambda r: False)["improvements"]
        assert imp["n"] == 4
        assert imp["visible_mean"] == pytest.approx(3 / 4)
        assert imp["with_visible"] == pytest.approx(2 / 4)
        assert (imp["permission_n"], imp["permission_cited"]) == (3, 2)
        assert imp["permission_cited_share"] == pytest.approx(2 / 3)
        assert imp["permission_only_keeps"] == 1

    def test_permission_citation_alarm(self):
        cited = [self._record(i, improvements=self._improvements(0, 1)) for i in range(2)]
        clean = [self._record(10 + i, improvements=self._improvements(0, 0)) for i in range(8)]
        report = m.gate_monitor(cited + clean, lambda r: False)
        assert any("'Expected, not a defect' bullet" in a and "2/10" in a for a in report["alarms"])
        quiet = m.gate_monitor(cited[:1] + clean + clean[:1], lambda r: False)
        assert not any("Expected, not a defect" in a for a in quiet["alarms"])
