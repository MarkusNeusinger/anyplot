"""anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

COLOR_INC = "#009E73"  # Okabe-Ito pos 1 — increase (brand green)
COLOR_DEC = "#D55E00"  # Okabe-Ito pos 2 — decrease (vermillion)

# Data
products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F", "Product G", "Product H"]
q1_sales = [3.0, 6.5, 10.0, 13.5, 17.0, 20.5, 24.0, 27.5]
q4_sales = [5.5, 4.0, 14.0, 11.0, 20.0, 17.5, 28.0, 25.0]
changes = [q4 - q1 for q1, q4 in zip(q1_sales, q4_sales, strict=True)]

# Label collision avoidance: sort by value and nudge positions if too close
min_gap = 1.8

q1_indexed = sorted(enumerate(q1_sales), key=lambda x: x[1])
q1_label_pos = [0.0] * len(q1_sales)
for i, (orig_idx, val) in enumerate(q1_indexed):
    if i == 0:
        q1_label_pos[orig_idx] = val
    else:
        prev_idx = q1_indexed[i - 1][0]
        if val - q1_label_pos[prev_idx] < min_gap:
            q1_label_pos[orig_idx] = q1_label_pos[prev_idx] + min_gap
        else:
            q1_label_pos[orig_idx] = val

q4_indexed = sorted(enumerate(q4_sales), key=lambda x: x[1])
q4_label_pos = [0.0] * len(q4_sales)
for i, (orig_idx, val) in enumerate(q4_indexed):
    if i == 0:
        q4_label_pos[orig_idx] = val
    else:
        prev_idx = q4_indexed[i - 1][0]
        if val - q4_label_pos[prev_idx] < min_gap:
            q4_label_pos[orig_idx] = q4_label_pos[prev_idx] + min_gap
        else:
            q4_label_pos[orig_idx] = val

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_positions = [0, 1]

# Vertical column lines at axis positions — structural anchors for the slopegraph
for x in x_positions:
    ax.axvline(x, color=INK_SOFT, linewidth=1.2, alpha=0.35, zorder=0)

for i, (product, q1, q4, change) in enumerate(zip(products, q1_sales, q4_sales, changes, strict=True)):
    color = COLOR_INC if change >= 0 else COLOR_DEC
    ax.plot(
        x_positions,
        [q1, q4],
        marker="o",
        markersize=12,
        linewidth=3,
        color=color,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.5,
    )

    # Left label: product name + Q1 value; dotted connector if label was nudged
    lpos = q1_label_pos[i]
    if abs(lpos - q1) > 0.05:
        ax.plot([-0.03, -0.03], [q1, lpos], color=color, linewidth=0.8, alpha=0.35, linestyle=":")
    ax.text(-0.06, lpos, f"{product}: ${q1:.1f}M", ha="right", va="center", fontsize=16, color=color, fontweight="bold")

    # Right label: product name + Q4 value; dotted connector if label was nudged
    rpos = q4_label_pos[i]
    if abs(rpos - q4) > 0.05:
        ax.plot([1.03, 1.03], [q4, rpos], color=color, linewidth=0.8, alpha=0.35, linestyle=":")
    ax.text(1.06, rpos, f"{product}: ${q4:.1f}M", ha="left", va="center", fontsize=16, color=color, fontweight="bold")

# Style
ax.set_xlim(-0.75, 1.75)
ax.set_xticks(x_positions)
ax.set_xticklabels(["Q1 2024", "Q4 2024"], fontsize=20, fontweight="bold", color=INK)
ax.set_ylabel("Sales", fontsize=20, color=INK)
ax.set_title("slope-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.tick_params(axis="x", length=0)
ax.tick_params(axis="y", labelsize=16, labelcolor=INK_SOFT, colors=INK_SOFT)

# FuncFormatter for y-axis: show units inline as "$XM" for self-documenting tick labels
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"${val:.0f}M"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)

ax.grid(True, axis="y", alpha=0.10, linewidth=0.8, color=INK)

# Legend centered below title
legend_elements = [
    Line2D(
        [0], [0], color=COLOR_INC, linewidth=3, marker="o", markersize=10, markeredgecolor=PAGE_BG, label="Increase"
    ),
    Line2D(
        [0], [0], color=COLOR_DEC, linewidth=3, marker="o", markersize=10, markeredgecolor=PAGE_BG, label="Decrease"
    ),
]
leg = ax.legend(
    handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, 0.98), fontsize=16, frameon=True, ncol=2
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
