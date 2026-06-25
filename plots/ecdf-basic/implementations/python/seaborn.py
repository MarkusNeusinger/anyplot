"""anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 88/100 | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import seaborn as sns


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1, 2, 3 (Adelie, Chinstrap, Gentoo)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3"]

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

# Data — penguin flipper lengths by species (deterministic real-world dataset)
penguins = sns.load_dataset("penguins").dropna(subset=["flipper_length_mm", "species"])

# Plot — multi-hue ecdfplot shows distribution comparison across species
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.ecdfplot(data=penguins, x="flipper_length_mm", hue="species", palette=IMPRINT_PALETTE, linewidth=2.5, ax=ax)

# Percentile reference lines for direct reading of Q1 / median / Q3
for p in (0.25, 0.50, 0.75):
    ax.axhline(p, color=INK_MUTED, linewidth=0.7, linestyle="--", alpha=0.55, zorder=0)

# Style
title = "Penguin Flipper Lengths · ecdf-basic · python · seaborn · anyplot.ai"
n = len(title)
title_fontsize = round(12 * 67 / n) if n > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Flipper Length (mm)", fontsize=10, color=INK)
ax.set_ylabel("Cumulative Proportion", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(0, 1)
ax.set_yticks([0, 0.25, 0.50, 0.75, 1.0])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Style the auto-generated legend
legend = ax.get_legend()
if legend:
    legend.get_frame().set_facecolor(ELEVATED_BG)
    legend.get_frame().set_edgecolor(INK_SOFT)
    for text in legend.get_texts():
        text.set_color(INK_SOFT)
        text.set_fontsize(8)
    legend.set_title("Species", prop={"size": 8, "weight": "medium"})
    legend.get_title().set_color(INK_SOFT)

# Save — bbox_inches must stay default (None) to preserve exact figsize × dpi canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
