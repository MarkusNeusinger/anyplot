"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome — Imprint palette
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — position 1 (brand green) is the single measure-bar color
BRAND = "#009E73"

# Qualitative range band shading — neutral grayscale ramp, theme-adaptive, poor -> good
BAND_RAMP = ["#DCDCDC", "#949494"] if THEME == "light" else ["#34342F", "#66665E"]

# Constants
BAND_NAMES = ["Poor", "Satisfactory", "Good"]

# Column constants
METRIC = "Metric"  # role: label
BAND = "Band"  # role: extra
ACTUAL = "Actual (%)"  # role: actual
TARGET = "Target (%)"  # role: target
RANGES = "Band limit (%)"  # role: ranges

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
# One row per metric and band: the band's upper limit, plus the metric's actual and target.
kpis = {
    "Revenue": (92, 85, [40, 70, 100]),
    "Profit Margin": (38, 45, [20, 40, 60]),
    "Customer Growth": (71, 80, [30, 60, 100]),
    "Satisfaction": (84, 90, [50, 75, 100]),
    "On-Time Delivery": (96, 95, [60, 80, 100]),
}
df = pd.DataFrame(
    [
        {METRIC: name, BAND: band, ACTUAL: actual, TARGET: target, RANGES: limit}
        for name, (actual, target, limits) in kpis.items()
        for band, limit in zip(BAND_NAMES, limits, strict=True)
    ]
)

# Plot
bar_height = 0.32
band_height = bar_height * 2.4
x_max = df[RANGES].max()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

metrics = df[METRIC].unique()
band_names = df[BAND].unique()
band_cmap = LinearSegmentedColormap.from_list("bands", BAND_RAMP)
band_colors = [band_cmap(k / max(len(band_names) - 1, 1)) for k in range(len(band_names))]
for y, (_, rows) in enumerate(df.groupby(METRIC, sort=False)):
    # Qualitative range bands, each ending at its threshold
    limits = rows[RANGES].tolist()
    starts = [0, *limits[:-1]]
    for j, (start, end) in enumerate(zip(starts, limits, strict=True)):
        ax.add_patch(
            FancyBboxPatch(
                (start, y - band_height / 2),
                end - start,
                band_height,
                boxstyle="round,pad=0,rounding_size=0.08",
                facecolor=band_colors[j],
                edgecolor="none",
                zorder=1,
            )
        )
    row = rows.iloc[0]

    # Measure bar from zero to the actual value
    ax.add_patch(
        FancyBboxPatch(
            (0, y - bar_height / 2),
            row[ACTUAL],
            bar_height,
            boxstyle="round,pad=0,rounding_size=0.06",
            facecolor=BRAND,
            edgecolor="none",
            zorder=2,
        )
    )

    # Target marker: thin line perpendicular to the bar
    ax.vlines(row[TARGET], y - band_height * 0.425, y + band_height * 0.425, colors=INK, linewidth=2.0, zorder=3)

    # Actual-value label right of the widest band
    ax.text(
        limits[-1] + x_max * 0.02,
        y,
        f"{row[ACTUAL]:g}%",
        va="center",
        ha="left",
        fontsize=8,
        fontweight="bold",
        color=INK,
        zorder=4,
    )

# Metric names beside their bullets
ax.set_yticks(range(len(metrics)), metrics, fontsize=8, fontweight="bold")
ax.tick_params(axis="y", length=0, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_xlabel("Performance (%)", fontsize=10, color=INK)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT, length=0)

title = "bullet-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", pad=12, color=INK)

# Subtle x-axis grid, bottom spine only
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_xlim(0, x_max * 1.15)
ax.set_ylim(len(metrics) - 0.5, -0.5)

# Legend
legend_elements = [
    Patch(facecolor=BRAND, edgecolor="none", label="Actual"),
    Line2D([0], [0], color=INK, linewidth=2.0, label="Target"),
    *[
        Patch(facecolor=c, edgecolor=INK_SOFT, linewidth=0.5, label=n)
        for c, n in zip(band_colors, band_names, strict=True)
    ],
]
leg = ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=5, fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Explicit padding — never bbox_inches="tight" (it trims the canvas)
fig.subplots_adjust(left=0.18, right=0.93, top=0.91, bottom=0.26)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
