""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
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

# Okabe-Ito palette (first two colors for the two groups)
COLORS = ["#009E73", "#C475FD"]

# Data - Response times across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]

# Generate data: different distributions for each category-group combination
data = {}
positions = {}
width = 0.35

for i, cat in enumerate(categories):
    for j, grp in enumerate(groups):
        if grp == "Novice":
            if cat == "Simple":
                vals = np.random.normal(loc=1.2, scale=0.3, size=40)
            elif cat == "Moderate":
                vals = np.random.normal(loc=2.5, scale=0.5, size=40)
            else:  # Complex
                vals = np.random.normal(loc=4.5, scale=0.8, size=40)
        else:  # Expert
            if cat == "Simple":
                vals = np.random.normal(loc=0.8, scale=0.2, size=40)
            elif cat == "Moderate":
                vals = np.random.normal(loc=1.5, scale=0.3, size=40)
            else:  # Complex
                vals = np.random.normal(loc=2.5, scale=0.5, size=40)
        vals = np.maximum(vals, 0.1)
        data[(cat, grp)] = vals
        offset = -width / 2 if j == 0 else width / 2
        positions[(cat, grp)] = i + offset

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw violins for each group
for j, grp in enumerate(groups):
    violin_data = [data[(cat, grp)] for cat in categories]
    pos = [i + (-width / 2 if j == 0 else width / 2) for i in range(len(categories))]

    parts = ax.violinplot(
        violin_data, positions=pos, widths=width * 0.9, showmeans=False, showmedians=True, showextrema=False
    )

    # Style violins
    for pc in parts["bodies"]:
        pc.set_facecolor(COLORS[j])
        pc.set_edgecolor(INK_SOFT)
        pc.set_alpha(0.5)
        pc.set_linewidth(1.5)

    # Style median lines
    parts["cmedians"].set_color(INK)
    parts["cmedians"].set_linewidth(2)

# Overlay swarm points
for cat in categories:
    for j, grp in enumerate(groups):
        vals = data[(cat, grp)]
        base_x = positions[(cat, grp)]

        # Create swarm-like jitter
        sorted_indices = np.argsort(vals)
        n_points = len(vals)
        jitter = np.zeros(n_points)

        bin_width = (vals.max() - vals.min()) / 20
        for idx in sorted_indices:
            val = vals[idx]
            nearby = np.abs(vals - val) < bin_width
            nearby_count = np.sum(nearby & (np.arange(n_points) <= idx))
            if nearby_count % 2 == 0:
                jitter[idx] = (nearby_count // 2) * 0.015
            else:
                jitter[idx] = -((nearby_count + 1) // 2) * 0.015

        x_positions = base_x + jitter

        ax.scatter(x_positions, vals, s=70, c=COLORS[j], edgecolors=PAGE_BG, linewidths=0.8, alpha=0.9, zorder=3)

# Style
ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, fontsize=18, color=INK_SOFT)
ax.set_xlabel("Task Complexity", fontsize=20, color=INK)
ax.set_ylabel("Response Time (seconds)", fontsize=20, color=INK)
ax.set_title("violin-grouped-swarm · Python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=COLORS[0], edgecolor=INK_SOFT, alpha=0.5, label=groups[0]),
    plt.Rectangle((0, 0), 1, 1, facecolor=COLORS[1], edgecolor=INK_SOFT, alpha=0.5, label=groups[1]),
]
leg = ax.legend(handles=legend_handles, fontsize=16, title="Expertise", title_fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
