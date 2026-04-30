""" anyplot.ai
rug-basic: Basic Rug Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
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
BRAND = "#009E73"  # Okabe-Ito position 1

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

# Data - response times with bimodal pattern (fast and slow responses)
np.random.seed(42)
fast_responses = np.random.normal(loc=150, scale=30, size=80)
slow_responses = np.random.normal(loc=350, scale=50, size=40)
response_times = np.concatenate([fast_responses, slow_responses, [50, 520, 550]])

# Plot - KDE with rug plot beneath
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.kdeplot(x=response_times, color=BRAND, linewidth=3, fill=True, alpha=0.18, ax=ax)
sns.rugplot(x=response_times, height=0.06, lw=2, alpha=0.6, color=BRAND, ax=ax)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Density", fontsize=20, color=INK)
ax.set_title("rug-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
