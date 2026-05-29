"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-29
"""

import os
import sys


# Remove this script's directory from sys.path so "matplotlib" resolves to the
# installed package rather than this file (which shares its name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here and p != ""]

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = [
    "#009E73",  # brand green — always first series
    "#C475FD",  # lavender
    "#4467A3",  # blue
    "#BD8233",  # ochre
    "#AE3030",  # matte red
    "#2ABCCD",  # cyan
    "#954477",  # rose
    "#99B314",  # lime
]

# Data
p = np.linspace(0, 1, 200)
gini = 2 * p * (1 - p)

entropy = np.zeros_like(p)
mask = (p > 0) & (p < 1)
entropy[mask] = -p[mask] * np.log2(p[mask]) - (1 - p[mask]) * np.log2(1 - p[mask])

gini_at_half = 2 * 0.5 * 0.5  # 0.5 at p=0.5
entropy_at_half = 1.0  # 1.0 at p=0.5

# Plot
title = "line-impurity-comparison · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded difference region between curves
ax.fill_between(p, gini, entropy, alpha=0.07, color=INK_MUTED)

halo = [pe.Stroke(linewidth=4, foreground=PAGE_BG), pe.Normal()]

ax.plot(p, gini, linewidth=2.5, color=IMPRINT_PALETTE[0], label="Gini Impurity:  $2p(1-p)$", path_effects=halo)
ax.plot(
    p,
    entropy,
    linewidth=2.5,
    color=IMPRINT_PALETTE[1],
    linestyle="--",
    label=r"Entropy (norm.):  $-p\,\log_2 p - (1{-}p)\,\log_2(1{-}p)$",
    path_effects=halo,
)

# Maxima markers at p=0.5
ax.plot(
    0.5,
    gini_at_half,
    "o",
    color=IMPRINT_PALETTE[0],
    markersize=8,
    zorder=5,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.5,
)
ax.plot(
    0.5,
    entropy_at_half,
    "o",
    color=IMPRINT_PALETTE[1],
    markersize=8,
    zorder=5,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.5,
)

# Annotations — spec requests annotating the maximum impurity at p=0.5
ax.annotate(
    "Entropy max = 1.0\n$p = 0.5$",
    xy=(0.5, entropy_at_half),
    xytext=(0.15, 0.86),
    fontsize=7,
    color=IMPRINT_PALETTE[1],
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": IMPRINT_PALETTE[1], "lw": 1.2, "connectionstyle": "arc3,rad=-0.15"},
    ha="center",
    va="top",
)
ax.annotate(
    "Gini max = 0.5\n$p = 0.5$",
    xy=(0.5, gini_at_half),
    xytext=(0.78, 0.40),
    fontsize=7,
    color=IMPRINT_PALETTE[0],
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": IMPRINT_PALETTE[0], "lw": 1.2, "connectionstyle": "arc3,rad=0.15"},
    ha="center",
    va="bottom",
)

# Reference line at maximum impurity point
ax.axvline(x=0.5, color=INK_MUTED, linestyle=":", linewidth=1.0, zorder=1)
ax.text(0.5, 0.04, "Maximum impurity", fontsize=7, color=INK_MUTED, ha="center", va="bottom", fontstyle="italic")

# Style
ax.set_xlabel("Probability of Class 1 ($p$)", fontsize=10, color=INK)
ax.set_ylabel("Impurity (normalized)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color=INK)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.03, 1.08)

leg = ax.legend(fontsize=8, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.93, bottom=0.13)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
