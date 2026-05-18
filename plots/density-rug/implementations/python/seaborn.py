""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Sensor measurement errors (single-peak exponential decay)
np.random.seed(17)
# Most measurements have small errors, few have large errors (exponential distribution)
# This represents measurement precision in scientific instruments
errors = np.random.exponential(scale=15, size=250)
# Add a small noise component to make it slightly more realistic
errors = errors + np.random.normal(0, 2, size=250)
# Clip to realistic bounds (0-80)
errors = np.clip(errors, 0, 80)

# Configure seaborn theme
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
    },
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot KDE with fill
sns.kdeplot(data=errors, ax=ax, fill=True, alpha=0.35, color=BRAND, linewidth=3, bw_adjust=0.9)

# Add rug plot
sns.rugplot(data=errors, ax=ax, color=BRAND, alpha=0.5, height=0.04, linewidth=1.2)

# Styling
ax.set_xlabel("Measurement Error (μm)", fontsize=20, color=INK)
ax.set_ylabel("Density", fontsize=20, color=INK)
ax.set_title("density-rug · Python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid styling (y-axis only, subtle)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
