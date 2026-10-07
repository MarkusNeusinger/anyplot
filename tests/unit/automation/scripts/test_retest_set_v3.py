"""Set v3 of the review retest: the 15 first generations of line-tanabe-sugano.

The label patterns are checked against what the live reviews of those pull
requests wrote (#12019 to #12038, 2026-10-01): a defect pattern matches the
lines that named its gap, and a permission probe ignores a ``Suggestion:``
line, which costs no points.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import review_retest as rt
from automation.scripts import review_retest_metrics as metrics


REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST = REPO_ROOT / "automation" / "retest" / "set-v3.yaml"
SNAPSHOT_COMMIT = "cda962dc3bc81d8ac3765ca7509d9980f92f3eb2"
LIVE_SPEC = "ec0619261d5b26a361eb5ba6ac54ba6d7c1a61f3"
# The two configurations with a high-spin/low-spin crossover.
CROSSOVER = {"bokeh", "seaborn"}
LOWEST_ROOT_ONLY = {"pygal", "altair", "makie", "chartjs", "highcharts"}


def _manifest() -> dict[str, Any]:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _items() -> dict[str, dict[str, Any]]:
    return {item["library"]: item for item in _manifest()["items"]}


def _label(library: str, kind: str, label_id: str) -> dict[str, Any]:
    return next(label for label in _items()[library][kind] if label["id"] == label_id)


def _matches(label: dict[str, Any], text: str) -> bool:
    return bool(re.compile(label["match"], re.IGNORECASE).search(text))


def _rec(library: str, weaknesses: list[str], spec_source: str = "pinned", **scores: tuple[int, int]) -> dict:
    return {
        "item": f"f-line-tanabe-sugano-{library}",
        "kind": "fresh",
        "order": None,
        "run": 1,
        "ok": True,
        "score_typed": 88,
        "spec_source": spec_source,
        "weaknesses": weaknesses,
        "checklist": {c.replace("_", "-"): {"score": s, "max": top, "comment": ""} for c, (s, top) in scores.items()},
    }


class TestShippedSet:
    def test_valid_and_confirmed(self):
        manifest = _manifest()
        assert rt.validate_manifest(manifest) == []
        assert manifest["labels"] == "confirmed"
        assert manifest["gcs_prefix"] == "retest/sets/v3"
        assert manifest["spec_commit"] == LIVE_SPEC

    def test_one_fresh_core_item_per_library(self):
        items = _manifest()["items"]
        assert sorted(item["library"] for item in items) == sorted(rt.LIBRARY_LANGUAGE)
        for item in items:
            assert item["id"] == f"f-line-tanabe-sugano-{item['library']}"
            assert (item["kind"], item["tier"], item["spec_id"]) == ("fresh", "core", "line-tanabe-sugano")
            assert item["new"]["commit"] == SNAPSHOT_COMMIT
            assert item["new"]["render"]["snapshot"].endswith("tanabe-firstgen-2026-10-01")
            assert "spec_commit" not in item

    def test_a_core_arm_is_45_sessions(self):
        manifest = _manifest()
        cells = rt.build_cells(manifest, rt.resolve_subset(manifest, "core"), "production", 3, "both")
        assert len(cells) == 45
        assert {cell["model"] for cell in cells} == {"opus"}

    def test_crossover_probe_on_every_configuration_without_one(self):
        for library, item in _items().items():
            probes = [label["id"] for label in item["permitted"]]
            assert ("A1" in probes) == (library not in CROSSOVER), library

    def test_range_probe_on_the_two_files_that_stop_at_30(self):
        with_a2 = {library for library, item in _items().items() if any(p["id"] == "A2" for p in item["permitted"])}
        # Both d⁷ files sample to 30; the letsplot repair extended its range to 40.
        assert with_a2 == {"bokeh", "seaborn"}
        assert _label("bokeh", "permitted", "A2")["match"] == _label("seaborn", "permitted", "A2")["match"]

    def test_lowest_root_defect_needs_the_every_root_spec(self):
        with_d2 = {library for library, item in _items().items() if any(d["id"] == "D2" for d in item["defects"])}
        assert with_d2 == LOWEST_ROOT_ONLY
        for library in LOWEST_ROOT_ONLY:
            assert _label(library, "defects", "D2")["spec_source"] == "rules_ref"

    def test_draft_labels_never_reach_a_report(self):
        labels = rt.item_labels({**_manifest(), "labels": "draft"})
        assert all(entry["defects"] == [] and entry["permitted"] == [] for entry in labels.values())

    def test_confirmed_labels_reach_the_report(self):
        labels = rt.item_labels(_manifest())
        assert [d["id"] for d in labels["f-line-tanabe-sugano-matplotlib"]["defects"]] == ["D1"]
        assert sum(len(entry["permitted"]) for entry in labels.values()) == 15  # 13 × A1, 2 × A2


class TestPatternsAgainstTheLiveReviews:
    @pytest.mark.parametrize(
        "library,line",
        [
            (
                "pygal",
                "DQ-01 (both): only the lowest eigenvalue of each doublet block is drawn (`doublet_e[:, 0]`), so no "
                "pair of same-symmetry doublets is on the chart → add the second branch. Likely cause: x.",
            ),
            (
                "altair",
                "SC-02 (both): the ¹Eg block is a 2×2 but only its lower eigenvalue is drawn → draw both. Likely cause: x.",
            ),
            ("makie", "DQ-01 (both): one root per block is drawn for the singlets → keep every root. Likely cause: x."),
        ],
    )
    def test_lowest_root_lines_match(self, library, line):
        assert _matches(_label(library, "defects", "D2"), line)

    @pytest.mark.parametrize(
        "line",
        [
            "VQ-01 (both): tick labels at size 10 are barely legible → about 12 (+2).",
            # An LM-02 line of another review: "only one" of anything is not a root.
            "LM-02 (code): only one distinctly matplotlib-native technique is used → add a second. Likely cause: x.",
            # The live highcharts wording: a suggestion never catches a defect.
            "Suggestion: `termEnergies` currently returns only the lowest root of each doublet block; exposing "
            "the second root of the ²T₁g or ²T₂g block would show an avoided crossing explicitly.",
        ],
    )
    def test_lowest_root_ignores_other_lines(self, line):
        assert not _matches(_label("pygal", "defects", "D2"), line)

    @pytest.mark.parametrize(
        "line",
        [
            "Suggestion: a d⁶ configuration would additionally exercise the high-spin/low-spin crossover line.",
            "Suggestion: a d⁵–d⁷ configuration would additionally exhibit the crossover line and the kink.",
        ],
    )
    def test_a_crossover_suggestion_is_no_false_alarm(self, line):
        record = _rec("plotly", [line], DQ_01=(6, 6))
        assert not metrics.probe_false_alarm(_label("plotly", "permitted", "A1"), record)

    @pytest.mark.parametrize(
        "comment",
        [
            # SC-02 comments of the live reviews that name the permission itself.
            "arrows miss their curves; crossover line correctly absent for d³",
            "the crossover line is d⁴–d⁷ only, which the characteristic section permits",
            "no crossover line is correct for d²",
            "every Notes bullet met; crossover line and example marker are not required for d³",
            # Comments of arm C3a, deducted for something else.
            "The crossover line is conditional on d⁴–d⁷ and does not apply to d³. Deducted for the label (defect line).",
            "all present; the crossover line is N/A for d8. Deducted for the dropped root (defect line).",
            "The absent high-spin/low-spin crossover is conditional on d⁴–d⁷ and costs nothing.",
            "The absent crossover line is not counted: d8 has no crossover.",
            "correctly no crossover line for d2. One point off: the labels are pushed off their pair.",
            "no crossover line (correct for d3), axes from 0, light grid",
            "labels per curve, avoided crossings preserved, no crossover line needed for d³.",
            # Arm C3b.
            "The crossover line is asked only for d4-d7 and the configuration is d2, so it is not missing.",
        ],
    )
    def test_naming_the_permission_on_a_deducted_criterion_is_no_false_alarm(self, comment):
        record = _rec("muix", [], SC_02=(3, 4))
        record["checklist"]["SC-02"]["comment"] = comment
        assert not metrics.probe_false_alarm(_label("muix", "permitted", "A1"), record)

    @pytest.mark.parametrize(
        "line",
        [
            "SC-02 (both): no vertical line marks the high-spin/low-spin crossover → draw it. Likely cause: x.",
            # Arm B3: a deduction for choosing d² over a configuration with a crossover.
            "DQ-01 (both): d² is the one configuration in which neither signature phenomenon appears — it has "
            "no high-spin/low-spin crossover → a d⁶ configuration shows the crossover line with its kinks.",
        ],
    )
    def test_a_crossover_defect_line_is_a_false_alarm(self, line):
        record = _rec("plotly", [line], SC_02=(3, 4))
        assert metrics.probe_false_alarm(_label("plotly", "permitted", "A1"), record)

    @pytest.mark.parametrize(
        "line",
        [
            "DQ-03 (both): Δ_o/B is sampled only to 30 while the spec's Data bullet asks for 0–40 → extend the "
            "sampling to 40 (+10 x-units). Likely cause: `DELTA_MAX = 30.0` on line 51.",
            "VQ-05 (both): the panel runs to Δ_o/B = 36.5 while the curves stop at 30 → stop the axis line there.",
        ],
    )
    def test_range_lines_match(self, line):
        assert _matches(_label("bokeh", "permitted", "A2"), line)

    @pytest.mark.parametrize(
        "line",
        [
            "Suggestion: extending the sampling from 30 to 40 would cover the spec's whole domain.",
            # Numbers of other reviews that are not the x range.
            "DQ-03 (both): conventional 0–40 / 0–80 ranges, but the y axis starts at 5 → start at 0.",
            "VQ-05 (both): legend breaks (10, 30, 60, 100) crowd the corner → three breaks.",
            "DQ-01 (both): 35 lags in the 30–40 range are too few to show the decay → 60 lags.",
        ],
    )
    def test_other_range_text_is_no_false_alarm(self, line):
        assert not metrics.probe_false_alarm(_label("bokeh", "permitted", "A2"), _rec("bokeh", [line]))

    def test_the_arrowhead_line_matches(self):
        line = (
            "SC-02 (both): the ν₁ and ν₂ transition arrows are drawn at x ± 12 px from the example line but "
            "terminate at each term's energy at the exact Δ_o/B = 24.9, so the ν₁ head pokes about 12 px (0.5 E/B) "
            "above the ⁴T₂g curve and the ν₂ head stops about 12 px short of ⁴T₁g(F)."
        )
        label = _label("muix", "defects", "D1")
        assert metrics.defect_hit(label, _rec("muix", [line], SC_02=(3, 4)))
        suggestion = "Suggestion: the Notes allow a marker with arrows from the ground term up to the excited terms."
        assert not _matches(label, suggestion)

    def test_the_strong_field_value_needs_a_dq03_deduction(self):
        label = _label("matplotlib", "defects", "D1")
        line = "DQ-03 (both): ¹A₁g(G) reaches 29 E/B at Δ_o/B = 40, the check value is 34.6 (−5.6). Likely cause: x."
        assert metrics.defect_hit(label, _rec("matplotlib", [line], DQ_03=(2, 4)))
        # The live review praised the scale at 4/4: a miss.
        assert not metrics.defect_hit(label, _rec("matplotlib", [line], DQ_03=(4, 4)))
        swapped = "DQ-03 (code): the two diagonal entries of the ¹A₁g block are swapped (line 50). Likely cause: x."
        assert metrics.defect_hit(label, _rec("matplotlib", [swapped], DQ_03=(2, 4)))

    @pytest.mark.parametrize(
        "line",
        [
            # A DQ-03 deduction for another reason, next to lines that name a
            # singlet, a bare 28 or 29, or another check value.
            "DQ-01 (both): the ¹A₁g(S) term is dropped from the diagram entirely by the `ENERGY_MAX = 100` filter.",
            "VQ-02 (both): the 28 px de-collision offset pushes two labels apart → 14 px. Likely cause: x.",
            "VQ-05 (both): the plot fills ~28% of canvas width → widen. Likely cause: x.",
            "DQ-03 (both): the crossover check value is missed: 19.0 where the Notes state 21.7 (−2.7).",
            "Suggestion: ¹A₁g(G) should reach 34.9 at the right edge; worth checking the block.",
        ],
    )
    def test_other_lines_do_not_catch_the_strong_field_value(self, line):
        label = _label("matplotlib", "defects", "D1")
        assert not metrics.defect_hit(label, _rec("matplotlib", [line], DQ_03=(2, 4)))


class TestSpecSourceLabels:
    LINE = "DQ-01 (both): only the lowest root of each doublet block is drawn → add the upper root. Likely cause: x."

    def _defects(self, records: list[dict]) -> dict[str, Any]:
        labels = rt.item_labels({**_manifest(), "labels": "confirmed"})
        return metrics.defect_metrics(metrics.by_unit(records), labels)

    def test_a_pinned_arm_does_not_count_the_label(self):
        result = self._defects([_rec("pygal", [], "pinned", DQ_01=(6, 6))])
        assert result["defect_runs"] == 0 and result["never_detected"] == []

    def test_a_rules_ref_arm_counts_it(self):
        caught = _rec("pygal", [self.LINE], "rules_ref", DQ_01=(5, 6))
        missed = {**_rec("pygal", [], "rules_ref", DQ_01=(6, 6)), "run": 2}
        result = self._defects([caught, missed])
        assert (result["defect_runs"], result["defect_misses"]) == (2, 1)

    def test_a_probe_follows_the_same_gate(self):
        labels = {
            "f-line-tanabe-sugano-bokeh": {
                "permitted": [{"id": "A9", "criteria": ["VQ-05"], "match": "tail", "spec_source": "rules_ref"}]
            }
        }
        alarm = "VQ-05 (both): a bare axis tail under the labels → trim. Likely cause: x."
        pinned = metrics.defect_metrics(metrics.by_unit([_rec("bokeh", [alarm], "pinned")]), labels)
        assert (pinned["probe_runs"], pinned["per_probe"]) == (0, {})
        gated = metrics.defect_metrics(metrics.by_unit([_rec("bokeh", [alarm], "rules_ref")]), labels)
        assert (gated["probe_runs"], gated["false_alarms"]) == (1, 1)

    def test_a_comparison_across_spec_sources_is_flagged(self):
        labels = rt.item_labels({**_manifest(), "labels": "confirmed"})

        def arm(spec_source: str) -> list[dict]:
            return [
                {**_rec("pygal", [], spec_source, DQ_01=(6, 6)), "cell": f"c{run}", "run": run, "model": "m"}
                for run in (1, 2)
            ]

        assert "label set differs" in metrics.compare_arms(arm("pinned"), arm("rules_ref"), labels)["flags"]
        assert "label set differs" not in metrics.compare_arms(arm("pinned"), arm("pinned"), labels)["flags"]

    def test_validate_refuses_an_unknown_spec_source(self):
        manifest = _manifest()
        manifest["items"][0]["defects"][0]["spec_source"] = "main"
        assert any("spec_source must be one of pinned, rules_ref" in e for e in rt.validate_manifest(manifest))
