""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-13
"""

import os
import sys


# Remove current directory from path to avoid shadowing by matplotlib.py in this directory
sys.path = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data
np.random.seed(42)
directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WSW", "NW", "NNW"]
angles = np.linspace(0, 2 * np.pi, len(directions), endpoint=False)

wind_speeds = np.array([45, 38, 52, 41, 35, 48, 42, 39, 36, 44, 50, 43, 47, 46, 40, 37])

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)

bars = ax.bar(angles, wind_speeds, width=0.35, alpha=0.8, color=IMPRINT[0], edgecolor=INK_SOFT, linewidth=1.5)

# Style
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(angles)
ax.set_xticklabels(directions, fontsize=18, color=INK_SOFT)
ax.set_ylim(0, max(wind_speeds) * 1.1)

ax.set_yticklabels([])
y_ticks = ax.get_yticks()
ax.set_yticks(y_ticks)
ax.set_yticklabels([f"{int(y)}" for y in y_ticks], fontsize=14, color=INK_SOFT)

ax.set_title("polar-bar · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.grid(True, alpha=0.15, color=INK_SOFT, linewidth=0.8)

for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(1)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
