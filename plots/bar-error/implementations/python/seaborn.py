"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
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

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # Imprint palette position 1

# Set theme
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
TREATMENT = "Treatment Group"  # role: category
RELIEF = "Symptom Relief (%)"  # role: value
STD_DEV = "Std Dev (±1 SD)"  # role: error

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
df = pd.DataFrame(
    {
        TREATMENT: ["Placebo", "Low Dose", "Medium Dose", "High Dose", "Combined"],
        RELIEF: [25.3, 42.1, 58.7, 71.2, 68.4],
        STD_DEV: [4.2, 5.1, 6.3, 5.8, 6.9],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.barplot(
    data=df, x=TREATMENT, y=RELIEF, color=BRAND, ax=ax, edgecolor=INK_SOFT, linewidth=0.75, width=0.6, saturation=1
)

# Error bars with caps
x_positions = np.arange(len(df))
ax.errorbar(
    x_positions, df[RELIEF], yerr=df[STD_DEV], fmt="none", ecolor=INK_SOFT, elinewidth=1.25, capsize=5, capthick=1.25
)

# Labels and title
ax.set_xlabel(TREATMENT, fontsize=10, color=INK)
ax.set_ylabel(RELIEF, fontsize=10, color=INK)
ax.set_title("bar-error · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Grid (y-axis only)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.4)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Set y-axis limits
ax.set_ylim(0, (df[RELIEF] + df[STD_DEV]).max() * 1.2)

# Add annotation explaining error bars
ax.text(
    0.98,
    0.95,
    "Error bars: ±1 SD",
    transform=ax.transAxes,
    fontsize=7,
    color=INK_SOFT,
    ha="right",
    va="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.4, "alpha": 0.9},
)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
