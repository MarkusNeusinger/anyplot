"""anyplot.ai
radar-basic: Basic Radar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

SERIES_1 = "#009E73"  # Imprint palette position 1
SERIES_2 = "#C475FD"  # Imprint palette position 2

# Data - Employee performance comparison across six competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
senior_dev = [82, 94, 75, 90, 48, 78]  # Strong technical, weaker leadership
team_lead = [88, 55, 96, 62, 91, 70]  # Strong people skills, weaker technical

num_vars = len(categories)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

senior_dev_closed = senior_dev + [senior_dev[0]]
team_lead_closed = team_lead + [team_lead[0]]
angles_closed = angles + [angles[0]]

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"polar": True}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Start from top (12 o'clock), go clockwise
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Alternating radial bands for subtle depth (design polish beyond flat gridlines)
ring_edges = [0, 20, 40, 60, 80, 100]
theta_full = np.linspace(0, 2 * np.pi, 200)
for i in range(len(ring_edges) - 1):
    if i % 2 == 1:
        ax.fill_between(theta_full, ring_edges[i], ring_edges[i + 1], color=INK, alpha=0.04, zorder=0)

# Senior Developer
ax.fill(angles_closed, senior_dev_closed, color=SERIES_1, alpha=0.25, zorder=2)
ax.plot(
    angles_closed,
    senior_dev_closed,
    color=SERIES_1,
    linewidth=3,
    marker="o",
    markersize=10,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.5,
    label="Senior Developer",
    zorder=3,
)

# Team Lead
ax.fill(angles_closed, team_lead_closed, color=SERIES_2, alpha=0.25, zorder=2)
ax.plot(
    angles_closed,
    team_lead_closed,
    color=SERIES_2,
    linewidth=3,
    marker="o",
    markersize=10,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.5,
    label="Team Lead",
    zorder=3,
)

# Axis configuration
ax.set_xticks(angles)
ax.set_xticklabels(categories, fontsize=18, color=INK)

ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_rlabel_position(22.5)
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=16, color=INK_MUTED)

# Grid and outer spine
ax.grid(True, alpha=0.18, linewidth=1.0, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.8)

# Title
title = "Employee Performance · radar-basic · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", pad=28, color=INK)

# Legend
leg = ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.2), fontsize=16, ncol=2)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.12, right=0.88, top=0.88, bottom=0.16)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
