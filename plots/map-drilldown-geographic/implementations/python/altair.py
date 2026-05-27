""" anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: altair 6.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-23
"""

import os
import sys


sys.path.pop(0)
import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#AE3030", "#4467A3"]
REGIONS = ["West", "South", "Midwest", "Northeast"]

# Data — US state-level sales ($K), Region → State → City hierarchy
us_states_url = "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json"

states_data = pd.DataFrame(
    {
        "id": [
            1,
            2,
            4,
            5,
            6,
            8,
            9,
            10,
            11,
            12,
            13,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            53,
            54,
            55,
            56,
        ],
        "state": [
            "Alabama",
            "Alaska",
            "Arizona",
            "Arkansas",
            "California",
            "Colorado",
            "Connecticut",
            "Delaware",
            "District of Columbia",
            "Florida",
            "Georgia",
            "Hawaii",
            "Idaho",
            "Illinois",
            "Indiana",
            "Iowa",
            "Kansas",
            "Kentucky",
            "Louisiana",
            "Maine",
            "Maryland",
            "Massachusetts",
            "Michigan",
            "Minnesota",
            "Mississippi",
            "Missouri",
            "Montana",
            "Nebraska",
            "Nevada",
            "New Hampshire",
            "New Jersey",
            "New Mexico",
            "New York",
            "North Carolina",
            "North Dakota",
            "Ohio",
            "Oklahoma",
            "Oregon",
            "Pennsylvania",
            "Rhode Island",
            "South Carolina",
            "South Dakota",
            "Tennessee",
            "Texas",
            "Utah",
            "Vermont",
            "Virginia",
            "Washington",
            "West Virginia",
            "Wisconsin",
            "Wyoming",
        ],
        "value": [
            145,
            78,
            210,
            98,
            520,
            185,
            165,
            72,
            95,
            380,
            275,
            88,
            62,
            310,
            155,
            92,
            88,
            125,
            142,
            48,
            195,
            225,
            245,
            168,
            85,
            155,
            45,
            68,
            175,
            52,
            285,
            78,
            425,
            265,
            35,
            295,
            112,
            145,
            320,
            42,
            135,
            38,
            195,
            485,
            95,
            28,
            255,
            215,
            58,
            165,
            25,
        ],
        "region": [
            "South",
            "West",
            "West",
            "South",
            "West",
            "West",
            "Northeast",
            "South",
            "South",
            "South",
            "South",
            "West",
            "West",
            "Midwest",
            "Midwest",
            "Midwest",
            "Midwest",
            "South",
            "South",
            "Northeast",
            "South",
            "Northeast",
            "Midwest",
            "Midwest",
            "South",
            "Midwest",
            "West",
            "Midwest",
            "West",
            "Northeast",
            "Northeast",
            "West",
            "Northeast",
            "South",
            "Midwest",
            "Midwest",
            "South",
            "West",
            "Northeast",
            "Northeast",
            "South",
            "Midwest",
            "South",
            "South",
            "West",
            "Northeast",
            "South",
            "West",
            "South",
            "Midwest",
            "West",
        ],
    }
)

# City-level sales data (level 3 leaf nodes — CA, TX, NY, FL only)
cities_data = pd.DataFrame(
    {
        "state": [
            "California",
            "California",
            "California",
            "California",
            "California",
            "Texas",
            "Texas",
            "Texas",
            "Texas",
            "New York",
            "New York",
            "New York",
            "Florida",
            "Florida",
            "Florida",
        ],
        "city": [
            "Los Angeles",
            "San Francisco",
            "San Diego",
            "San Jose",
            "Sacramento",
            "Houston",
            "Dallas",
            "Austin",
            "San Antonio",
            "New York City",
            "Buffalo",
            "Albany",
            "Miami",
            "Tampa",
            "Orlando",
        ],
        "value": [182, 148, 96, 58, 36, 188, 148, 105, 44, 335, 62, 28, 182, 124, 74],
    }
)

# Region aggregation (level 1 → 2 rollup)
region_data = (
    states_data.groupby("region").agg(total_value=("value", "sum"), num_states=("state", "count")).reset_index()
)

# Interactive selections — defaults produce a meaningful static PNG; clickable in HTML
region_select = alt.selection_point(fields=["region"], name="region_drill", value=[{"region": "West"}])
state_select = alt.selection_point(fields=["state"], name="state_drill", value=[{"state": "California"}])

# Choropleth map — states colored by sales value using anyplot_seq colormap
states_map = alt.topo_feature(us_states_url, "states")

choropleth = (
    alt.Chart(states_map)
    .mark_geoshape(stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(range=["#009E73", "#003D94"], domain=[0, 550]),
            legend=alt.Legend(
                title="Sales ($K)",
                titleFontSize=12,
                labelFontSize=10,
                orient="bottom-left",
                gradientLength=130,
                gradientThickness=12,
                offset=8,
                titleColor=INK,
                labelColor=INK_SOFT,
            ),
        ),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("value:Q", title="Sales ($K)", format=",.0f"),
        ],
    )
    .transform_lookup(lookup="id", from_=alt.LookupData(states_data, "id", ["state", "value", "region"]))
    .project(type="albersUsa")
    .properties(width=340, height=220)
)

# Region bars — ① Country → Regions (click to drill down)
region_bars = (
    alt.Chart(region_data)
    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
    .encode(
        y=alt.Y("region:N", sort="-x", title=None),
        x=alt.X("total_value:Q", title="Sales ($K)", axis=alt.Axis(grid=True, gridOpacity=0.10)),
        color=alt.Color(
            "region:N",
            scale=alt.Scale(domain=REGIONS, range=IMPRINT),
            legend=alt.Legend(title="Region", titleFontSize=10, labelFontSize=11, orient="right", direction="vertical"),
        ),
        opacity=alt.condition(region_select, alt.value(1.0), alt.value(0.55)),
        tooltip=[
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("total_value:Q", title="Total Sales ($K)", format=",.0f"),
            alt.Tooltip("num_states:Q", title="States"),
        ],
    )
    .add_params(region_select)
    .properties(width=185, height=60, title=alt.Title("① USA → Regions", fontSize=11, color=INK))
)

# State bars — ② Region → States (filtered by selected region via transform_filter)
state_bars = (
    alt.Chart(states_data)
    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
    .encode(
        y=alt.Y("state:N", sort="-x", title=None),
        x=alt.X("value:Q", title="Sales ($K)", axis=alt.Axis(grid=True, gridOpacity=0.10)),
        color=alt.Color("region:N", scale=alt.Scale(domain=REGIONS, range=IMPRINT), legend=None),
        opacity=alt.condition(state_select, alt.value(1.0), alt.value(0.55)),
        tooltip=[
            alt.Tooltip("state:N", title="State"),
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("value:Q", title="Sales ($K)", format=",.0f"),
        ],
    )
    .transform_filter(region_select)
    .add_params(state_select)
    .properties(width=185, height=75, title=alt.Title("② Region → States", fontSize=11, color=INK))
)

# City bars — ③ State → Cities (filtered by selected state; CA, TX, NY, FL have data)
city_bars = (
    alt.Chart(cities_data)
    .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=IMPRINT[0])
    .encode(
        y=alt.Y("city:N", sort="-x", title=None),
        x=alt.X("value:Q", title="Sales ($K)", axis=alt.Axis(grid=True, gridOpacity=0.10)),
        tooltip=[alt.Tooltip("city:N", title="City"), alt.Tooltip("value:Q", title="Sales ($K)", format=",.0f")],
    )
    .transform_filter(state_select)
    .properties(width=185, height=45, title=alt.Title("③ State → Cities", fontSize=11, color=INK))
)

# Breadcrumb showing current drill-down path
breadcrumb_df = pd.DataFrame({"label": ["USA  ▸  West  ▸  California  ▸  Cities"]})
breadcrumb = (
    alt.Chart(breadcrumb_df)
    .mark_text(fontSize=10, align="left", fontWeight="bold", color=INK_SOFT)
    .encode(text="label:N", x=alt.value(2), y=alt.value(10))
    .properties(width=185, height=13)
)

# Note: city drill-down available for CA, TX, NY, FL only
city_note_df = pd.DataFrame({"label": ["City data available for CA · TX · NY · FL only"]})
city_note = (
    alt.Chart(city_note_df)
    .mark_text(fontSize=9, align="left", fontStyle="italic", color=INK_SOFT)
    .encode(text="label:N", x=alt.value(2), y=alt.value(10))
    .properties(width=185, height=10)
)

# Sidebar: breadcrumb + all three hierarchy levels + note
sidebar = alt.vconcat(breadcrumb, region_bars, state_bars, city_bars, city_note, spacing=7).resolve_legend(
    color="independent"
)

# Full chart composition
chart = (
    alt.hconcat(choropleth, sidebar, spacing=22)
    .properties(
        background=PAGE_BG,
        title=alt.Title(
            "map-drilldown-geographic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle=["Hierarchical US Sales: Country → Region → State → City  (click to drill down in HTML)"],
            subtitleFontSize=10,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=11,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad-only to exact 3200×1800 canvas (do NOT crop — AR-09 auto-reject)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML (interactive drill-down works here)
chart.save(f"plot-{THEME}.html")
