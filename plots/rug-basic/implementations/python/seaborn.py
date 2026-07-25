"""anyplot.ai
rug-basic: Basic Rug Plot
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 83/100 | Updated: 2026-07-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series
AMBER = "#DDCC77"  # semantic caution anchor — flags outlier ticks

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
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - response times with bimodal pattern (fast and slow responses)
np.random.seed(42)
fast_responses = np.random.normal(loc=150, scale=30, size=80)
slow_responses = np.random.normal(loc=350, scale=50, size=40)
outliers = np.array([50, 520, 550])
response_times = np.concatenate([fast_responses, slow_responses, outliers])

# Plot - KDE with rug plot beneath
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.kdeplot(x=response_times, color=BRAND, linewidth=2.5, fill=True, alpha=0.28, ax=ax)
# Main cluster ticks: taller + more opaque than the fill so they read distinctly on top of it
sns.rugplot(x=np.concatenate([fast_responses, slow_responses]), height=0.08, lw=1.5, alpha=0.85, color=BRAND, ax=ax)
# Outlier ticks called out in amber (caution anchor) — a focal point for the tail observations
sns.rugplot(x=outliers, height=0.11, lw=2, alpha=0.9, color=AMBER, ax=ax)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title("rug-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
