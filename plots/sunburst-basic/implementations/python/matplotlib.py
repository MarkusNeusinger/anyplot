""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Hierarchical data: Company budget breakdown (in $thousands)
# Level 1: Departments, Level 2: Teams, Level 3: Projects
data = {
    "Engineering": {
        "Frontend": {"Web App": 150, "Mobile": 120},
        "Backend": {"API": 180, "Database": 90},
        "DevOps": {"Cloud": 100, "CI/CD": 60},
    },
    "Sales": {"North": {"Enterprise": 200, "SMB": 80}, "South": {"Enterprise": 150, "SMB": 70}},
    "Marketing": {"Digital": {"SEO": 60, "Ads": 140}, "Brand": {"Events": 80, "Content": 50}},
}

# Build hierarchical structure for plotting
level1_names = []
level1_values = []
level2_names = []
level2_values = []
level3_names = []
level3_values = []

# Color palette - Python colors first, then colorblind-safe
base_colors = ["#306998", "#FFD43B", "#4B8BBE"]

level1_colors = []
level2_colors = []
level3_colors = []

for i, (dept, teams) in enumerate(data.items()):
    dept_total = sum(sum(projs.values()) for projs in teams.values())
    level1_names.append(dept)
    level1_values.append(dept_total)
    base_color = base_colors[i % len(base_colors)]
    level1_colors.append(base_color)

    # Create color variations for child levels
    base_rgb = tuple(int(base_color.lstrip("#")[j : j + 2], 16) / 255 for j in (0, 2, 4))

    team_count = len(teams)
    for j, (team, projects) in enumerate(teams.items()):
        team_total = sum(projects.values())
        level2_names.append(team)
        level2_values.append(team_total)
        # Lighter shade for level 2
        factor = 0.7 + 0.3 * (j / max(team_count - 1, 1))
        l2_color = tuple(min(1, c * factor + (1 - factor) * 0.5) for c in base_rgb)
        level2_colors.append(l2_color)

        proj_count = len(projects)
        for k, (proj, value) in enumerate(projects.items()):
            level3_names.append(proj)
            level3_values.append(value)
            # Even lighter shade for level 3
            factor2 = 0.5 + 0.5 * (k / max(proj_count - 1, 1))
            l3_color = tuple(min(1, c * factor2 + (1 - factor2) * 0.7) for c in base_rgb)
            level3_colors.append(l3_color)

# Create square figure for radial plot - better canvas utilization
fig, ax = plt.subplots(figsize=(12, 12))

# Ring parameters - larger rings to fill canvas better
ring_width = 0.35
inner_radius = 0.25

# Level 3 (outermost ring)
wedges3, texts3 = ax.pie(
    level3_values,
    radius=inner_radius + 3 * ring_width,
    colors=level3_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": "white", "linewidth": 2.5},
)

# Level 2 (middle ring)
wedges2, texts2 = ax.pie(
    level2_values,
    radius=inner_radius + 2 * ring_width,
    colors=level2_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": "white", "linewidth": 2.5},
)

# Level 1 (innermost ring)
wedges1, texts1 = ax.pie(
    level1_values,
    radius=inner_radius + ring_width,
    colors=level1_colors,
    labels=level1_names,
    labeldistance=0.55,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": "white", "linewidth": 2.5},
    textprops={"fontsize": 18, "fontweight": "bold", "color": "white"},
)

# Add labels for level 2 segments (positioned within wedges)
for i, wedge in enumerate(wedges2):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r = inner_radius + 1.5 * ring_width
    x = r * np.cos(np.radians(ang))
    y = r * np.sin(np.radians(ang))
    # Only label if segment is large enough
    if (wedge.theta2 - wedge.theta1) > 15:
        ax.text(x, y, level2_names[i], ha="center", va="center", fontsize=14, fontweight="medium")

# Add labels for level 3 segments (outermost)
for i, wedge in enumerate(wedges3):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r = inner_radius + 2.5 * ring_width
    x = r * np.cos(np.radians(ang))
    y = r * np.sin(np.radians(ang))
    # Only label if segment is large enough
    if (wedge.theta2 - wedge.theta1) > 12:
        ax.text(x, y, level3_names[i], ha="center", va="center", fontsize=12)

ax.set_aspect("equal")
ax.set_title("Company Budget · sunburst-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=25)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
