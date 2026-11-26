"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
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
from scipy import stats


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BIN_COUNT = 30  # spec Notes: 20-50 bins for 252+ observations
TAIL_SIGMA = 2  # tail regions lie beyond 2 standard deviations
SERIES = ["Returns", "Tail (±2σ)", "Normal dist."]  # legend order: bars, tail bars, fitted curve

DATE = "Date"  # role: date
RETURNS = "Returns (%)"  # role: returns
# Derived columns of the plot tables below
BIN_START = "bin start"  # role: extra
BIN_END = "bin end"  # role: extra
DENSITY = "Density"  # role: extra
SERIES_COL = "Series"  # role: extra
X_COL = "x"  # role: extra
Y_COL = "y"  # role: extra
LABEL = "label"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
n_days = 252
raw_returns = np.random.standard_t(df=5, size=n_days) * 0.015 + 0.0003
# Clip at 1st-99th percentile to remove extreme outliers that compress the main distribution
clipped = np.clip(raw_returns, np.percentile(raw_returns, 1), np.percentile(raw_returns, 99))
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), RETURNS: clipped * 100})

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
returns = df[RETURNS].dropna()
mean_ret = returns.mean()
std_ret = returns.std(ddof=0)
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

hist_values, bin_edges = np.histogram(returns, bins=BIN_COUNT, density=True)
lower_tail = mean_ret - TAIL_SIGMA * std_ret
upper_tail = mean_ret + TAIL_SIGMA * std_ret
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
is_tail = (bin_centers < lower_tail) | (bin_centers > upper_tail)
hist_df = pd.DataFrame(
    {
        BIN_START: bin_edges[:-1],
        BIN_END: bin_edges[1:],
        DENSITY: hist_values,
        SERIES_COL: np.where(is_tail, SERIES[1], SERIES[0]),
    }
)

x_range = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 300)
normal_df = pd.DataFrame({X_COL: x_range, DENSITY: stats.norm.pdf(x_range, mean_ret, std_ret), SERIES_COL: SERIES[2]})

sigma_df = pd.DataFrame({X_COL: [lower_tail, upper_tail]})

stats_text = f"Mean: {mean_ret:.2f}%\nStd Dev: {std_ret:.2f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}"
stats_df = pd.DataFrame({X_COL: [returns.max() - 0.1], Y_COL: [hist_values.max() * 0.95], LABEL: [stats_text]})

title = "histogram-returns-distribution · python · altair · anyplot.ai"

# Shared color scale: explicit domain shows all 3 entries in the legend even
# though the histogram data only contains the first two
color_scale = alt.Scale(domain=SERIES, range=IMPRINT_PALETTE[: len(SERIES)])

histogram = (
    alt.Chart(hist_df)
    .mark_bar(opacity=0.8)
    .encode(
        x=alt.X(BIN_START.translate(ESCAPE), type="quantitative", bin="binned", title=RETURNS),
        x2=alt.X2(BIN_END.translate(ESCAPE)),
        y=alt.Y(DENSITY.translate(ESCAPE), type="quantitative", title=DENSITY),
        color=alt.Color(
            SERIES_COL.translate(ESCAPE),
            type="nominal",
            scale=color_scale,
            legend=alt.Legend(title=None, orient="right", labelFontSize=10, symbolSize=80),
        ),
        tooltip=[
            alt.Tooltip(BIN_START.translate(ESCAPE), type="quantitative", title="Bin start (%)", format=".2f"),
            alt.Tooltip(DENSITY.translate(ESCAPE), type="quantitative", title=DENSITY, format=".4f"),
        ],
    )
)

normal_curve = (
    alt.Chart(normal_df)
    .mark_line(strokeWidth=3, strokeDash=[6, 3])
    .encode(
        x=alt.X(X_COL, type="quantitative"),
        y=alt.Y(DENSITY.translate(ESCAPE), type="quantitative"),
        color=alt.Color(SERIES_COL.translate(ESCAPE), type="nominal", scale=color_scale, legend=None),
    )
)

# Subtle ±2σ reference lines to mark tail cutoffs
sigma_lines = (
    alt.Chart(sigma_df)
    .mark_rule(strokeDash=[4, 4], opacity=0.4, strokeWidth=1.5, color=INK_SOFT)
    .encode(x=alt.X(X_COL, type="quantitative"))
)

stats_annotation = (
    alt.Chart(stats_df)
    .mark_text(align="right", baseline="top", fontSize=13, color=INK_SOFT, lineBreak="\n")
    .encode(
        x=alt.X(X_COL, type="quantitative"), y=alt.Y(Y_COL, type="quantitative"), text=alt.Text(LABEL, type="nominal")
    )
)

chart = (
    alt.layer(histogram, sigma_lines, normal_curve, stats_annotation)
    .properties(
        width=800,
        height=450,
        background=PAGE_BG,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        title=alt.Title(title, fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
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
chart.save(f"plot-{THEME}.html")
