""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-24
"""

import os

import matplotlib.pyplot as plt
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

# Data - real-world sample: penguin flipper lengths
penguins = sns.load_dataset("penguins").dropna(subset=["flipper_length_mm"])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.ecdfplot(data=penguins, x="flipper_length_mm", ax=ax, linewidth=3.5, color=BRAND)

# Style
ax.set_xlabel("Flipper Length (mm)", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Proportion", fontsize=20, color=INK)
ax.set_title("Penguin Flipper Lengths · ecdf-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_ylim(0, 1)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

ax.grid(True, axis="both", alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
