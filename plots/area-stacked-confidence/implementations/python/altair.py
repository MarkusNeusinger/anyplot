""" anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in stack order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAND_LABEL = "band: 90% interval (symmetric)"  # what the shaded bands represent

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
SOURCE = "Energy source"  # role: category
CONSUMPTION = ["Energy consumption (TWh)"]  # role: y
LOWER = ["Lower bound (TWh)"]  # role: y_lower
UPPER = ["Upper bound (TWh)"]  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
# Rows in stack order: the first source sits on the zero baseline
np.random.seed(42)
quarters = pd.date_range("2020-01-01", periods=20, freq="QE")
solar = np.linspace(50, 150, 20) + np.random.randn(20) * 5
solar_half = np.linspace(10, 30, 20)
wind = np.linspace(80, 130, 20) + np.random.randn(20) * 8
wind_half = np.ones(20) * 20
hydro = np.linspace(120, 125, 20) + np.random.randn(20) * 3
hydro_half = np.ones(20) * 8
df = pd.DataFrame(
    {
        QUARTER: np.tile(quarters, 3),
        SOURCE: np.repeat(["Hydro", "Wind", "Solar"], 20),
        CONSUMPTION[0]: np.concatenate([hydro, wind, solar]),
        LOWER[0]: np.concatenate([hydro - hydro_half, wind - wind_half, solar - solar_half]),
        UPPER[0]: np.concatenate([hydro + hydro_half, wind + wind_half, solar + solar_half]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
VALUE, LOW, HIGH = CONSUMPTION[0], LOWER[0], UPPER[0]
sources = [str(source) for source in df[SOURCE].dropna().unique()]

# Stack each source on the ones listed before it; bands stack the same way so each sits on its own edge
stacked = df.dropna(subset=[SOURCE]).copy()
by_quarter = stacked.groupby(QUARTER, sort=False)
stacked["stack_top"] = by_quarter[VALUE].cumsum()
stacked["stack_base"] = stacked["stack_top"] - stacked[VALUE]
stacked["band_low"] = by_quarter[LOW].cumsum()
stacked["band_high"] = by_quarter[HIGH].cumsum()

x_enc = alt.X(QUARTER.translate(ESCAPE), type="temporal", title=QUARTER, axis=alt.Axis(format="%Y-Q%q", grid=False))
color_enc = alt.Color(
    SOURCE.translate(ESCAPE),
    type="nominal",
    sort=sources,
    scale=alt.Scale(domain=sources, range=IMPRINT_PALETTE),
    legend=alt.Legend(title=[SOURCE, BAND_LABEL], orient="right", symbolType="square", symbolSize=180),
)
base = alt.Chart(stacked).encode(x=x_enc, color=color_enc)

layers = base.mark_area(opacity=0.55, interpolate="monotone").encode(
    y=alt.Y("stack_base", type="quantitative", title=VALUE), y2="stack_top"
)
bands = base.mark_area(opacity=0.3, interpolate="monotone").encode(
    y=alt.Y("band_low", type="quantitative"), y2="band_high"
)
edges = base.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
    y=alt.Y("stack_top", type="quantitative"),
    tooltip=[
        alt.Tooltip(QUARTER.translate(ESCAPE), type="temporal", title=QUARTER, format="%Y-Q%q"),
        alt.Tooltip(SOURCE.translate(ESCAPE), type="nominal", title=SOURCE),
        alt.Tooltip(VALUE.translate(ESCAPE), type="quantitative", title=VALUE, format=".1f"),
        alt.Tooltip(LOW.translate(ESCAPE), type="quantitative", title=LOW, format=".1f"),
        alt.Tooltip(HIGH.translate(ESCAPE), type="quantitative", title=HIGH, format=".1f"),
    ],
)

chart = (
    alt.layer(layers, bands, edges)
    .properties(
        width=530,
        height=340,
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        title=alt.Title(
            "area-stacked-confidence · python · altair · anyplot.ai",
            fontSize=16,
            subtitle="Quarterly renewable energy consumption, stacked by source with 90% prediction intervals",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
            anchor="start",
            offset=12,
        ),
    )
    .interactive()
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        ticks=False,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_axisX(domain=True)
    .configure_title(color=INK)
    .configure_legend(
        labelFontSize=10,
        titleFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        padding=8,
        cornerRadius=3,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
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
chart.save(f"plot-{THEME}.html")
