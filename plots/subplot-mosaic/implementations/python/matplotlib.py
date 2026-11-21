"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MOSAIC = """
AAB
AAB
CDE
"""  # A spans 2x2 cells, B spans 2 rows, C, D and E fill the bottom row

# Columns: set these to your table's column names; panels of different length share one table, padded with NaN
DAY = "Day"  # role: x
SALES = "Cumulative Sales ($)"  # role: y
PRODUCT = "Product"  # role: extra
UNITS = "Units Sold"  # role: extra
FEATURE_X = "Feature X"  # role: extra
FEATURE_Y = "Feature Y"  # role: extra
MEASUREMENT = "Value"  # role: extra
METRIC = "Metric"  # role: extra
METRIC_VALUE = "Metric value (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("dashboard.csv")
np.random.seed(42)
sales = np.cumsum(np.random.randn(100) * 5 + 2) + 500
feature_x = np.random.normal(50, 15, 80)
feature_y = feature_x * 0.8 + np.random.normal(0, 10, 80)
measurements = np.random.normal(100, 20, 200)
df = pd.DataFrame(
    {
        DAY: pd.Series(np.arange(100)),
        SALES: pd.Series(sales),
        PRODUCT: pd.Series(["Product A", "Product B", "Product C", "Product D"]),
        UNITS: pd.Series([85, 120, 95, 110]),
        FEATURE_X: pd.Series(feature_x),
        FEATURE_Y: pd.Series(feature_y),
        MEASUREMENT: pd.Series(measurements),
        METRIC: pd.Series(["Growth", "Conversion", "Retention"]),
        METRIC_VALUE: pd.Series([12.5, 3.2, 87.4]),
    }
)

# Plot: every panel reads its own columns of df
fig, axes = plt.subplot_mosaic(
    MOSAIC, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, gridspec_kw={"height_ratios": [1, 1, 1.2]}
)
panel_axes = list(axes.values())
for ax in panel_axes:
    ax.set_facecolor(PAGE_BG)
    ax.tick_params(axis="both", colors=INK_SOFT)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(INK_SOFT)
    ax.set_axisbelow(True)

# A: main time series, the largest panel
ax = axes["A"]
series = df[[DAY, SALES]].dropna()
ax.plot(series[DAY], series[SALES], linewidth=1.8, color=IMPRINT_PALETTE[0])
ax.fill_between(series[DAY], series[SALES].min(), series[SALES], alpha=0.2, color=IMPRINT_PALETTE[0])
ax.set_title("Sales Overview", fontsize=11, color=INK, fontweight="medium")
ax.set_xlabel(DAY, fontsize=10, color=INK)
ax.set_ylabel(SALES, fontsize=10, color=INK)
ax.tick_params(labelsize=8)
ax.yaxis.grid(True, alpha=0.10, color=INK_SOFT, linewidth=0.5)

# B: horizontal bars with value labels
ax = axes["B"]
bars_df = df[[PRODUCT, UNITS]].dropna()
bars = ax.barh(bars_df[PRODUCT], bars_df[UNITS], color=IMPRINT_PALETTE[0], edgecolor=INK_SOFT, linewidth=0.8)
ax.bar_label(bars, padding=3, fontsize=7, color=INK)
ax.set_xlim(0, bars_df[UNITS].max() * 1.15)
ax.set_title("Product Performance", fontsize=11, color=INK, fontweight="medium")
ax.set_xlabel(UNITS, fontsize=10, color=INK)
ax.tick_params(labelsize=8)
ax.xaxis.grid(True, alpha=0.10, color=INK_SOFT, linewidth=0.5)

# C: scatter
ax = axes["C"]
ax.scatter(df[FEATURE_X], df[FEATURE_Y], s=14, alpha=0.7, color=IMPRINT_PALETTE[1], edgecolors=PAGE_BG, linewidth=0.4)
ax.set_title("Correlation", fontsize=10, color=INK, fontweight="medium")
ax.set_xlabel(FEATURE_X, fontsize=9, color=INK)
ax.set_ylabel(FEATURE_Y, fontsize=9, color=INK)
ax.tick_params(labelsize=7)
ax.grid(True, alpha=0.10, color=INK_SOFT, linewidth=0.5)

# D: histogram
ax = axes["D"]
ax.hist(df[MEASUREMENT].dropna(), bins=20, color=IMPRINT_PALETTE[2], edgecolor=PAGE_BG, linewidth=0.5, alpha=0.8)
ax.set_title("Distribution", fontsize=10, color=INK, fontweight="medium")
ax.set_xlabel(MEASUREMENT, fontsize=9, color=INK)
ax.set_ylabel("Frequency", fontsize=9, color=INK)
ax.tick_params(labelsize=7)
ax.yaxis.grid(True, alpha=0.10, color=INK_SOFT, linewidth=0.5)

# E: key metrics as text tiles inside a framed panel
ax = axes["E"]
tiles = df[[METRIC, METRIC_VALUE]].dropna()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.set_title("Key Metrics", fontsize=10, color=INK, fontweight="medium", pad=10)
slots = (np.arange(len(tiles))[::-1] + 0.5) / len(tiles)
for i, (name, value, slot) in enumerate(zip(tiles[METRIC], tiles[METRIC_VALUE], slots, strict=True)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    ax.text(0.12, slot, name, ha="left", va="center", fontsize=8, color=INK, fontweight="medium")
    ax.text(0.88, slot, f"{value}%", ha="right", va="center", fontsize=11, color=color)
ax.add_patch(plt.Rectangle((0.05, 0.02), 0.9, 0.96, fill=False, edgecolor=INK_SOFT, linewidth=0.8))

fig.suptitle("subplot-mosaic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95))
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
