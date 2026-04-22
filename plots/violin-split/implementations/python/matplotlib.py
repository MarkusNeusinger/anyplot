""" pyplots.ai
violin-split: Split Violin Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data - Salary comparison by gender across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_group = 150

# Generate realistic salary data with different distributions
data = {"category": [], "value": [], "split_group": []}

# Base salaries and characteristics per department
dept_params = {
    "Engineering": {"base_m": 95000, "base_f": 90000, "spread_m": 20000, "spread_f": 18000},
    "Marketing": {"base_m": 72000, "base_f": 71000, "spread_m": 15000, "spread_f": 14000},
    "Sales": {"base_m": 68000, "base_f": 65000, "spread_m": 25000, "spread_f": 22000},
    "HR": {"base_m": 58000, "base_f": 60000, "spread_m": 12000, "spread_f": 13000},
}

for dept in departments:
    params = dept_params[dept]
    # Male salaries - slightly right-skewed
    male_salaries = np.random.lognormal(mean=np.log(params["base_m"]), sigma=0.25, size=n_per_group)
    male_salaries = np.clip(male_salaries, 30000, 180000)

    # Female salaries - different distribution shape
    female_salaries = np.random.lognormal(mean=np.log(params["base_f"]), sigma=0.22, size=n_per_group)
    female_salaries = np.clip(female_salaries, 30000, 180000)

    data["category"].extend([dept] * n_per_group * 2)
    data["value"].extend(list(male_salaries) + list(female_salaries))
    data["split_group"].extend(["Male"] * n_per_group + ["Female"] * n_per_group)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Colors
color_male = "#306998"  # Python Blue
color_female = "#FFD43B"  # Python Yellow

# Create split violins
positions = np.arange(len(departments))

for i, dept in enumerate(departments):
    # Get data for this department
    mask_male = [
        j
        for j, (c, g) in enumerate(zip(data["category"], data["split_group"], strict=False))
        if c == dept and g == "Male"
    ]
    mask_female = [
        j
        for j, (c, g) in enumerate(zip(data["category"], data["split_group"], strict=False))
        if c == dept and g == "Female"
    ]

    male_vals = [data["value"][j] for j in mask_male]
    female_vals = [data["value"][j] for j in mask_female]

    # Create violin for males (left side)
    vp_male = ax.violinplot(
        [male_vals], positions=[i], widths=0.8, showmeans=False, showmedians=False, showextrema=False
    )

    # Clip to left half
    for body in vp_male["bodies"]:
        m = np.mean(body.get_paths()[0].vertices[:, 0])
        body.get_paths()[0].vertices[:, 0] = np.clip(body.get_paths()[0].vertices[:, 0], -np.inf, m)
        body.set_facecolor(color_male)
        body.set_edgecolor("black")
        body.set_linewidth(1.5)
        body.set_alpha(0.8)

    # Create violin for females (right side)
    vp_female = ax.violinplot(
        [female_vals], positions=[i], widths=0.8, showmeans=False, showmedians=False, showextrema=False
    )

    # Clip to right half
    for body in vp_female["bodies"]:
        m = np.mean(body.get_paths()[0].vertices[:, 0])
        body.get_paths()[0].vertices[:, 0] = np.clip(body.get_paths()[0].vertices[:, 0], m, np.inf)
        body.set_facecolor(color_female)
        body.set_edgecolor("black")
        body.set_linewidth(1.5)
        body.set_alpha(0.8)

    # Add consistent quartile markers with contrasting outlines
    q1_m, med_m, q3_m = np.percentile(male_vals, [25, 50, 75])
    q1_f, med_f, q3_f = np.percentile(female_vals, [25, 50, 75])

    # Male side (left) - white lines with dark edge for visibility
    ax.hlines(med_m, i - 0.28, i - 0.02, colors="white", linewidth=4, zorder=3)
    ax.hlines(med_m, i - 0.28, i - 0.02, colors="#1a1a1a", linewidth=1, zorder=4)
    ax.hlines([q1_m, q3_m], i - 0.18, i - 0.02, colors="white", linewidth=2.5, zorder=3)
    ax.hlines([q1_m, q3_m], i - 0.18, i - 0.02, colors="#1a1a1a", linewidth=0.8, zorder=4)

    # Female side (right) - same style for consistency
    ax.hlines(med_f, i + 0.02, i + 0.28, colors="white", linewidth=4, zorder=3)
    ax.hlines(med_f, i + 0.02, i + 0.28, colors="#1a1a1a", linewidth=1, zorder=4)
    ax.hlines([q1_f, q3_f], i + 0.02, i + 0.18, colors="white", linewidth=2.5, zorder=3)
    ax.hlines([q1_f, q3_f], i + 0.02, i + 0.18, colors="#1a1a1a", linewidth=0.8, zorder=4)

# Styling
ax.set_xticks(positions)
ax.set_xticklabels(departments)
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Annual Salary ($)", fontsize=20)
ax.set_title("violin-split · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Format y-axis with dollar amounts
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}K"))

# Add legend - positioned outside plot area to avoid overlap with violins
legend_elements = [
    Patch(facecolor=color_male, edgecolor="black", alpha=0.8, label="Male"),
    Patch(facecolor=color_female, edgecolor="black", alpha=0.8, label="Female"),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left", bbox_to_anchor=(0.01, 0.99), framealpha=0.9)

# Grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
