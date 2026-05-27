""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-12
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

# Okabe-Ito palette (canonical order)
IMPRINT = [
    "#009E73",  # bluish green — ALWAYS first series
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
]

# Data — plant species with distinct petal characteristics
np.random.seed(42)
n_per_group = 40

# Species A: Smaller petals
species_a_x = np.random.normal(1.5, 0.3, n_per_group)
species_a_y = np.random.normal(0.3, 0.1, n_per_group)

# Species B: Medium petals
species_b_x = np.random.normal(4.0, 0.5, n_per_group)
species_b_y = np.random.normal(1.3, 0.2, n_per_group)

# Species C: Larger petals
species_c_x = np.random.normal(5.5, 0.6, n_per_group)
species_c_y = np.random.normal(2.0, 0.3, n_per_group)

categories = ["Species A", "Species B", "Species C"]
markers = ["o", "s", "^"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot each category with distinct colors and markers
scatter_data = [
    (species_a_x, species_a_y, IMPRINT[0], markers[0]),
    (species_b_x, species_b_y, IMPRINT[1], markers[1]),
    (species_c_x, species_c_y, IMPRINT[2], markers[2]),
]

for i, (x, y, color, marker) in enumerate(scatter_data):
    ax.scatter(x, y, s=200, c=color, alpha=0.8, label=categories[i], marker=marker, edgecolors=PAGE_BG, linewidth=0.5)

# Labels and styling
ax.set_xlabel("Petal Length (cm)", fontsize=20, color=INK)
ax.set_ylabel("Petal Width (cm)", fontsize=20, color=INK)
ax.set_title("scatter-categorical · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)

# Legend
leg = ax.legend(fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
