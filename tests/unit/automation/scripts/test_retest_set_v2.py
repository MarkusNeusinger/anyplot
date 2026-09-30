"""Set v2 of the review retest: the 12 regen pairs of verification round 1.

The ``fixes`` labels are checked against what round 1's reviews actually wrote
(the gate comments of #11951 to #11963, and the defect / suggestion / obsolete
reading of every cited improvement in plan P3 v2, §8.5): each improvement read
as a fixed defect matches exactly one ``fixes`` label of its pair, and no
suggestion or obsolete improvement matches any. The owner's confirmation moved
two readings: #11953's W1 is a suggestion, and #11960 fixes a defect round 1
did not cite. Replaying round 1 through the metric with the confirmed labels
still gives the plan's baseline: 6 of the 12 forward merges had no carrier
(#11960 among them, since round 1 cited only a suggestion there).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import review_retest as rt
from automation.scripts import review_retest_metrics as metrics


REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST = REPO_ROOT / "automation" / "retest" / "set-v2.yaml"
T0 = "0ccb3fec15888aae4772a7b5c09ea9692f330c22"
AFTER = "28df16aeda6f3ed2c9778053764bc5d88128549d"

# Round 1, from the gate comments: per PR, every cited improvement as
# (ref, class, what, where_visible). The class is plan P3 v2's reading
# (agentic/runs/verify-b1-regens/build.py, KIND).
ROUND1: dict[int, list[tuple[str, str, str, str]]] = {
    11951: [
        (
            "W1",
            "obsolete",
            "Max bubble radius reduced from 21px to 18px, easing overlap severity in the densest funding cluster",
            "densest bubble cluster (high funding, right side of chart), both renders",
        ),
        (
            "W2",
            "suggestion",
            "Legend value label font size increased from 14px to 16px for better balance against axis tick labels",
            "size legend, both renders",
        ),
        (
            "C3",
            "defect",
            "Bubbles now render at their exact (funding, growth) coordinates; the predecessor's d3-force collision "
            "simulation that displaced marks from their true positions has been removed",
            "all bubbles, both renders",
        ),
        (
            "C5",
            "defect",
            "The trend line and annotation callout card, an unasked derived-variable narrative layer not permitted "
            "on the basic variant, have been removed — only x, y, and size are encoded",
            "both renders: no dashed trend line or callout card present",
        ),
    ],
    11952: [
        (
            "W1",
            "obsolete",
            "Anti-overlap threshold tightened (0.9x combined radius / 2+ neighbors -> 1.0x / 1+ neighbor); the "
            "previously near-fused bubble pair is now clearly separated with each bubble's outline visible",
            "growth ~19-24%, revenue ~$100-350M region, both renders",
        )
    ],
    11953: [
        (
            "W1",
            "suggestion",  # the owner's reading at confirmation; the plan read it as a defect
            "Top-seller label offset formula widened (min offset 8→14, price multiplier 0.25→0.34, vjust magnitude "
            "increased) — the BEAU-001 callout now sits clear of the bubble cluster above it instead of touching it",
            "BEAU-001 label, both renders",
        ),
        (
            "W3",
            "defect",
            "Sporting Goods recolored from matte red (#AE3030, the semantic bad/loss/error anchor) to cyan "
            "(#2ABCCD), reserving red for its intended semantic role since no error category exists here",
            "Sporting Goods legend swatch and bubbles, both renders",
        ),
    ],
    11954: [
        (
            "W1",
            "defect",
            "Added an explicit y-axis title ('Number of Responses', fontsize=10, INK color) alongside the existing "
            "x-axis title, so the axis itself communicates that bars represent response counts rather than relying "
            "solely on the direct bar labels.",
            "rotated axis label along the left edge of the plot, both renders",
        )
    ],
    11956: [
        (
            "C4",
            "defect",
            "Removed the disallowed secondary-axis cumulative-% line, 80% threshold annotation and its legend — the "
            "chart is now the basic variant's single categorical series the spec requires",
            "both renders: a single green bar series, no secondary axis, no legend",
        ),
        (
            "W2",
            "suggestion",
            "Tick labels, axis titles and bar labels are modestly larger (12px/14px vs the predecessor's 11px/13px), "
            "adding mobile-width legibility headroom",
            "both renders: x/y tick labels and the count/percentage bar labels",
        ),
    ],
    11957: [
        (
            "W1",
            "suggestion",
            "Mean-reference line and its 'Mean = 91' label recolored from amber to the theme-adaptive ink/neutral "
            "token, so it no longer reads as the same signal type as the amber 'Most common' leader callout",
            "mean line and label, both renders: now dashed gray/ink instead of gold",
        )
    ],
    11958: [
        (
            "W1",
            "suggestion",
            "Design moves beyond generic library defaults: a dashed Control-baseline reference line and an "
            "ink-toned focal highlight replace the flat, undifferentiated bars",
            "all bars and the dashed baseline, both renders",
        ),
        (
            "W2",
            "suggestion",
            "The top-performing variant now reads as a clear focal point via a bolder ink-colored outline, instead "
            "of every bar carrying equal visual weight",
            "Variant C bar outline, both renders",
        ),
        (
            "W4",
            "suggestion",
            "The annotation is now visually emphatic and tied to a computed insight ('+50% vs Control baseline') "
            "with a connector line to the highlighted bar, instead of a plain static caption",
            "annotation box and connector line, both renders",
        ),
        (
            "new",
            "defect",
            "Title now includes the required language segment ('python'), fixing the predecessor's incomplete "
            "title format",
            "title text, both renders",
        ),
        (
            "new",
            "defect",
            "Canvas is the exact canonical 3200×1800 target (predecessor was 4766×2670 due to bbox_inches='tight' "
            "trimming an oversized figure)",
            "overall frame proportions, both renders",
        ),
        (
            "new",
            "defect",
            "The winner highlight uses the ink theme token instead of the predecessor's off-palette vermillion-like "
            "outline, keeping the highlight CVD-safe and palette-compliant",
            "Variant C bar outline color, both renders",
        ),
    ],
    11959: [
        (
            "P1",
            "suggestion",
            "Percentage-of-total annotations now shown beneath each count label",
            "all five bars, both renders",
        ),
        (
            "P2",
            "suggestion",
            'Title now carries the descriptive prefix "Device Type Sessions" ahead of the mandated format',
            "title, both renders",
        ),
        (
            "P3",
            "suggestion",
            "Bars now have a thin page-colored stroke separating them from each other, adding definition",
            "all five bars, both renders",
        ),
    ],
    11960: [
        (
            "W1",
            "suggestion",
            "Axis tick labels now show units directly (' t/ha' suffix via scales::label_number) and the chart "
            "switched to horizontal orientation via coord_flip — both distinctive ggplot2 features the previous "
            "review flagged as missing",
            "x-axis tick labels and bar orientation, both light and dark renders",
        )
    ],
    11961: [
        (
            "W1",
            "defect",
            "All five bars now render in consistent Imprint brand green (#009E73), matching the code — the previous "
            "rainbow color/code mismatch is gone",
            "all bars, both renders",
        ),
        (
            "W2",
            "suggestion",
            "Top and right spines removed via explicit showline/mirror config, leaving a clean L-shaped frame "
            "instead of a full box",
            "chart frame, both renders",
        ),
        (
            "W3",
            "suggestion",
            "Dashed control-baseline reference line with annotation replaces the previous generic look with a "
            "deliberate design/comparison device",
            "dashed line and its annotation, both renders",
        ),
        (
            "W4",
            "suggestion",
            "The control-baseline line creates visual hierarchy, letting the viewer see at a glance which "
            "treatments beat the control",
            "dashed baseline crossing the bars, both renders",
        ),
        (
            "new",
            "defect",
            "Title now includes the previously missing language segment, correctly reading 'bar-error · python · "
            "plotly · anyplot.ai' instead of 'bar-error · plotly · anyplot.ai'",
            "title, both renders",
        ),
    ],
    11962: [
        (
            "W1",
            "suggestion",
            "Title font size increased from 30px to 36px, giving the title noticeably more visual presence",
            "title, both renders",
        )
    ],
    11963: [
        (
            "W1",
            "suggestion",
            "Adds Makie's distinctive `bracket!` curly-brace annotation connecting the top two bars' error-bar caps, "
            "labeled with the actual computed yield gap — a library-specific primitive with no direct "
            "matplotlib/plotly equivalent",
            "bracket annotation above the Pd/C and Pt/C bars, both renders",
        ),
        (
            "W2",
            "suggestion",
            "Error bars are now genuinely asymmetric (16th–84th percentile), derived from a ceiling-compressed "
            "asymmetric mixture model instead of a symmetric ±1 SD",
            "error-bar caps on all 6 bars show visibly unequal upper/lower arms, most pronounced on the Fe bar, "
            "both renders",
        ),
        (
            "W3",
            "suggestion",
            "The top-performing bar (Pd/C) now carries a bold ink-colored outline stroke, giving the focal point a "
            "second visual cue beyond the callout text",
            "Pd/C bar outline vs the other bars' invisible page-colored strokes, both renders",
        ),
    ],
}
# Round 1's merges that rested on no cited fixed defect (plan P3 v2, §8.5). #11960
# is carried under the confirmed labels (F1), but round 1 cited only W1, a
# suggestion, so its replay still finds no carrier.
UNCARRIED = {11952, 11957, 11959, 11962, 11963}
UNCARRIED_IN_REPLAY = UNCARRIED | {11960}
# The retest arms' improvements for #11960 (runs v2-baseline and p3-v2): every
# forward citation of the gridline fix, and the texts around it that are not it.
GRIDLINE_FIX = [
    "Value labels no longer collide with a gridline: in the predecessor the bold '7.0' sat on the topmost "
    "(y = 8) gridline and the rule ran through the digits",
    "The top bar's bold value label no longer sits on a grid line or against the panel ceiling",
    "Value labels moved beside the bar ends, so the bold '7.0' is no longer crossed by a grid line",
    "The bold 7.0 value label no longer has a gridline running through it",
    "Value labels no longer collide with a grid rule: they now sit beside the error-bar caps",
    "The value labels moved off the gridlines: in the predecessor the y=8 gridline ran straight through the "
    "bold 7.0 label",
]
NOT_GRIDLINE_FIX = [
    "Fewer gridlines cross the translucent bars (10 crossings instead of 18), so the alpha-0.6 bar fills read "
    "as solid blocks instead of being banded by bright rules",
    "the value axis now stops just above the tallest upper cap instead of running past a '9 t/ha' tick and "
    "gridline over empty panel, so the bars fill the panel",
]


def _manifest() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data


def _items_by_pr() -> dict[int, dict[str, Any]]:
    return {int(item["id"].rsplit("-pr", 1)[1]): item for item in _manifest()["items"]}


def _cases(kinds: set[str]) -> list[tuple[int, str, str, str]]:
    return [(pr, ref, what, where) for pr, rows in ROUND1.items() for ref, kind, what, where in rows if kind in kinds]


class TestShippedSet:
    def test_valid_and_confirmed(self):
        manifest = _manifest()
        assert rt.validate_manifest(manifest) == []
        assert manifest["labels"] == "confirmed"
        assert manifest["gcs_prefix"] == "retest/sets/v2"
        assert manifest["spec_commit"] == T0
        assert manifest["baseline_rules_sha"].startswith("9a6ed1952")

    def test_the_twelve_round_one_pairs(self):
        items = _items_by_pr()
        assert set(items) == set(ROUND1)  # #11955 is left out
        assert len(items) == 12
        for pr, item in items.items():
            assert item["kind"] == "regen" and item["tier"] == "core" and item["class"] == "different", pr
            assert item["prev"]["commit"] == T0, pr
            assert item["new"]["commit"] == AFTER, pr
            assert item["prev"]["render"]["snapshot"].endswith(f"verify-b1-regens/before/{item['spec_id']}"), pr
            assert item["new"]["render"]["snapshot"].endswith(f"verify-b1-regens/after/{item['spec_id']}"), pr
            assert f"#{pr}" in item["note"]

    def test_expected_verdicts_follow_the_fixes(self):
        """Forward merges exactly where a defect is fixed; every reversed order keeps."""
        for pr, item in _items_by_pr().items():
            assert isinstance(item["fixes"], list), pr
            forward = "merge" if item["fixes"] else "keep"
            assert item["expected"] == {"forward": forward, "reversed": "keep"}, pr
            assert (pr in UNCARRIED) == (not item["fixes"]), pr

    def test_off_canvas_predecessors_run_forward_only(self):
        forward_only = {pr for pr, item in _items_by_pr().items() if item.get("orders") == "forward"}
        assert forward_only == {11958, 11961}

    def test_fixes_name_carrier_criteria_only(self):
        for item in _manifest()["items"]:
            for label in item["fixes"]:
                assert set(label["criteria"]) <= set(metrics.CARRIER_CRITERIA), (item["id"], label["id"])

    def test_draft_labels_never_reach_a_report(self):
        labels = rt.item_labels({**_manifest(), "labels": "draft"})
        assert all(entry["fixes"] is None and entry["expected"] == {} for entry in labels.values())

    def test_confirmed_labels_reach_the_report(self):
        labels = rt.item_labels(_manifest())
        by_pr = {int(item_id.rsplit("-pr", 1)[1]): entry for item_id, entry in labels.items()}
        assert all(isinstance(entry["fixes"], list) for entry in by_pr.values())
        # The owner's corrections.
        assert [f["id"] for f in by_pr[11953]["fixes"]] == ["F2"]
        assert [(f["id"], f["criteria"]) for f in by_pr[11960]["fixes"]] == [("F1", ["VQ-02"])]
        assert by_pr[11963]["fixes"] == [] and by_pr[11963]["expected"]["forward"] == "keep"


class TestFixesAgainstRoundOne:
    @pytest.mark.parametrize(("pr", "ref", "what", "where"), _cases({"defect"}))
    def test_every_fixed_defect_matches_one_label(self, pr, ref, what, where):
        fixes = _items_by_pr()[pr]["fixes"]
        hits = [f["id"] for f in fixes if re.search(f["match"], what, re.IGNORECASE)]
        assert len(hits) == 1, (ref, hits)

    @pytest.mark.parametrize(("pr", "ref", "what", "where"), _cases({"suggestion", "obsolete"}))
    def test_no_suggestion_or_obsolete_text_matches(self, pr, ref, what, where):
        fixes = _items_by_pr()[pr]["fixes"]
        line = f"`{ref}` {what} — {where}"  # the whole gate-comment line, not only `what`
        assert not [f["id"] for f in fixes if re.search(f["match"], line, re.IGNORECASE)]

    def test_round_one_counts(self):
        kinds = [kind for rows in ROUND1.values() for _, kind, _, _ in rows]
        assert (kinds.count("defect"), kinds.count("suggestion"), kinds.count("obsolete")) == (10, 18, 2)

    @pytest.mark.parametrize("what", GRIDLINE_FIX)
    def test_the_gridline_fix_matches(self, what):
        (label,) = _items_by_pr()[11960]["fixes"]
        assert re.search(label["match"], what, re.IGNORECASE)

    @pytest.mark.parametrize("what", NOT_GRIDLINE_FIX)
    def test_other_gridline_texts_do_not_match(self, what):
        (label,) = _items_by_pr()[11960]["fixes"]
        assert not re.search(label["match"], what, re.IGNORECASE)


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
class TestRoundOneReplay:
    """Round 1's forward merges through ``merges_without_carrier``, labels confirmed."""

    @staticmethod
    def _spec(spec_id: str) -> dict[str, Any] | None:
        text = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"{T0}:plots/{spec_id}/specification.md"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return rt.characteristics_summary(text)

    def test_half_of_the_merges_had_no_carrier(self):
        """Round 1 cited no carrier in 6 of 12 merges, #11960 among them."""
        manifest = _manifest()
        items = _items_by_pr()
        specs = {spec: self._spec(spec) for spec in {i["spec_id"] for i in items.values()}}
        # C2 of bubble-basic and C5 of count-basic and bar-error are the permissions.
        assert specs == {
            "bubble-basic": {"count": 5, "permission": ["C2"]},
            "count-basic": {"count": 5, "permission": ["C5"]},
            "bar-error": {"count": 5, "permission": ["C5"]},
        }
        records = [
            {
                "cell": f"{items[pr]['id']}__fwd__r1",
                "item": items[pr]["id"],
                "kind": "regen",
                "order": "forward",
                "run": 1,
                "gate": {"verdict": "merge", "prev_rescored": 80, "code": "merge"},
                "score_typed": 85,
                "regen": {"improvements": [{"ref": r, "what": w, "where_visible": v} for r, _, w, v in rows]},
                "spec_characteristics": specs[items[pr]["spec_id"]],
            }
            for pr, rows in ROUND1.items()
        ]
        gate = metrics.gate_metrics(metrics.by_unit(records), rt.item_labels(manifest))
        assert gate["carrier_units"] == 12
        assert (gate["merges_without_carrier_count"], gate["merges_without_carrier_n"]) == (6, 12)
        uncarried = {
            pr
            for pr, record in zip(ROUND1, records, strict=True)
            if not metrics.carrier_claimed(record, items[pr]["fixes"])
        }
        assert uncarried == UNCARRIED_IN_REPLAY
