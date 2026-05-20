"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: altair | Python 3.13
Quality: 92/100 | Updated: 2026-05-20
"""

import os
import sys


# Prevent altair.py (this file) from shadowing the installed altair package:
# Python puts the script's directory as sys.path[0], so we drop it.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _script_dir]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito 1 — main distribution bars
TAIL_COLOR = "#D55E00"  # Okabe-Ito 2 — tail bars beyond ±2σ
CURVE_COLOR = "#0072B2"  # Okabe-Ito 3 — fitted normal distribution overlay

# Data
np.random.seed(42)
n_days = 252
raw_returns = np.random.standard_t(df=5, size=n_days) * 0.015 + 0.0003
# Clip at 1st–99th percentile to remove extreme outliers that compress the main distribution
returns = np.clip(raw_returns, np.percentile(raw_returns, 1), np.percentile(raw_returns, 99))

mean_ret = np.mean(returns) * 100
std_ret = np.std(returns) * 100
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

df_ret = pd.DataFrame({"returns": returns * 100})

bin_count = 30
hist_values, bin_edges = np.histogram(df_ret["returns"], bins=bin_count, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

hist_df = pd.DataFrame(
    {"bin_center": bin_centers, "density": hist_values, "bin_start": bin_edges[:-1], "bin_end": bin_edges[1:]}
)

lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret
hist_df["is_tail"] = (hist_df["bin_center"] < lower_tail) | (hist_df["bin_center"] > upper_tail)

x_range = np.linspace(df_ret["returns"].min() - 0.5, df_ret["returns"].max() + 0.5, 300)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)
normal_df = pd.DataFrame({"x": x_range, "density": normal_pdf})

stats_text = f"Mean: {mean_ret:.2f}%\nStd Dev: {std_ret:.2f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}"
stats_df = pd.DataFrame({"x": [df_ret["returns"].max() - 0.1], "y": [max(hist_values) * 0.95], "text": [stats_text]})

title = "histogram-returns-distribution · python · altair · anyplot.ai"

# Plot
histogram = (
    alt.Chart(hist_df)
    .mark_bar(opacity=0.8)
    .encode(
        x=alt.X("bin_start:Q", bin="binned", title="Returns (%)"),
        x2="bin_end:Q",
        y=alt.Y("density:Q", title="Density"),
        color=alt.condition(alt.datum.is_tail, alt.value(TAIL_COLOR), alt.value(BRAND)),
        tooltip=[
            alt.Tooltip("bin_center:Q", title="Return (%)", format=".2f"),
            alt.Tooltip("density:Q", title="Density", format=".4f"),
        ],
    )
)

normal_curve = (
    alt.Chart(normal_df)
    .mark_line(color=CURVE_COLOR, strokeWidth=3, strokeDash=[6, 3])
    .encode(x=alt.X("x:Q"), y=alt.Y("density:Q"))
)

stats_annotation = (
    alt.Chart(stats_df)
    .mark_text(align="right", baseline="top", fontSize=11, color=INK_SOFT, lineBreak="\n")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

chart = (
    alt.layer(histogram, normal_curve, stats_annotation)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title(title, fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0, continuousWidth=620, continuousHeight=320)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
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
    _bg_rgb = (250, 248, 241) if THEME == "light" else (26, 26, 23)
    _canvas = Image.new("RGB", (TW, TH), _bg_rgb)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
