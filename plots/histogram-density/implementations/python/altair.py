""" anyplot.ai
histogram-density: Density Histogram
Library: altair 6.3.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette position 1 for the bars; the density curve uses the theme-adaptive neutral anchor
BRAND = "#009E73"
ANYPLOT_NEUTRAL = INK

# Constants
NUM_BINS = 25
HIST_LABEL = "Histogram (area = 1)"
KDE_LABEL = "Kernel density estimate"

# Columns: set these to your table's column names
REACTION_TIME = "Reaction Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
np.random.seed(42)
baseline_times = np.random.normal(loc=250, scale=30, size=350)
fatigued_times = np.random.normal(loc=380, scale=45, size=150)
df = pd.DataFrame({REACTION_TIME: np.concatenate([baseline_times, fatigued_times])})

# Plot: reads only df and the constants above
values = df[REACTION_TIME].dropna().to_numpy()
density, edges = np.histogram(values, bins=NUM_BINS, density=True)
hist_df = pd.DataFrame({"bin_start": edges[:-1], "bin_end": edges[1:], "density": density})

kde = stats.gaussian_kde(values, bw_method=0.15)
kde_x = np.linspace(edges[0], edges[-1], 300)
kde_df = pd.DataFrame({"x": kde_x, "density": kde(kde_x)})

y_top = max(density.max(), kde_df["density"].max()) * 1.1
x_scale = alt.Scale(domain=[edges[0], edges[-1]], nice=False, zero=False)
y_scale = alt.Scale(domain=[0, y_top], nice=False)
# Each layer gets its own legend so the glyph matches the mark: a square swatch for the bars, a dashed stroke for the curve
hist_color = alt.Color(
    "series:N",
    title=None,
    scale=alt.Scale(domain=[HIST_LABEL], range=[BRAND]),
    legend=alt.Legend(orient="none", legendX=470, legendY=8, symbolType="square", symbolSize=200, symbolOpacity=0.85),
)
kde_dash = alt.StrokeDash(
    "series:N",
    title=None,
    scale=alt.Scale(domain=[KDE_LABEL], range=[[6, 3]]),
    legend=alt.Legend(
        orient="none",
        legendX=470,
        legendY=28,
        symbolType="stroke",
        symbolSize=300,
        symbolStrokeWidth=2.5,
        symbolStrokeColor=ANYPLOT_NEUTRAL,
    ),
)

histogram = (
    alt.Chart(hist_df)
    .transform_calculate(series=f"'{HIST_LABEL}'")
    .mark_rect(opacity=0.85, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        x=alt.X("bin_start", type="quantitative", scale=x_scale, title=REACTION_TIME),
        x2="bin_end",
        y=alt.Y("density", type="quantitative", scale=y_scale, title="Density (probability per ms)"),
        color=hist_color,
        tooltip=[
            alt.Tooltip("bin_start", type="quantitative", title="Bin start", format=".0f"),
            alt.Tooltip("bin_end", type="quantitative", title="Bin end", format=".0f"),
            alt.Tooltip("density", type="quantitative", title="Density", format=".5f"),
        ],
    )
)

kde_line = (
    alt.Chart(kde_df)
    .transform_calculate(series=f"'{KDE_LABEL}'")
    .mark_line(strokeWidth=2.5, color=ANYPLOT_NEUTRAL)
    .encode(
        x=alt.X("x", type="quantitative", scale=x_scale),
        y=alt.Y("density", type="quantitative", scale=y_scale),
        strokeDash=kde_dash,
    )
)

chart = (
    alt.layer(histogram, kde_line)
    .properties(
        width=640,
        height=340,
        background=PAGE_BG,
        padding={"left": 30, "right": 30, "top": 20, "bottom": 20},
        title=alt.Title("histogram-density · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.15,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK)
    .configure_legend(labelFontSize=10, labelColor=INK_SOFT, padding=2)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}×{h}, exceeds target {TW}×{TH}. Shrink width/height.")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
