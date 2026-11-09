"""Set v4 of the review retest: the catalogue audit's implementations before their fixes.

The label patterns are checked against what the stored reviews of those
implementations wrote at the pinned commits: a stand-in's pattern matches the
line in which the live review named the stand-in, and no pattern takes praise,
a suggestion, or a remark about something else for a catch. A pattern is
matched against every weakness line of a run, not only the lines of its own
criteria, so a word that also fits an unrelated defect line is a false catch.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import review_retest as rt


REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST = REPO_ROOT / "automation" / "retest" / "set-v4.yaml"
PASS_1 = "586d4242432491519c5bd0f5dda62f35471b31a1"
PASS_2 = "473023d4fa28ccfd1f6a8ce6f718720f5313a7e0"


@functools.cache
def _manifest() -> dict[str, Any]:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def _label(item_id: str, label_id: str) -> dict[str, Any]:
    item = next(i for i in _manifest()["items"] if i["id"] == item_id)
    return next(lab for lab in [*(item.get("defects") or []), *(item.get("permitted") or [])] if lab["id"] == label_id)


def _matches(item_id: str, label_id: str, text: str) -> bool:
    return bool(re.compile(_label(item_id, label_id)["match"], re.IGNORECASE).search(text))


def test_manifest_is_valid_and_draft():
    manifest = _manifest()
    assert rt.validate_manifest(manifest) == []
    assert manifest["labels"] == "draft"  # the owner confirms them once
    assert len(manifest["items"]) == 28
    assert {i["kind"] for i in manifest["items"]} == {"fresh"}


def test_pins_are_the_two_snapshot_passes():
    """Every item pins main at one of the snapshot's passes, whose plots/ trees are equal."""
    for item in _manifest()["items"]:
        render = item["new"]["render"]
        if render == "production":
            assert item["id"] == "f-bar-3d-categorical-plotnine"
            assert item["new"]["commit"] == PASS_1
            continue
        group, spec = render["snapshot"].split("/")
        assert spec == item["spec_id"]
        assert item["new"]["commit"] == {"run1": PASS_1, "run2": PASS_2}[group]


@pytest.mark.parametrize(
    ("item_id", "label_id", "text"),
    [
        (
            "f-surface-basic-highcharts",
            "D1",
            "No true 3D surface or interactive rotation, as the code comments document",
        ),
        (
            "f-scatter-3d-echarts",
            "D1",
            "a subtle floor/backplane grid would reduce visual similarity to a ternary layout",
        ),
        ("f-strip-basic-d3", "D1", "the spec explicitly distinguishes strip plots (random jitter) from swarm plots"),
        (
            "f-windrose-basic-pygal",
            "D1",
            "so the result reads more like a star/radar chart than the polar stacked histogram",
        ),
        (
            "f-errorbar-basic-plotnine",
            "D1",
            "geom_crossbar renders a rectangular box rather than the canonical point-plus-whisker",
        ),
        (
            "f-sequence-logo-basic-altair",
            "D1",
            "Letter glyphs are sized proportionally via font-size but do not physically stretch",
        ),
        ("f-acf-pacf-pygal", "D1", "Filled bars (pygal.Bar) instead of vertical stem lines"),
        (
            "f-choropleth-basic-makie",
            "D1",
            "Tile-grid layout remains a schematic substitute for true geographic polygon boundaries",
        ),
        (
            "f-map-tile-background-plotnine",
            "D1",
            "Map with tile-style background implemented using geom_rect simulation",
        ),
        ("f-cartogram-area-distortion-ggplot2", "D1", "Northeast cluster creates unavoidable circle overlap"),
        (
            "f-line-timeseries-pygal",
            "D1",
            "SC-02 (light): show_x_guides draws a dashed vertical guide for each of the 365 daily x labels",
        ),
        ("f-parliament-basic-pygal", "D1", "SC-02, VQ-05 (both): the arcs form an ellipse about 13 % wider than tall"),
        (
            "f-scatter-connected-temporal-pygal",
            "D2",
            "SC-03 (both): the '● 2023' end label draws a solid ink-colored dot",
        ),
        (
            "f-sequence-logo-basic-altair",
            "D2",
            "VQ-01 (dark): the axis titles and tick labels are pure black on #1A1A17",
        ),
        (
            "f-flowmap-origin-destination-ggplot2",
            "D1",
            "VQ-03 (dark): the Flow legend keys are near-black on the #242420 legend box",
        ),
    ],
)
def test_a_named_defect_matches(item_id, label_id, text):
    assert _matches(item_id, label_id, text)


@pytest.mark.parametrize(
    ("item_id", "label_id", "text"),
    [
        # Praise in a deducted DE-03 comment is no catch of the variant creep.
        (
            "f-sequence-logo-basic-altair",
            "D3",
            "Clear visual hierarchy: core region shading + opacity contrast draws eye to the motif.",
        ),
        # A suggestion to thin the line further names the opposite of the dark-render defect.
        (
            "f-line-3d-trajectory-pygal",
            "D1",
            "strands hard to separate -- could push alpha lower (e.g. 0.5-0.6) or thin the line width",
        ),
        ("f-line-3d-trajectory-pygal", "D2", "the tightly-wound coil regions still show some overlapping strands"),
        (
            "f-spiral-timeseries-pygal",
            "D2",
            "pygal-distinctive features are used only moderately (hover tooltips, dashed guides)",
        ),
        # The F102 defect is labels far from their markers; the live review only flagged the edge.
        (
            "f-map-tile-background-plotnine",
            "D2",
            "Union Square label nudge_x=0.025 lands very close to right coord boundary",
        ),
        (
            "f-scatter-connected-temporal-pygal",
            "D2",
            "'2010' and the '▶' glyph touch the path → every year label clear of the path",
        ),
        # The spec accepts Dorling circles: calling them Dorling names no stand-in.
        (
            "f-cartogram-area-distortion-altair",
            "D1",
            "Dorling cartogram (circles at centroids) diverges from the contiguous type",
        ),
        ("f-windrose-basic-pygal", "D1", "Suggestion: a radar fill would read softer at 0.8 opacity"),
    ],
)
def test_no_catch_on_praise_suggestion_or_another_defect(item_id, label_id, text):
    assert not _matches(item_id, label_id, text)


def test_the_live_false_alarm_fires_the_probe():
    """The live flamegraph review read the share-driven heat ramp as a hot path (F196, refuted)."""
    line = (
        "SC-01 (both): the fill is a heat channel driven by each frame's sample share, which paints "
        "the hot path main → handle_business_logic → fetch_orders → db_query in red and orange"
    )
    assert _matches("f-flamegraph-basic-muix", "A1", line)


def test_control_probes_stay_quiet_on_praise():
    assert not _matches("f-bar-3d-categorical-plotnine", "A1", "Hand-projected isometric 3D bars on a base-plane grid")
    assert not _matches("f-scatter-map-geographic-muix", "A1", "Real coastlines in an equirectangular projection")
    assert not _matches(
        "f-contour-3d-muix", "A2", "Dark render: all text readable, no dark-on-dark failures on any element"
    )
    assert _matches("f-contour-3d-muix", "A2", "VQ-01 (dark): the axis ticks are dark-on-dark and unreadable")


@pytest.mark.parametrize(
    ("item_id", "label_id", "text"),
    [
        ("f-line-3d-trajectory-pygal", "D3", "VQ-05 (both): the landscape orientation leaves wide side margins"),
        ("f-parliament-basic-pygal", "D1", "VQ-05 (both): the 16:9 aspect leaves balanced margins around the dome"),
        ("f-acf-pacf-pygal", "D1", "CQ-01 (code): the pygal.Bar config dict repeats the Style per panel"),
        (
            "f-sequence-logo-basic-altair",
            "D1",
            "VQ-01 (both): the tick label font size is 10 px, below the 12 px minimum",
        ),
        ("f-surface-basic-highcharts", "D2", "VQ-01 (both): the title descenders render crisply at 66 px"),
        (
            "f-flowmap-origin-destination-ggplot2",
            "D1",
            "VQ-07 (dark): legend keys keep strong contrast; the title is grey",
        ),
        (
            "f-map-tile-background-ggplot2",
            "D1",
            "SC-02 (both): polygon outlines of the land are accurate but the labels are small",
        ),
        ("f-windrose-basic-pygal", "D1", "SC-04 (both): the legend sector polygons are styled like the data"),
        ("f-scatter-connected-temporal-pygal", "D1", "SC-04 (both): the legend labels touch their swatches"),
        ("f-flowmap-origin-destination-ggplot2", "D3", "SC-04 (both): the legend labels overlap the legend frame"),
    ],
)
def test_no_catch_on_an_unrelated_defect_line(item_id, label_id, text):
    assert not _matches(item_id, label_id, text)
