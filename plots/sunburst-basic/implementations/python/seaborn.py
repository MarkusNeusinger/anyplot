""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Hierarchical data: Company budget breakdown (in $K)
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

# Apply seaborn styling
sns.set_theme(style="white", context="poster", font_scale=1.1)

# Build hierarchical structure for plotting
level1_names = []
level1_values = []
level2_names = []
level2_values = []
level2_parents = []
level3_names = []
level3_values = []
level3_parents = []

# Use seaborn color palette - Python Blue, Python Yellow, then colorblind-safe
base_palette = sns.color_palette(["#306998", "#FFD43B", "#4B8BBE"])

level1_colors = []
level2_colors = []
level3_colors = []

# Build data structure and color scheme
for i, (dept, teams) in enumerate(data.items()):
    dept_total = sum(sum(projs.values()) for projs in teams.values())
    level1_names.append(dept)
    level1_values.append(dept_total)
    base_color = base_palette[i % len(base_palette)]
    level1_colors.append(base_color)

    # Create lighter shades for child levels using seaborn's light_palette
    dept_light_palette = sns.light_palette(base_color, n_colors=6, reverse=False)

    team_count = len(teams)
    for j, (team, projects) in enumerate(teams.items()):
        team_total = sum(projects.values())
        level2_names.append(team)
        level2_values.append(team_total)
        level2_parents.append(dept)
        # Use intermediate shade for level 2
        level2_colors.append(dept_light_palette[3 + j % 2])

        for k, (proj, value) in enumerate(projects.items()):
            level3_names.append(proj)
            level3_values.append(value)
            level3_parents.append(team)
            # Use lighter shade for level 3
            level3_colors.append(dept_light_palette[4 + k % 2])

# Create DataFrame for all levels (used for seaborn heatmap representation)
df_full = pd.DataFrame({"Project": level3_names, "Team": level3_parents, "Budget": level3_values})

# Create figure with two subplots: sunburst and summary bar chart
fig = plt.figure(figsize=(16, 9))
ax_sun = fig.add_axes([0.02, 0.05, 0.58, 0.85])  # Main sunburst
ax_bar = fig.add_axes([0.65, 0.15, 0.32, 0.70])  # Summary bar chart

# Ring parameters
ring_width = 0.28
inner_radius = 0.22

# Level 3 (outermost ring)
wedges3, _ = ax_sun.pie(
    level3_values,
    radius=inner_radius + 3 * ring_width,
    colors=level3_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": "white", "linewidth": 2.5},
)

# Level 2 (middle ring)
wedges2, _ = ax_sun.pie(
    level2_values,
    radius=inner_radius + 2 * ring_width,
    colors=level2_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": "white", "linewidth": 2.5},
)

# Level 1 (innermost ring)
wedges1, texts1 = ax_sun.pie(
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
        ax_sun.text(x, y, level2_names[i], ha="center", va="center", fontsize=14, fontweight="medium", color="#333333")

# Add labels for level 3 segments (outermost)
for i, wedge in enumerate(wedges3):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r = inner_radius + 2.5 * ring_width
    x = r * np.cos(np.radians(ang))
    y = r * np.sin(np.radians(ang))
    # Only label if segment is large enough
    if (wedge.theta2 - wedge.theta1) > 12:
        ax_sun.text(x, y, level3_names[i], ha="center", va="center", fontsize=12, color="#555555")

# Add center text showing total
total_budget = sum(level1_values)
ax_sun.text(
    0, 0, f"${total_budget:,}K\nTotal", ha="center", va="center", fontsize=22, fontweight="bold", color="#306998"
)

ax_sun.set_aspect("equal")

# Create summary bar chart using seaborn barplot
df_dept = pd.DataFrame({"Department": level1_names, "Budget ($K)": level1_values})
sns.barplot(
    data=df_dept,
    y="Department",
    x="Budget ($K)",
    hue="Department",
    palette=base_palette,
    ax=ax_bar,
    legend=False,
    edgecolor="white",
    linewidth=2,
)

ax_bar.set_xlabel("Budget ($K)", fontsize=18)
ax_bar.set_ylabel("")
ax_bar.tick_params(axis="both", labelsize=16)
ax_bar.set_title("Department Totals", fontsize=20, fontweight="bold", pad=15)
ax_bar.grid(True, axis="x", alpha=0.3, linestyle="--")
ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)

# Add value labels on bars
for i, v in enumerate(level1_values):
    ax_bar.text(v + 15, i, f"${v}K", va="center", fontsize=14, fontweight="medium")

# Main title
fig.suptitle("Company Budget · sunburst-basic · seaborn · pyplots.ai", fontsize=26, fontweight="bold", y=0.98)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
