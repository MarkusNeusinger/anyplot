""" anyplot.ai
line-stepwise: Step Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os
import pathlib

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always brand green)
BRAND = "#009E73"
SECONDARY = "#C475FD"

# Data: Server capacity levels over monitoring period
np.random.seed(42)
hours = np.arange(0, 24, 1)

# Server capacity changes at discrete intervals
capacity = np.array(
    [
        50,
        50,
        50,
        50,
        50,
        50,  # Night: low capacity
        75,
        75,
        100,
        100,
        100,
        100,  # Morning ramp-up
        150,
        150,
        150,
        125,
        125,
        100,  # Peak hours, then decline
        100,
        75,
        75,
        75,
        50,
        50,  # Evening wind-down
    ]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Step plot with 'post' alignment - value persists until next point
ax.step(hours, capacity, where="post", linewidth=3.5, color=BRAND, label="Server Capacity")

# Add markers at change points to show discrete values
ax.scatter(hours, capacity, s=150, color=BRAND, edgecolors=PAGE_BG, linewidths=1.5, zorder=5)

# Fill under the step curve for visual emphasis
ax.fill_between(hours, capacity, step="post", alpha=0.15, color=BRAND)

# Style
ax.set_xlabel("Hour of Day", fontsize=20, color=INK)
ax.set_ylabel("Server Capacity (units)", fontsize=20, color=INK)
ax.set_title("line-stepwise · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set axis limits with padding
ax.set_xlim(-0.5, 23.5)
ax.set_ylim(0, 175)

# Configure x-axis ticks for hours
ax.set_xticks(np.arange(0, 24, 2))
ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK_SOFT)

# Legend styling
leg = ax.legend(fontsize=16, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()

# Save to implementation directory
output_dir = pathlib.Path(__file__).parent
plt.savefig(output_dir / f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
