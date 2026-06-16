""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
HISTOGRAM_COLOR = "#009E73"  # Brand green
KDE_COLOR = "#C475FD"  # Vermillion

# Configure seaborn theme with theme-adaptive colors
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

# Data: Test score distribution (quality control scenario)
np.random.seed(42)
# Mix of different student performance patterns
test_scores = np.concatenate(
    [
        np.random.normal(72, 8, 300),  # Most students in 60-85 range
        np.random.normal(92, 5, 80),  # High-performing students
        np.random.normal(45, 10, 40),  # Struggling students
    ]
)
test_scores = np.clip(test_scores, 0, 100)  # Bound to valid range
np.random.shuffle(test_scores)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Histogram with semi-transparent bars
sns.histplot(
    test_scores,
    bins=35,
    kde=False,
    stat="density",
    alpha=0.5,
    color=HISTOGRAM_COLOR,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    ax=ax,
    label="Histogram",
)

# KDE overlay for smooth density curve
sns.kdeplot(test_scores, color=KDE_COLOR, linewidth=4, ax=ax, label="KDE")

# Style
ax.set_xlabel("Test Score (%)", fontsize=20, color=INK)
ax.set_ylabel("Density", fontsize=20, color=INK)
ax.set_title("histogram-kde · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Clean up spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, linestyle="-", color=INK)

# Legend
ax.legend(frameon=True, fancybox=False, fontsize=16, framealpha=0.95, edgecolor=INK_SOFT, facecolor=ELEVATED_BG)

plt.tight_layout()
output_dir = os.path.dirname(os.path.abspath(__file__))
plt.savefig(os.path.join(output_dir, f"plot-{THEME}.png"), dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
