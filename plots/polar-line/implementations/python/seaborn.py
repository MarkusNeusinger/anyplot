""" anyplot.ai
polar-line: Polar Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Configure seaborn theme with theme-adaptive colors
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

# Data - Wind speeds by compass direction (8 directions, two wind patterns)
np.random.seed(42)
angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)

# Pattern 1: Prevailing winds (stronger from one direction)
prevailing = 12 + 6 * np.sin(angles) + np.random.randn(8) * 0.3

# Pattern 2: Secondary wind pattern (different characteristic)
secondary = 8 + 4 * np.sin(angles + np.pi / 2) + np.random.randn(8) * 0.3

# Close the loop for continuous lines
angles_closed = np.append(angles, angles[0])
prevailing_closed = np.append(prevailing, prevailing[0])
secondary_closed = np.append(secondary, secondary[0])

# Create polar plot (square format for circular plot)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot lines
ax.plot(
    angles_closed,
    prevailing_closed,
    linewidth=3.5,
    color=IMPRINT[0],
    label="Prevailing Winds",
    marker="o",
    markersize=12,
    alpha=0.9,
)
ax.plot(
    angles_closed,
    secondary_closed,
    linewidth=3.5,
    color=IMPRINT[1],
    label="Secondary Pattern",
    marker="s",
    markersize=10,
    alpha=0.9,
)

# Configure theta axis (compass directions)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
ax.set_xticks(angles)
ax.set_xticklabels(directions, fontsize=18, color=INK_SOFT)

# Configure radial axis (wind speed in m/s)
ax.set_ylim(0, 20)
ax.set_yticks([5, 10, 15, 20])
ax.set_yticklabels(["5", "10", "15", "20"], fontsize=16, color=INK_SOFT)

# Title and legend
ax.set_title(
    "Wind Speed by Direction · polar-line · seaborn · anyplot.ai", fontsize=24, pad=30, fontweight="medium", color=INK
)

ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.05), fontsize=18, frameon=True)

# Grid styling
ax.grid(True, alpha=0.15, linestyle="-", linewidth=0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
