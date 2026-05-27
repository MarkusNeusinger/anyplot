""" anyplot.ai
map-animated-temporal: Animated Map over Time
Library: altair 6.1.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-27
"""

import json
import os
import sys


# This file is named altair.py; remove its directory from sys.path before
# importing the installed altair package to avoid shadowing it.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


sys.path.insert(0, _here)  # restore for relative-path file saves

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LAND_FILL = "#CCC4B0" if THEME == "light" else "#2D2D29"
OCEAN_FILL = "#E0D8C8" if THEME == "light" else "#1E1E1C"

# Data: synthetic earthquake aftershock sequence (Omori's Law decay)
np.random.seed(42)
lat_center, lon_center = 38.3, 142.4  # Offshore Tohoku
n_days = 30

records = []
for day in range(n_days):
    n_quakes = max(2, int(20 * np.exp(-0.09 * day) + np.random.randint(-2, 3)))
    for _ in range(n_quakes):
        records.append(
            {
                "day": day,
                "day_label": f"Day {day + 1:02d}",
                "lat": lat_center + np.random.normal(0, 0.9),
                "lon": lon_center + np.random.normal(0, 1.3),
                "magnitude": round(np.clip(np.random.exponential(0.9) + 2.0, 2.0, 6.8), 1),
            }
        )

df = pd.DataFrame(records)
df["label"] = df.apply(lambda r: f"M{r.magnitude:.1f} · Day {r.day + 1}", axis=1)

# World country polygons (Vega CDN — standard topo used by all Vega/Altair examples)
world = alt.topo_feature("https://vega.github.io/vega-datasets/data/world-110m.json", "countries")

# Title (scaled for length)
title_str = "Earthquake Aftershock Sequence · map-animated-temporal · python · altair · anyplot.ai"
n = len(title_str)
title_fontsize = max(11, round(16 * (67 / n if n > 67 else 1.0)))

# Play/pause checkbox param
play_param = alt.param(name="playing", value=False, bind=alt.binding_checkbox(name="Play / Pause  "))

# Time slider — default at mid-sequence so PNG shows meaningful data
time_param = alt.param(
    name="selected_day", value=15, bind=alt.binding_range(min=0, max=n_days - 1, step=1, name="Day: ")
)

# Base map layer (land + borders)
base_map = alt.Chart(world).mark_geoshape(fill=LAND_FILL, stroke=INK_MUTED, strokeWidth=0.5)

# Earthquake circles — cumulative up to selected_day
points = (
    alt.Chart(df)
    .mark_circle(opacity=0.72, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size(
            "magnitude:Q",
            scale=alt.Scale(range=[30, 480], domain=[2.0, 7.0]),
            legend=alt.Legend(title="Magnitude", orient="bottom-right", symbolOpacity=0.75),
        ),
        color=alt.Color("magnitude:Q", scale=alt.Scale(range=["#009E73", "#4467A3"]), legend=None),
        tooltip=[
            alt.Tooltip("label:N", title="Event"),
            alt.Tooltip("magnitude:Q", title="Magnitude", format=".1f"),
            alt.Tooltip("lat:Q", title="Latitude", format=".2f"),
            alt.Tooltip("lon:Q", title="Longitude", format=".2f"),
        ],
    )
    .transform_filter("datum.day <= selected_day")
)

# Dynamic timestamp overlay — positioned lower-left of the study area
day_text_layer = (
    alt.Chart(pd.DataFrame([{"lon": 136.5, "lat": 33.5}]))
    .mark_text(align="left", baseline="middle", fontWeight="bold", fontSize=13, color=INK, opacity=0.9)
    .transform_calculate(day_str='"Day " + (selected_day + 1) + " / 30"')
    .encode(longitude="lon:Q", latitude="lat:Q", text="day_str:N")
)

# Compose layers with mercator projection centered on study area
chart = (
    alt.layer(base_map, points, day_text_layer)
    .project(type="mercator", center=[lon_center, lat_center], scale=1400)
    .properties(
        width=600,
        height=310,
        background=PAGE_BG,
        title=alt.TitleParams(
            title_str,
            subtitle="Use slider or Play / Pause to animate cumulative aftershocks",
            subtitleColor=INK_SOFT,
            subtitleFontSize=10,
            fontSize=title_fontsize,
            color=INK,
            anchor="start",
            offset=8,
        ),
    )
    .add_params(time_param, play_param)
    .configure_view(fill=OCEAN_FILL, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
)

# Save PNG (static render — timer param not needed for static snapshot)
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

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

# Inject Vega-Lite timer signal for auto-play in the interactive HTML output
chart_dict = chart.to_dict()
for _param in chart_dict.get("params", []):
    if _param.get("name") == "selected_day":
        _param["on"] = [
            {
                "events": {"type": "timer", "throttle": 800},
                "update": f"playing ? (selected_day + 1) % {n_days} : selected_day",
            }
        ]
        break

_spec = json.dumps(chart_dict)
_html = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<script src='https://cdn.jsdelivr.net/npm/vega@5'></script>"
    "<script src='https://cdn.jsdelivr.net/npm/vega-lite@5'></script>"
    "<script src='https://cdn.jsdelivr.net/npm/vega-embed@6'></script>"
    "</head><body><div id='vis'></div>"
    f"<script>vegaEmbed('#vis',{_spec}).catch(console.error);</script>"
    "</body></html>"
)
with open(f"plot-{THEME}.html", "w") as _f:
    _f.write(_html)
