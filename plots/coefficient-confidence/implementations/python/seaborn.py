""" anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SIGNIFICANT_COLOR = IMPRINT_PALETTE[0]  # brand green
NEUTRAL_COLOR = INK_SOFT  # adaptive neutral for non-significant

# Library setup
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Column constants
VARIABLE = "Predictor Variable"  # role: variable
COEFFICIENT = "Coefficient Estimate (Standardized)"  # role: coefficient
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
SIGNIFICANT = "Significant"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
# Regression coefficients from a housing price prediction model
variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Age of Home (years)",
    "Distance to Downtown",
    "School Rating",
    "Crime Rate Index",
    "Garage Spaces",
    "Has Pool",
    "Renovated Recently",
    "Neighborhood Tier",
]
coefficients = np.array([0.45, 0.12, 0.18, 0.08, -0.15, -0.22, 0.25, -0.31, 0.09, 0.14, 0.11, 0.28])
ci_widths = np.array([0.08, 0.15, 0.12, 0.18, 0.09, 0.14, 0.11, 0.16, 0.20, 0.13, 0.22, 0.10])
df = pd.DataFrame(
    {
        VARIABLE: variables,
        COEFFICIENT: coefficients,
        CI_LOWER: coefficients - ci_widths,
        CI_UPPER: coefficients + ci_widths,
    }
)
df[SIGNIFICANT] = (df[CI_LOWER] > 0) | (df[CI_UPPER] < 0)

# Plot
# Order by coefficient so the largest effect sits at the top
df = df.sort_values(COEFFICIENT, ascending=True).reset_index(drop=True)
df["row"] = np.arange(len(df))
point_colors = {True: SIGNIFICANT_COLOR, False: NEUTRAL_COLOR}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Confidence-interval bars, one per row, colored by significance
ax.hlines(
    y=df["row"],
    xmin=df[CI_LOWER],
    xmax=df[CI_UPPER],
    colors=df[SIGNIFICANT].map(point_colors).tolist(),
    linewidth=1.8,
    alpha=0.7,
)

# Point estimates
sns.scatterplot(
    data=df,
    x=COEFFICIENT,
    y="row",
    hue=SIGNIFICANT,
    hue_order=[False, True],
    palette=point_colors,
    s=110,
    ax=ax,
    zorder=5,
)

# Zero reference line
ax.axvline(x=0, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.6, zorder=1)

ax.set_yticks(df["row"], df[VARIABLE])
ax.set_ylim(-0.7, len(df) - 0.3)
ax.set_xlabel(COEFFICIENT, fontsize=10, color=INK)
ax.set_ylabel(VARIABLE, fontsize=10, color=INK)
ax.set_title("coefficient-confidence · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, axis="x", alpha=0.10, linewidth=0.6, color=INK)

# Legend: hue_order is [False, True]
handles, _ = ax.get_legend_handles_labels()
ax.legend(
    handles, ["CI includes zero", "CI excludes zero (significant)"], fontsize=8, loc="lower right", framealpha=0.95
)

fig.subplots_adjust(left=0.22, right=0.97, top=0.92, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
