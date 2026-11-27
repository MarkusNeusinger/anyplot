"""anyplot.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_GOOD = IMPRINT_PALETTE[0]  # brand green, semantic good/pass
COLOR_BAD = IMPRINT_PALETTE[4]  # matte red, semantic bad/loss/error
COLOR_KS = IMPRINT_PALETTE[2]  # blue, neutral annotation

# Columns: set these to your table's column names (they also name the legend entries)
GOOD = "Good Customers"  # role: sample1
BAD = "Bad Customers"  # role: sample2

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Credit scoring: score distributions of Good vs Bad customers
rng = np.random.default_rng(42)
df = pd.DataFrame({GOOD: rng.normal(loc=620, scale=80, size=300), BAD: rng.normal(loc=480, scale=90, size=300)})

# Plot: reads only df and the constants above
SCORE, ECDF, GROUP = "Credit Score", "Cumulative Proportion", "Group"
samples = {name: np.sort(df[name].dropna().to_numpy()) for name in df.columns}
names = list(samples)

# K-S test
ks_stat, p_value = stats.ks_2samp(samples[names[0]], samples[names[1]])

# ECDF of each sample on the union of both samples' values; the largest gap is the K-S distance
grid = np.union1d(samples[names[0]], samples[names[1]])
at_grid = {name: np.searchsorted(values, grid, side="right") / len(values) for name, values in samples.items()}
max_idx = np.argmax(np.abs(at_grid[names[0]] - at_grid[names[1]]))
ks_x = grid[max_idx]
ecdf_df = pd.concat(
    [
        pd.DataFrame({SCORE: values, ECDF: np.arange(1, len(values) + 1) / len(values), GROUP: name})
        for name, values in samples.items()
    ],
    ignore_index=True,
)

# K-S distance vertical line endpoints
ks_line_df = pd.DataFrame({SCORE: [ks_x, ks_x], ECDF: [at_grid[names[1]][max_idx], at_grid[names[0]][max_idx]]})

# Label just above the lower endpoint, in the gap; text extends left into clear whitespace
ks_label_df = pd.DataFrame({SCORE: [ks_x], ECDF: [ks_line_df[ECDF].min() + 0.05], "label": [f"D = {ks_stat:.3f}"]})

# Color and dash scales, one entry per group in data order
color_scale = alt.Scale(domain=names, range=[COLOR_GOOD, COLOR_BAD])
dash_scale = alt.Scale(domain=names, range=[[1, 0], [8, 4]])

# Title — fontsize scaled to title length (floor: 11px)
title = "ks-test-comparison · python · altair · anyplot.ai"
title_fontsize = round(16 * 67 / len(title)) if len(title) > 67 else 16

subtitle_text = f"K-S Statistic: {ks_stat:.3f}  ·  p = {p_value:.1e}  ·  {' vs. '.join(names)}"

# ECDF step lines with redundant dash encoding for colorblind safety
ecdf_lines = (
    alt.Chart(ecdf_df)
    .mark_line(interpolate="step-after", strokeWidth=3.5)
    .encode(
        x=alt.X(SCORE, type="quantitative", title=SCORE, scale=alt.Scale(nice=True)),
        y=alt.Y(
            ECDF,
            type="quantitative",
            title=ECDF,
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(values=[0, 0.2, 0.4, 0.6, 0.8, 1.0], format=".1f"),
        ),
        color=alt.Color(GROUP, type="nominal", scale=color_scale, legend=alt.Legend(title=None)),
        strokeDash=alt.StrokeDash(GROUP, type="nominal", scale=dash_scale, legend=None),
        tooltip=[
            alt.Tooltip(GROUP, type="nominal"),
            alt.Tooltip(SCORE, type="quantitative", format=".0f"),
            alt.Tooltip(ECDF, type="quantitative", format=".3f"),
        ],
    )
)

# K-S distance vertical line marking maximum divergence
ks_distance = (
    alt.Chart(ks_line_df)
    .mark_line(color=COLOR_KS, strokeWidth=2.5, strokeDash=[6, 4])
    .encode(x=alt.X(SCORE, type="quantitative"), y=alt.Y(ECDF, type="quantitative"))
)

# Endpoint dots on the distance line
ks_dots = (
    alt.Chart(ks_line_df)
    .mark_point(color=COLOR_KS, size=100, filled=True, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(x=alt.X(SCORE, type="quantitative"), y=alt.Y(ECDF, type="quantitative"))
)

# K-S statistic label — right-aligned so text extends left of the KS line into clean whitespace
ks_label = (
    alt.Chart(ks_label_df)
    .mark_text(align="right", dx=-8, fontSize=13, fontWeight="bold", color=INK, font="monospace")
    .encode(x=alt.X(SCORE, type="quantitative"), y=alt.Y(ECDF, type="quantitative"), text="label:N")
)

# Combine layers and apply theme-adaptive chrome
chart = (
    alt.layer(ecdf_lines, ks_distance, ks_dots, ks_label)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            title,
            subtitle=subtitle_text,
            fontSize=title_fontsize,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
            color=INK,
            anchor="start",
            offset=10,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleColor=INK,
        labelColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_axisX(grid=False)
    .configure_legend(
        labelFontSize=10,
        titleFontSize=10,
        symbolSize=200,
        symbolStrokeWidth=3.5,
        orient="top-right",
        padding=10,
        cornerRadius=4,
        strokeColor=INK_SOFT,
        fillColor=ELEVATED_BG,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
)

# Save PNG; the fit autosize lands on 3200×1800, the block pads any shortfall (never crops)
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
