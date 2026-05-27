""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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

# Okabe-Ito palette - brand green for boxes, vermillion for strip points
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - product quality scores across manufacturing batches
np.random.seed(42)

# Create groups with different distributions to show boxplot features
batch_a = np.random.normal(75, 8, 40)  # Centered, moderate spread
batch_b = np.random.normal(82, 5, 35)  # Higher center, tight spread
batch_c = np.concatenate(
    [
        np.random.normal(68, 6, 30),  # Main distribution
        [45, 48, 95, 97],  # Outliers
    ]
)
batch_d = np.random.normal(70, 12, 45)  # Wide spread

# Combine into DataFrame
df = pd.DataFrame(
    {
        "Batch": ["Batch A"] * len(batch_a)
        + ["Batch B"] * len(batch_b)
        + ["Batch C"] * len(batch_c)
        + ["Batch D"] * len(batch_d),
        "Quality Score": np.concatenate([batch_a, batch_b, batch_c, batch_d]),
    }
)

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Box plot in brand green
sns.boxplot(data=df, x="Batch", y="Quality Score", color=BRAND, width=0.5, linewidth=2, fliersize=0, ax=ax)

# Strip plot overlay in accent vermillion
sns.stripplot(
    data=df,
    x="Batch",
    y="Quality Score",
    color=ACCENT,
    size=10,
    alpha=0.7,
    jitter=0.2,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    ax=ax,
)

# Style
ax.set_title("cat-box-strip · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.set_xlabel("Manufacturing Batch", fontsize=20, color=INK)
ax.set_ylabel("Quality Score (points)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Y-axis limits with padding
ax.set_ylim(35, 105)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
