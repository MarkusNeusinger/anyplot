""" anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the studies, position 2 sets the pooled diamond apart
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_EFFECT = 0.0  # no difference on the mean-difference scale
Z_95 = 1.959964  # normal quantile behind a 95% confidence interval
MAX_MARKER_AREA = 90  # marker area (pt²) of the heaviest study

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Standardized Mean Difference (95% CI)"  # role: effect_size
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("meta_analysis.csv")
# Meta-analysis of RCTs comparing treatment vs control, ordered chronologically
df = pd.DataFrame(
    {
        STUDY: [
            "Johnson 2018",
            "Smith 2019",
            "Garcia 2020",
            "Williams 2020",
            "Brown 2021",
            "Davis 2021",
            "Miller 2022",
            "Wilson 2022",
            "Anderson 2023",
            "Taylor 2023",
        ],
        EFFECT: [-0.45, -0.32, -0.58, -0.21, -0.67, -0.38, -0.52, -0.29, -0.41, -0.55],
        CI_LOWER: [-0.78, -0.61, -0.95, -0.48, -1.02, -0.69, -0.88, -0.56, -0.72, -0.91],
        CI_UPPER: [-0.12, -0.03, -0.21, 0.06, -0.32, -0.07, -0.16, -0.02, -0.10, -0.19],
        WEIGHT: [8.5, 10.2, 7.8, 11.5, 6.9, 9.3, 8.1, 10.8, 9.7, 7.2],
    }
)

# Plot: reads only df and the constants above
effect = df[EFFECT].astype(float).to_numpy()
lower = df[CI_LOWER].astype(float).to_numpy()
upper = df[CI_UPPER].astype(float).to_numpy()
weight = df[WEIGHT].astype(float).to_numpy()

# Pooled estimate: fixed-effect inverse-variance, standard errors recovered from the 95% CIs
se = (upper - lower) / (2 * Z_95)
valid = np.isfinite(effect) & np.isfinite(se) & (se > 0)
iv_weight = 1 / se[valid] ** 2
pooled = np.sum(iv_weight * effect[valid]) / np.sum(iv_weight)
pooled_se = 1 / np.sqrt(np.sum(iv_weight))
pooled_lower = pooled - Z_95 * pooled_se
pooled_upper = pooled + Z_95 * pooled_se

n_studies = len(df)
y_positions = np.arange(n_studies, 0, -1)
pooled_y = 0
marker_sizes = MAX_MARKER_AREA * weight / np.nanmax(weight)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Null-effect reference line through every row
ax.axvline(x=NULL_EFFECT, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.8, zorder=1)

# Study confidence intervals and weight-sized point estimates
ax.hlines(y=y_positions, xmin=lower, xmax=upper, color=IMPRINT_PALETTE[0], linewidth=1.8, zorder=2)
ax.scatter(
    effect, y_positions, s=marker_sizes, color=IMPRINT_PALETTE[0], edgecolors=ELEVATED_BG, linewidths=0.8, zorder=3
)

# Pooled estimate as a diamond whose tips sit at the pooled CI bounds
diamond_half_height = 0.4
diamond = mpatches.Polygon(
    [
        [pooled, pooled_y + diamond_half_height],
        [pooled_upper, pooled_y],
        [pooled, pooled_y - diamond_half_height],
        [pooled_lower, pooled_y],
    ],
    closed=True,
    facecolor=IMPRINT_PALETTE[1],
    edgecolor=INK_SOFT,
    linewidth=0.8,
    zorder=4,
)
ax.add_patch(diamond)

# Style
ax.set_yticks(np.append(y_positions, pooled_y), list(df[STUDY].astype(str)) + ["Pooled estimate"])
ax.tick_params(axis="y", length=0, labelsize=8, labelcolor=INK_SOFT)
ax.tick_params(axis="x", length=0, labelsize=8, labelcolor=INK_SOFT)
ax.get_yticklabels()[-1].set_fontweight("bold")
ax.get_yticklabels()[-1].set_color(INK)

ax.set_xlabel(EFFECT, fontsize=10, color=INK)
ax.set_title("forest-basic · python · matplotlib · anyplot.ai", fontsize=12, color=INK, fontweight="medium")

x_min = min(np.nanmin(lower), pooled_lower, NULL_EFFECT)
x_max = max(np.nanmax(upper), pooled_upper, NULL_EFFECT)
x_pad = (x_max - x_min) * 0.12
ax.set_xlim(x_min - x_pad, x_max + x_pad)
ax.set_ylim(pooled_y - 0.8, n_studies + 0.8)

ax.grid(True, axis="x", alpha=0.15, linestyle="-", linewidth=0.6, color=INK)
ax.set_axisbelow(True)

for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
