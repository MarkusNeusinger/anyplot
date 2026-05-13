""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-13
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
BRAND = "#009E73"

# Data - Technology companies with market cap and revenue
companies = [
    "TechCorp",
    "DataSys",
    "CloudNet",
    "ByteWorks",
    "QuantumAI",
    "NexGen",
    "CyberFlow",
    "InfoPrime",
    "CodeLabs",
    "DigiCore",
    "NetSphere",
    "AlgoTech",
    "VisionX",
    "PulseTech",
    "ZetaLogic",
]
market_cap = np.array([55, 135, 105, 18, 225, 70, 120, 45, 165, 85, 30, 195, 150, 175, 60])
revenue = np.array([12, 42, 30, 4, 65, 18, 38, 10, 52, 24, 6, 58, 45, 50, 15])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(market_cap, revenue, s=250, alpha=0.7, color=BRAND, edgecolors=PAGE_BG, linewidths=2, zorder=3)

# Custom annotation offsets to avoid overlap
offsets = [
    (10, -10),
    (-10, 8),
    (10, 8),
    (-10, -12),
    (10, 8),
    (-10, 8),
    (10, -10),
    (10, -10),
    (-12, 8),
    (10, 8),
    (-10, -10),
    (10, -12),
    (10, 8),
    (10, 10),
    (-10, -10),
]

# Annotate each point
for i, company in enumerate(companies):
    x_offset, y_offset = offsets[i]
    ha = "left" if x_offset > 0 else "right"

    ax.annotate(
        company,
        xy=(market_cap[i], revenue[i]),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        fontsize=13,
        color=INK,
        fontweight="medium",
        ha=ha,
        va="center",
        arrowprops={"arrowstyle": "-", "color": INK_SOFT, "lw": 1, "connectionstyle": "arc3,rad=0"},
        zorder=4,
    )

# Style
ax.set_xlabel("Market Capitalization ($ Billions)", fontsize=20, color=INK)
ax.set_ylabel("Annual Revenue ($ Billions)", fontsize=20, color=INK)
ax.set_title("scatter-annotated · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

ax.set_xlim(0, 240)
ax.set_ylim(0, 70)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
