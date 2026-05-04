""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-04
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

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

sns.set_theme(
    style="white",
    context="poster",
    font_scale=1.1,
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

# Build hierarchical structure and color scheme
level1_names = []
level1_values = []
level2_names = []
level2_values = []
level3_names = []
level3_values = []
level1_colors = []
level2_colors = []
level3_colors = []

for i, (dept, teams) in enumerate(data.items()):
    dept_total = sum(sum(projs.values()) for projs in teams.values())
    level1_names.append(dept)
    level1_values.append(dept_total)
    base_color = OKABE_ITO[i % len(OKABE_ITO)]
    level1_colors.append(base_color)

    # Light palette for child levels shows branch relationships via seaborn
    dept_light_palette = sns.light_palette(base_color, n_colors=6, reverse=False)

    for j, (team, projects) in enumerate(teams.items()):
        team_total = sum(projects.values())
        level2_names.append(team)
        level2_values.append(team_total)
        level2_colors.append(dept_light_palette[3 + j % 2])

        for k, (proj, value) in enumerate(projects.items()):
            level3_names.append(proj)
            level3_values.append(value)
            level3_colors.append(dept_light_palette[4 + k % 2])

# Figure layout: sunburst left, summary bar chart right
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax_sun = fig.add_axes([0.02, 0.05, 0.58, 0.85])
ax_bar = fig.add_axes([0.65, 0.15, 0.32, 0.70])
ax_sun.set_facecolor(PAGE_BG)
ax_bar.set_facecolor(PAGE_BG)

ring_width = 0.28
inner_radius = 0.22

# Level 3 (outermost ring)
wedges3, _ = ax_sun.pie(
    level3_values,
    radius=inner_radius + 3 * ring_width,
    colors=level3_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": PAGE_BG, "linewidth": 2.5},
)

# Level 2 (middle ring)
wedges2, _ = ax_sun.pie(
    level2_values,
    radius=inner_radius + 2 * ring_width,
    colors=level2_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": ring_width, "edgecolor": PAGE_BG, "linewidth": 2.5},
)

# Level 1 (innermost ring) — white labels contrast against saturated Okabe-Ito fills
wedges1, _ = ax_sun.pie(
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

# Level 2 labels (only for large enough segments)
for i, wedge in enumerate(wedges2):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r = inner_radius + 1.5 * ring_width
    x = r * np.cos(np.radians(ang))
    y = r * np.sin(np.radians(ang))
    if (wedge.theta2 - wedge.theta1) > 18:
        ax_sun.text(x, y, level2_names[i], ha="center", va="center", fontsize=13, fontweight="medium", color=INK)

# Level 3 labels (higher threshold to avoid crowding)
for i, wedge in enumerate(wedges3):
    ang = (wedge.theta2 + wedge.theta1) / 2
    r = inner_radius + 2.5 * ring_width
    x = r * np.cos(np.radians(ang))
    y = r * np.sin(np.radians(ang))
    if (wedge.theta2 - wedge.theta1) > 16:
        ax_sun.text(x, y, level3_names[i], ha="center", va="center", fontsize=11, color=INK_SOFT)

# Center text showing total
total_budget = sum(level1_values)
ax_sun.text(0, 0, f"${total_budget:,}K\nTotal", ha="center", va="center", fontsize=22, fontweight="bold", color=INK)
ax_sun.set_aspect("equal")

# Bar chart with palette matching sunburst branch colors
dept_palette = dict(zip(level1_names, OKABE_ITO, strict=True))
df_dept = pd.DataFrame({"Department": level1_names, "Budget ($K)": level1_values})
sns.barplot(
    data=df_dept,
    y="Department",
    x="Budget ($K)",
    hue="Department",
    palette=dept_palette,
    ax=ax_bar,
    legend=False,
    edgecolor=PAGE_BG,
    linewidth=2,
)

ax_bar.set_xlabel("Budget ($K)", fontsize=18, color=INK)
ax_bar.set_ylabel("", color=INK)
ax_bar.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax_bar.set_title("Department Totals", fontsize=20, fontweight="bold", pad=15, color=INK)
ax_bar.grid(True, axis="x", alpha=0.15, color=INK)
ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)
ax_bar.spines["left"].set_color(INK_SOFT)
ax_bar.spines["bottom"].set_color(INK_SOFT)

for i, v in enumerate(level1_values):
    ax_bar.text(v + 15, i, f"${v}K", va="center", fontsize=14, fontweight="medium", color=INK)

fig.suptitle(
    "Company Budget · sunburst-basic · seaborn · anyplot.ai", fontsize=26, fontweight="bold", y=0.98, color=INK
)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
