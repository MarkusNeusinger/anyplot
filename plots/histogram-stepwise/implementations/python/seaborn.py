""" anyplot.ai
histogram-stepwise: Step Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-12
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

# Okabe-Ito palette — positions 1 and 2
IMPRINT = ["#009E73", "#C475FD"]

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

# Data - Simulating response times (ms) for two different services
np.random.seed(42)
service_a = np.random.exponential(scale=50, size=500) + 20
service_b = np.random.exponential(scale=80, size=500) + 40

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Step histograms
sns.histplot(service_a, bins=30, element="step", fill=False, color=IMPRINT[0], linewidth=3, label="Service A", ax=ax)
sns.histplot(service_b, bins=30, element="step", fill=False, color=IMPRINT[1], linewidth=3, label="Service B", ax=ax)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Count", fontsize=20, color=INK)
ax.set_title("histogram-stepwise · seaborn · anyplot.ai", fontsize=24, color=INK, fontweight="medium")
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.legend(fontsize=16, loc="upper right", framealpha=0.95)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
