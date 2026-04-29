""" anyplot.ai
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

SERIES_1 = "#009E73"  # Okabe-Ito position 1
SERIES_2 = "#D55E00"  # Okabe-Ito position 2

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
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"polar": True}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Start from top (12 o'clock), go clockwise
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Senior Developer
ax.fill(angles_closed, senior_dev_closed, color=SERIES_1, alpha=0.25)
ax.plot(
    angles_closed, senior_dev_closed, color=SERIES_1, linewidth=3, marker="o", markersize=10, label="Senior Developer"
)

# Team Lead
ax.fill(angles_closed, team_lead_closed, color=SERIES_2, alpha=0.25)
ax.plot(angles_closed, team_lead_closed, color=SERIES_2, linewidth=3, marker="o", markersize=10, label="Team Lead")

# Axis configuration
ax.set_xticks(angles)
ax.set_xticklabels(categories, fontsize=18, color=INK)

ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_rlabel_position(22.5)
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=13, color=INK_MUTED)

# Grid and outer spine
ax.grid(True, alpha=0.18, linewidth=1.0, color=INK)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.8)

# Title
ax.set_title(
    "Employee Performance · radar-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", pad=40, color=INK
)

# Legend
leg = ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=16)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
