""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - using first 3 colors in canonical order
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Response times (ms) for three different server regions
np.random.seed(42)

us_east = np.random.normal(loc=45, scale=12, size=200)
europe = np.random.normal(loc=65, scale=15, size=180)
asia = np.random.normal(loc=80, scale=20, size=150)

us_east = np.clip(us_east, 10, 120)
europe = np.clip(europe, 15, 140)
asia = np.clip(asia, 20, 160)

labels = ["US-East", "Europe", "Asia-Pacific"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.hist(
    [us_east, europe, asia],
    bins=20,
    stacked=True,
    color=IMPRINT,
    label=labels,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    alpha=0.9,
)

# Style
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Number of Requests", fontsize=20, color=INK)
ax.set_title("histogram-stacked · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="upper right", frameon=True)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
