""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-04
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito base colors for level-1 departments (positions 1–3)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]
OKABE_RGB = [tuple(int(c[j : j + 2], 16) / 255 for j in (1, 3, 5)) for c in OKABE_ITO]

# Data: Company budget breakdown ($thousands)
data = {
    "Engineering": {
        "Frontend": {"Web App": 150, "Mobile": 120},
        "Backend": {"API": 180, "Database": 90},
        "DevOps": {"Cloud": 100, "CI/CD": 60},
    },
    "Sales": {"North": {"Enterprise": 200, "SMB": 80}, "South": {"Enterprise": 150, "SMB": 70}},
    "Marketing": {"Digital": {"SEO": 60, "Ads": 140}, "Brand": {"Events": 80, "Content": 50}},
}

# Build flat lists per ring
level1_names, level1_values, level1_colors = [], [], []
level2_names, level2_values, level2_colors = [], [], []
level3_names, level3_values, level3_colors = [], [], []

for i, (dept, teams) in enumerate(data.items()):
    dept_total = sum(sum(projs.values()) for projs in teams.values())
    level1_names.append(dept)
    level1_values.append(dept_total)
    level1_colors.append(OKABE_ITO[i])

    r, g, b = OKABE_RGB[i]
    team_items = list(teams.items())
    n_teams = len(team_items)
    for j, (team, projects) in enumerate(team_items):
        team_total = sum(projects.values())
        level2_names.append(team)
        level2_values.append(team_total)
        f2 = 0.38 + 0.12 * j / max(n_teams - 1, 1)
        level2_colors.append((min(1, r + (1 - r) * f2), min(1, g + (1 - g) * f2), min(1, b + (1 - b) * f2)))

        proj_items = list(projects.items())
        n_projs = len(proj_items)
        for k, (proj, value) in enumerate(proj_items):
            level3_names.append(proj)
            level3_values.append(value)
            f3 = 0.58 + 0.12 * k / max(n_projs - 1, 1)
            level3_colors.append((min(1, r + (1 - r) * f3), min(1, g + (1 - g) * f3), min(1, b + (1 - b) * f3)))

# Plot — square canvas for radial chart
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ring_width = 0.35
inner_radius = 0.25

# Level 3 (outermost ring)
wedges3, _ = ax.pie(
    level3_values,
    radius=inner_radius + 3 * ring_width,
    colors=level3_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": PAGE_BG, "linewidth": 2.5},
)

# Level 2 (middle ring)
wedges2, _ = ax.pie(
    level2_values,
    radius=inner_radius + 2 * ring_width,
    colors=level2_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": PAGE_BG, "linewidth": 2.5},
)

# Level 1 (innermost ring) with department labels inside wedges
wedges1, texts1 = ax.pie(
    level1_values,
    radius=inner_radius + ring_width,
    colors=level1_colors,
    labels=level1_names,
    labeldistance=0.55,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": PAGE_BG, "linewidth": 2.5},
    textprops={"fontsize": 18, "fontweight": "bold", "color": "white"},
)

# Level 2 segment labels (positioned at ring midpoint)
for i, wedge in enumerate(wedges2):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r_mid = inner_radius + 1.5 * ring_width
    x = r_mid * np.cos(np.radians(ang))
    y = r_mid * np.sin(np.radians(ang))
    if (wedge.theta2 - wedge.theta1) > 15:
        ax.text(x, y, level2_names[i], ha="center", va="center", fontsize=14, fontweight="medium", color="#1A1A17")

# Level 3 segment labels (outermost ring midpoint)
for i, wedge in enumerate(wedges3):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r_mid = inner_radius + 2.5 * ring_width
    x = r_mid * np.cos(np.radians(ang))
    y = r_mid * np.sin(np.radians(ang))
    if (wedge.theta2 - wedge.theta1) > 12:
        ax.text(x, y, level3_names[i], ha="center", va="center", fontsize=12, color="#4A4A44")

ax.set_aspect("equal")
ax.set_title(
    "Company Budget · sunburst-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="bold", pad=25, color=INK
)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
