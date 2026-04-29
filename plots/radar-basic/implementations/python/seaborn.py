""" anyplot.ai
radar-basic: Basic Radar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-29
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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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
        "grid.color": INK_SOFT,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Employee performance comparison across competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Leadership", "Problem Solving", "Creativity"]
employee_a_values = [85, 90, 75, 70, 88, 82]  # Senior Developer
employee_b_values = [78, 65, 92, 85, 72, 75]  # Team Lead

n_vars = len(categories)
angles = np.linspace(0, 2 * np.pi, n_vars, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

employee_a = employee_a_values + employee_a_values[:1]
employee_b = employee_b_values + employee_b_values[:1]

# Plot - square canvas for symmetric radar chart (3600x3600 at 300 dpi)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

color_a = OKABE_ITO[0]  # #009E73 - Senior Developer (first series)
color_b = OKABE_ITO[1]  # #D55E00 - Team Lead

ax.fill(angles, employee_a, alpha=0.25, color=color_a)
ax.plot(angles, employee_a, color=color_a, linewidth=3.5, label="Senior Developer")
ax.scatter(angles[:-1], employee_a_values, color=color_a, s=150, zorder=5)

ax.fill(angles, employee_b, alpha=0.25, color=color_b)
ax.plot(angles, employee_b, color=color_b, linewidth=3.5, label="Team Lead")
ax.scatter(angles[:-1], employee_b_values, color=color_b, s=150, zorder=5)

# Style axes
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=20, color=INK, fontweight="medium")
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=16, color=INK_SOFT)

# Grid and spines
grid_alpha = 0.20 if THEME == "light" else 0.25
ax.grid(True, alpha=grid_alpha, linestyle="-", linewidth=1.2, color=INK_SOFT)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_alpha(0.4)

# Title
ax.set_title("radar-basic · seaborn · anyplot.ai", fontsize=26, fontweight="medium", color=INK, pad=40)

# Legend
legend = ax.legend(
    loc="upper right",
    bbox_to_anchor=(1.35, 1.15),
    fontsize=18,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
for text in legend.get_texts():
    text.set_color(INK)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
