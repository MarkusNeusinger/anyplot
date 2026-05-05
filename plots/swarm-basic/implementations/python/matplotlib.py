""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-05
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

# Okabe-Ito palette — 4 departments
COLORS = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Employee performance scores by department
np.random.seed(42)

departments = ["Engineering", "Sales", "Marketing", "Support"]
n_points = [50, 45, 40, 55]

scores_data = {
    "Engineering": np.clip(np.random.normal(78, 12, n_points[0]), 0, 100),
    "Sales": np.clip(np.random.normal(72, 15, n_points[1]), 0, 100),
    "Marketing": np.clip(np.random.normal(82, 10, n_points[2]), 0, 100),
    "Support": np.clip(np.random.normal(68, 14, n_points[3]), 0, 100),
}

# Calculate point radius for swarm collision detection
all_values = np.concatenate(list(scores_data.values()))
y_min, y_max = all_values.min() - 5, all_values.max() + 5
point_radius = 0.03 * (y_max - y_min)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, dept in enumerate(departments):
    vals = scores_data[dept]
    n = len(vals)
    offsets = np.zeros(n)

    sorted_idx = np.argsort(vals)

    for j, idx in enumerate(sorted_idx):
        val = vals[idx]
        placed_idx = sorted_idx[:j]
        nearby = [(offsets[k], vals[k]) for k in placed_idx if abs(vals[k] - val) < point_radius * 2.5]

        if not nearby:
            offsets[idx] = 0
            continue

        best_offset = 0
        found = False
        for offset in np.linspace(0, 0.35, 50):
            for sign in [1, -1]:
                test_x = sign * offset
                collision = False
                for ox, oy in nearby:
                    dx = test_x - ox
                    dy = (val - oy) / point_radius
                    if dx * dx + dy * dy < 4:
                        collision = True
                        break
                if not collision:
                    best_offset = test_x
                    found = True
                    break
            if found:
                break
        offsets[idx] = best_offset

    ax.scatter(i + offsets, vals, s=150, alpha=0.75, color=COLORS[i], edgecolors=PAGE_BG, linewidth=0.5, label=dept)

    mean_val = np.mean(vals)
    ax.scatter(i, mean_val, s=350, color=COLORS[i], marker="D", edgecolors=INK, linewidth=2, zorder=5)

# Add invisible mean-marker entry for legend
ax.scatter([], [], s=350, color=INK_SOFT, marker="D", edgecolors=INK, linewidth=2, label="Mean")

# Style
ax.set_xlabel("Department", fontsize=20, color=INK)
ax.set_ylabel("Performance Score", fontsize=20, color=INK)
ax.set_title("swarm-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(range(len(departments)))
ax.set_xticklabels(departments, fontsize=16)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_ylim(25, 105)
ax.set_xlim(-0.6, 3.6)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

leg = ax.legend(fontsize=16, loc="upper right", framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
