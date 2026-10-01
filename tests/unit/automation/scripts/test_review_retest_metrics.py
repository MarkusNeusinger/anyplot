"""Tests for automation.scripts.review_retest_metrics — pure metric functions."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from automation.scripts import review_retest_metrics as m


REPO_ROOT = Path(__file__).resolve().parents[4]


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

    def test_pooled_sd_weights_units_by_degrees_of_freedom(self):
        # var([80, 90, 80, 90, 80]) = 30 on 4 df, var([88, 90]) = 2 on 1 df:
        # (4 * 30 + 1 * 2) / (4 + 1) = 24.4, not the unweighted (30 + 2) / 2 = 16.
        assert m.pooled_sd([[80, 90, 80, 90, 80], [88, 90], [70]]) == pytest.approx(math.sqrt(24.4))

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

    def test_add_order_behind_the_defect_prefix(self):
        """P3's defect line: the render tag must not hide an add order; a suggestion is no order."""
        assert m.is_add_weakness("VQ-03 (both): add a size legend → three reference circles. Likely cause: none.")
        assert m.is_add_weakness("VQ-03, SC-04 (both): Include a legend title → 'Revenue'. Likely cause: x.")
        assert not m.is_add_weakness("VQ-03 (both): the legend circles vanish → fill them. Likely cause: guide.")
        assert not m.is_add_weakness("Suggestion: add percentage labels")

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

    def test_totals_pool_unequal_run_counts_by_degrees_of_freedom(self):
        # Unit a kept five runs, unit b lost one of its three to a usage limit.
        records = [_rec("a", r, s) for r, s in enumerate((80, 90, 80, 90, 80), 1)]
        records += [_rec("b", 1, 88), _rec("b", 2, 90)]
        typed = m.group_metrics(records, {})["total"]["typed"]
        assert typed["sd"] == pytest.approx(math.sqrt((4 * 30 + 1 * 2) / 5))
        assert typed["n_units"] == 2

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

    def test_p8_lean_code_labels(self):
        """D2 (acf-pacf/plotly) is caught only by the hand-roll sense of a CQ-04
        deduction, and A2 (network-basic/bokeh) fires on a spring-layout
        hand-roll complaint but not on the item's D1 wording (P8)."""
        manifest = yaml.safe_load((REPO_ROOT / "automation" / "retest" / "set-v1.yaml").read_text())
        items = {item["id"]: item for item in manifest["items"]}
        d2 = next(d for d in items["f-acf-pacf-plotly"]["defects"] if d["id"] == "D2")
        a2 = next(p for p in items["f-network-basic-bokeh"]["permitted"] if p["id"] == "A2")
        deducted = _checklist(CQ_04=(1, 2, "verbose"))
        durbin = "CQ-04 (code): lines 39–60 write out the ACF and a Durbin-Levinson PACF → `acf()`. Likely cause: x."
        d1_wording = "DE-02 (dark): bright white vertical zero-lag line in both panes → a GRID-colored rule."
        assert m.defect_hit(d2, _rec("f-acf-pacf-plotly", 1, 80, weaknesses=[durbin], checklist=deducted))
        assert not m.defect_hit(d2, _rec("f-acf-pacf-plotly", 2, 80, weaknesses=[d1_wording], checklist=deducted))
        assert not m.defect_hit(d2, _rec("f-acf-pacf-plotly", 3, 80, weaknesses=[durbin], checklist={}))
        hand_roll = "CQ-04 (code): spring layout written out by hand → networkx. Likely cause: x."
        labels_far = "VQ-02 (both): the force-directed layout leaves labels far from their nodes → closer."
        assert m.probe_false_alarm(a2, _rec("f-network-basic-bokeh", 1, 80, weaknesses=[hand_roll]))
        assert not m.probe_false_alarm(a2, _rec("f-network-basic-bokeh", 2, 80, weaknesses=[labels_far]))

    # Verbatim criterion comments of the P8 arms (baseline 36782558185 at rules
    # 748d230c9, candidate 36782726606 at d87bcebd4), each on a deducted item.
    @pytest.mark.parametrize(
        ("label_id", "criterion", "comment", "hit"),
        [
            # A2, baseline: the hand-rolled spring layout is blamed (3 of 3).
            (
                "A2",
                "CQ_04",
                "Readable and well commented, but the PIL pad/crop block re-normalises a canvas the CDP viewport pin "
                "already fixes, and the hull computation plus the greedy eight-direction label search stack another "
                "~50 lines on top of the hand-rolled force loop.",
                True,
            ),
            (
                "A2",
                "LM_01",
                "ColumnDataSource, column-driven glyph properties and Legend/LegendItem models are correct bokeh, but "
                "31 individual p.line() calls instead of one multi_line glyph, and a hand-rolled force loop instead of "
                "from_networkx, miss the library's own patterns.",
                True,
            ),
            (
                "A2",
                "CQ_04",
                "About 100 lines of hand-rolled machinery: an O(n^2) force loop, a greedy 8-direction label placer "
                "whose scoring is what detaches the labels, and a pad/crop normalisation that the CDP viewport pin "
                "already makes unreachable.",
                True,
            ),
            # A2, candidate: the comment declines the deduction (0 of 3).
            (
                "A2",
                "CQ_04",
                "Lines 197-203 create one p.line() renderer per edge (31 glyph renderers for a single visual layer) "
                "where two p.multi_line() calls do the same in about four lines. The hand-written spring layout is "
                "not a deduction - networkx is not available.",
                False,
            ),
            (
                "A2",
                "CQ_04",
                "The hand-rolled spring layout is correct and not deducted — networkx is explicitly unavailable, so "
                "no installed call reproduces it. Two leanness issues: 51 one-item glyph renderers (31 p.line, 20 "
                "p.text) where multi_line and a source-driven text do the same, and a 9-line PIL pad/crop pass that "
                "the CDP viewport pin already makes a no-op.",
                False,
            ),
            (
                "A2",
                "CQ_04",
                "Lines 314-322 pad/crop the PNG to a size the CDP viewport pin already guarantees - nine dead lines "
                "plus a mid-module PIL import. The hand-rolled spring layout is not a deduction: networkx is not "
                "available to this environment",
                False,
            ),
            # D2, baseline: the duplication of trace blocks is not the hand-rolled ACF/PACF.
            (
                "D2",
                "CQ_04",
                "The Durbin-Levinson recursion is appropriately compact, but six hand-unrolled add_trace blocks for "
                "the ACF/PACF stems and markers - each behind an if guard that cannot be false for this data - repeat "
                "the same shape roughly 100 lines with no effect on either render.",
                False,
            ),
            (
                "D2",
                "CQ_04",
                "Likely cause: the per-row trace construction written out twice instead of once in a loop.",
                False,
            ),
            # D2, candidate.
            (
                "D2",
                "CQ_04",
                "Lines 39-59 write out the ACF sum and the Durbin-Levinson PACF recursion by hand, ~21 lines that "
                "statsmodels.tsa.stattools.acf/pacf reproduce in two. No fake UI and no over-engineering elsewhere.",
                True,
            ),
        ],
    )
    def test_p8_labels_on_the_arms_own_wording(self, label_id, criterion, comment, hit):
        manifest = yaml.safe_load((REPO_ROOT / "automation" / "retest" / "set-v1.yaml").read_text())
        items = {item["id"]: item for item in manifest["items"]}
        labels = items["f-network-basic-bokeh"]["permitted"] + items["f-acf-pacf-plotly"]["defects"]
        label = next(entry for entry in labels if entry["id"] == label_id and "CQ-04" in entry["criteria"])
        record = _rec("x", 1, 80, checklist=_checklist(**{criterion: (1, 2, comment)}))
        check = m.probe_false_alarm if label_id == "A2" else m.defect_hit
        assert check(label, record) is hit

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

    def test_carrier_claims_and_obsolete_citations(self):
        """P3: on an identity pair a carrier claim is always wrong; older records stay out."""
        labels = {"p": {"class": "identity"}}
        suggestion = _regen_rec("p", "forward", 1, 90, 90, "keep", visible=1)
        suggestion["regen_counts"] = {"total": 2, "visible": 1, "permission": 0, "obsolete": 1, "carriers": 0}
        carrier = _regen_rec("p", "forward", 2, 90, 90, "merge", visible=1)
        carrier["regen_counts"] = {"total": 1, "visible": 1, "permission": 0, "obsolete": 0, "carriers": 1}
        older = _regen_rec("p", "forward", 3, 90, 90, "merge", visible=1)
        older["regen_counts"] = {"total": 1, "visible": 1, "permission": 0}
        gate = m.group_metrics([suggestion, carrier, older], labels)["gate"]
        identity = gate["calibration"]["identity"]
        assert identity["visible_claims"] == pytest.approx(1.0)
        assert identity["carrier_claims"] == pytest.approx(1 / 2)
        assert (gate["obsolete_cited"], gate["obsolete_cited_n"]) == (pytest.approx(1 / 2), 2)

    def test_class_flip(self):
        def run(n: int, classes: dict[str, str] | None) -> dict:
            record = _regen_rec("p", "forward", n, 90, 88, "keep")
            if classes is not None:
                record["regen"]["prev_weaknesses"] = [{"ref": k, "class": v} for k, v in classes.items()]
            return record

        records = [
            run(1, {"W1": "obsolete", "W2": "suggestion", "W3": "defect"}),
            run(2, {"W1": "Obsolete", "w2": "suggestion", "W3": "suggestion"}),
            run(3, {"W1": "obsolete", "W3": "defect"}),  # W2 unclassified: read as a suggestion
            run(4, None),  # older prompts: no classification, not part of the metric
        ]
        gate = m.group_metrics(records, {})["gate"]
        assert (gate["class_flip"], gate["class_flip_n"]) == (pytest.approx(1 / 3), 3)  # W3 flips
        assert m.weakness_classes(records[1]) == {"W1": "obsolete", "W2": "suggestion", "W3": "suggestion"}
        assert m.weakness_classes(run(5, {"W1": "maybe"})) == {"W1": "suggestion"}
        single = m.group_metrics(records[:1], {})["gate"]
        assert (single["class_flip"], single["class_flip_n"]) == (None, 0)


SPEC = {"count": 5, "permission": ["C2"]}
FIXES = [{"id": "F1", "criteria": ["SC-03"], "match": r"force (layout|simulation)"}]


def _imp(ref: str, what: str = "x", where: str = "both renders") -> dict:
    return {"ref": ref, "what": what, "where_visible": where}


def _merge(item: str, run: int, improvements: list, *, order: str = "forward", verdict: str = "merge", spec=SPEC):
    record = _rec(
        item,
        run,
        90,
        kind="regen",
        order=order,
        model="claude-sonnet-5",
        gate={"verdict": verdict, "prev_rescored": 85, "code": "x"},
        regen={"improvements": improvements},
    )
    if spec is not None:
        record["spec_characteristics"] = spec
    return record


class TestMergesWithoutCarrier:
    def test_carrier_criteria_leave_out_de_lm_and_dq01(self):
        assert len(m.CARRIER_CRITERIA) == 18  # 7 VQ + 4 SC + 2 DQ + 5 CQ
        assert not any(c.startswith(("DE", "LM")) for c in m.CARRIER_CRITERIA)
        assert "DQ-01" not in m.CARRIER_CRITERIA

    def test_carrier_criteria_match_the_gate(self):
        from automation.scripts.regen_gate import CARRIER_CRITERIA

        assert set(m.CARRIER_CRITERIA) == CARRIER_CRITERIA

    @pytest.mark.parametrize(
        ("improvements", "fixes", "expected"),
        [
            ([_imp("C3")], [], True),  # an affirmative characteristic
            ([_imp("c3")], [], True),  # the gate coerces c3 -> C3
            ([_imp("C2")], [], False),  # a permission never carries
            ([_imp("C9")], [], False),  # not a bullet of this spec
            ([_imp("W1", "force layout removed")], FIXES, True),  # a labeled fix, whatever its ref
            ([_imp("new", "Force simulation dropped")], FIXES, True),
            ([_imp("W1", "force layout removed", " ")], FIXES, False),  # not visible
            ([_imp("C2", "force layout removed")], FIXES, False),  # a permission, even when the text matches
            ([_imp("W2", "legend font larger"), _imp("P1", "title prefix")], FIXES, False),
            ([], FIXES, False),
        ],
    )
    def test_carrier_claimed(self, improvements, fixes, expected):
        assert m.carrier_claimed(_merge("p", 1, improvements), fixes) is expected

    def test_unknown_characteristics_are_left_out(self):
        assert m.carrier_claimed(_merge("p", 1, [_imp("C3")], spec=None), FIXES) is None
        # An unlabeled section: every bullet reads as affirmative, as the gate reads it.
        assert m.carrier_claimed(_merge("p", 1, [_imp("C2")], spec={"count": 5, "permission": []}), []) is True

    def test_share_of_forward_merges_on_labeled_items(self):
        labels = {"p": {"fixes": FIXES}, "q": {"fixes": None}}
        records = [
            _merge("p", 1, [_imp("W1", "force layout removed")]),  # carried
            _merge("p", 2, [_imp("W2", "legend font larger")]),  # not carried
            _merge("p", 3, [_imp("W2", "legend font larger")], verdict="keep"),  # a keep: not counted
            _merge("p", 4, [_imp("W2", "legend font larger")], spec=None),  # unknown spec: left out
            _merge("p", 1, [_imp("W2", "legend")], order="reversed"),  # reversed: not counted
            _merge("q", 1, [_imp("W2", "legend")]),  # not labeled for carriers
        ]
        gate = m.group_metrics(records, labels)["gate"]
        assert gate["carrier_units"] == 1
        assert (gate["merges_without_carrier_count"], gate["merges_without_carrier_n"]) == (1, 2)
        assert gate["merges_without_carrier"] == pytest.approx(0.5)

    def test_no_labels_no_value(self):
        gate = m.group_metrics([_merge("p", 1, [_imp("W2")])], {})["gate"]
        assert gate["merges_without_carrier"] is None
        assert gate["carrier_units"] == 0 and gate["merges_without_carrier_n"] == 0


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

    def test_delta_sd_pools_unequal_run_counts_by_degrees_of_freedom(self):
        base = [_rec("a", r, s) for r, s in enumerate((80, 90, 80, 90, 80), 1)]
        base += [_rec("b", 1, 88), _rec("b", 2, 90)]
        cand = [_rec("a", r, 85) for r in range(1, 6)] + [_rec("b", 1, 88), _rec("b", 2, 90)]
        fresh = m.compare_arms(base, cand, {})["kinds"]["fresh"]
        # Candidate (4 * 0 + 1 * 2) / 5, baseline (4 * 30 + 1 * 2) / 5; the
        # unweighted mean of the variances would give sqrt(1) - sqrt(16) = -3.
        assert fresh["delta_sd"] == pytest.approx(math.sqrt(2 / 5) - math.sqrt(122 / 5))
        assert fresh["delta_sd_ci"] is not None

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

    def test_writeback_counts_keeps_only(self):
        """P9b: a keep record's `writeback`; merges and pre-P9b records carry none."""
        records = [
            self._record(0, writeback="opened"),
            self._record(1, writeback="opened"),
            self._record(2, writeback="stale"),
            self._record(3),  # before P9b
            self._record(4, verdict="merge", code="merge"),
        ]
        report = m.gate_monitor(records, lambda r: False)
        assert report["writeback"] == {"n": 3, "counts": {"opened": 2, "stale": 1}}
        assert not report["alarms"]

    def test_code_path_merges(self):
        """P8: a merge with no carrier and a counted code improvement; older records are unknown."""
        records = [
            self._record(0, verdict="merge", code="merge", improvements={"carriers": 0, "code": 1, "visible": 2}),
            self._record(1, verdict="merge", code="merge", improvements={"carriers": 1, "code": 1}),
            self._record(2, improvements={"carriers": 0, "code": 1}),  # a keep (below tolerance)
            self._record(3, verdict="merge", code="merge", improvements={"carriers": 0}),  # before P8
            self._record(4, verdict="merge", code="merge", improvements={"code": 1}),  # no carrier key
        ]
        imp = m.gate_monitor(records, lambda r: False)["improvements"]
        assert (imp["code_path_merges"], imp["code_path_n"]) == (1, 3)

    @pytest.mark.parametrize(("invalid", "alarm"), [(2, True), (1, False)])
    def test_writeback_invalid_alarm(self, invalid, alarm):
        """More than 10 % invalid over at least 10 keeps: the 8b step 5 prompt needs work."""
        records = [self._record(i, writeback="invalid") for i in range(invalid)] + [
            self._record(10 + i, writeback="opened") for i in range(10 - invalid)
        ]
        alarms = m.gate_monitor(records, lambda r: False)["alarms"]
        assert any("review_prev.json invalid in" in a for a in alarms) is alarm

    def test_writeback_alarm_needs_ten_keeps(self):
        records = [self._record(i, writeback="invalid") for i in range(9)]
        assert not any("review_prev.json" in a for a in m.gate_monitor(records, lambda r: False)["alarms"])

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

    @staticmethod
    def _classified(carriers: int = 0, obsolete: int = 0, unverified: int = 0, de_lm: int = 0) -> dict:
        suggestion = unverified + de_lm
        return {
            "total": carriers + suggestion + obsolete,
            "visible": carriers + suggestion,
            "W": 0,
            "P": 0,
            "C": 0,
            "new": 0,
            "permission": 0,
            "obsolete": obsolete,
            "carriers": carriers,
            "suggestion": suggestion,
            "unverified": unverified,
            "de_lm": de_lm,
        }

    def test_carrier_counts(self):
        records = [
            self._record(0, verdict="merge", code="merge", improvements=self._classified(carriers=2, de_lm=1)),
            self._record(1, code="no_defect_improvement", improvements=self._classified(unverified=1)),
            self._record(2, code="no_visible_improvement", improvements=self._classified(obsolete=1)),
            # A record from before P3 stays out of the carrier shares.
            self._record(3, improvements=self._improvements(1, 0)),
        ]
        imp = m.gate_monitor(records, lambda r: False)["improvements"]
        assert imp["carrier_n"] == 3
        assert imp["carriers_mean"] == pytest.approx(2 / 3)
        assert imp["with_carrier"] == pytest.approx(1 / 3)
        assert imp["no_defect_improvement"] == 1
        assert (imp["obsolete_cited"], imp["obsolete_cited_share"]) == (1, pytest.approx(1 / 3))
        assert imp["unverified_share"] == pytest.approx(1 / 3)
        assert imp["de_lm_share"] == pytest.approx(1 / 3)
        assert imp["permission_or_obsolete_cited"] == 1

    def test_obsolete_citations_join_the_permission_alarm(self):
        cited = [self._record(i, improvements=self._classified(obsolete=1)) for i in range(2)]
        clean = [self._record(10 + i, improvements=self._classified(carriers=1)) for i in range(8)]
        report = m.gate_monitor(cited + clean, lambda r: False)
        assert any("or an obsolete weakness" in a and "2/10" in a for a in report["alarms"])

    def test_unverified_alarm(self):
        unverified = [self._record(i, improvements=self._classified(unverified=1)) for i in range(3)]
        clean = [self._record(10 + i, improvements=self._classified(carriers=1, de_lm=1)) for i in range(7)]
        report = m.gate_monitor(unverified + clean, lambda r: False)
        assert any("unverified claim" in a and "30% of 10 decisions" in a for a in report["alarms"])
        quiet = m.gate_monitor(unverified[:2] + clean + clean[:1], lambda r: False)
        assert not any("unverified" in a for a in quiet["alarms"])
        # DE and LM points are normal: no alarm however many.
        de_lm = [self._record(i, improvements=self._classified(de_lm=2)) for i in range(10)]
        assert not m.gate_monitor(de_lm, lambda r: False)["alarms"]

    @classmethod
    def _kinded(
        cls, carriers: int = 0, carriers_pn: int = 0, addition: int = 0, polish: int = 0, no_kind: int = 0
    ) -> dict:
        """A P3.1 record's counts; every carrier is a fix, and a demoted item has its kind (or none)."""
        counts = cls._classified(carriers=carriers)
        suggestion = addition + polish + no_kind
        counts.update(
            {
                "total": carriers + suggestion,
                "visible": carriers + suggestion,
                "suggestion": suggestion,
                "addition": addition,
                "polish": polish,
                "no_kind": no_kind,
                "carriers_pn": carriers_pn,
                "by_kind": {"fix": carriers, "removal": 0, "addition": addition, "polish": polish, "none": no_kind},
            }
        )
        return counts

    def test_kind_shares(self):
        records = [
            self._record(0, verdict="merge", code="merge", improvements=self._kinded(carriers=2, carriers_pn=2)),
            self._record(1, verdict="merge", code="merge", improvements=self._kinded(carriers=2, carriers_pn=1)),
            self._record(2, code="no_defect_improvement", improvements=self._kinded(polish=1, addition=1)),
            self._record(3, code="no_defect_improvement", improvements=self._kinded(no_kind=2)),
            # A P3 record (no kind keys) stays out of the kind shares.
            self._record(4, verdict="merge", code="merge", improvements=self._classified(carriers=1)),
        ]
        # A DQ-01 percentage-label addition: counted as de_lm, but by_kind still names it.
        dq01 = self._kinded()
        dq01.update({"total": 1, "visible": 1, "suggestion": 1, "de_lm": 1})
        dq01["by_kind"] = {**dq01["by_kind"], "addition": 1}
        records.append(self._record(5, code="no_defect_improvement", improvements=dq01))
        imp = m.gate_monitor(records, lambda r: False)["improvements"]
        assert imp["kind_n"] == 5
        assert imp["addition_share"] == pytest.approx(2 / 5)
        assert imp["polish_share"] == pytest.approx(1 / 5)
        assert imp["no_kind_share"] == pytest.approx(1 / 5)
        assert imp["kind_valid_share"] == pytest.approx(7 / 9)
        assert (imp["pn_merge_n"], imp["pn_only_merge_share"]) == (2, pytest.approx(1 / 2))
        assert imp["carrier_n"] == 6

    def test_kind_shares_without_p31_records(self):
        imp = m.gate_monitor([self._record(0, improvements=self._classified(carriers=1))], lambda r: False)[
            "improvements"
        ]
        assert imp["kind_n"] == 0
        for key in ("addition_share", "polish_share", "no_kind_share", "kind_valid_share", "pn_only_merge_share"):
            assert imp[key] is None, key

    def test_no_kind_alarm(self):
        unnamed = [self._record(0, improvements=self._kinded(no_kind=1))]
        clean = [self._record(10 + i, improvements=self._kinded(carriers=1)) for i in range(27)]
        fired = m.gate_monitor(unnamed + clean[:9], lambda r: False)  # 1 of 10 decisions: 10 %
        assert any("without a kind" in a and "10% of 10 decisions" in a for a in fired["alarms"])
        # The unverified alarm never sees a missing kind.
        assert not any("unverified" in a for a in fired["alarms"])
        few = m.gate_monitor(unnamed + clean[:8], lambda r: False)  # 9 decisions
        assert not any("without a kind" in a for a in few["alarms"])
        low = m.gate_monitor(unnamed + clean, lambda r: False)  # 1 of 28 decisions: under 5 %
        assert not any("without a kind" in a for a in low["alarms"])
