""" pyplots.ai
violin-basic: Basic Violin Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Salary distributions across departments
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "Support"]
records = []

for dept in departments:
    if dept == "Engineering":
        salaries = np.random.normal(85000, 15000, 150)
    elif dept == "Marketing":
        salaries = np.random.normal(70000, 12000, 150)
    elif dept == "Sales":
        # Bimodal distribution (junior vs senior) — showcases KDE strength
        salaries = np.concatenate([np.random.normal(55000, 8000, 75), np.random.normal(90000, 10000, 75)])
    else:
        salaries = np.random.normal(55000, 10000, 150)
    for s in salaries:
        records.append({"Department": dept, "Salary": s})

df = pd.DataFrame(records)

# Distinctive palette with good contrast between categories
palette = ["#306998", "#E8825A", "#5BA38B", "#C46BAE"]

fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

# Violin plot
sns.violinplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Department",
    palette=palette,
    inner="box",
    cut=0,
    linewidth=1.2,
    saturation=0.85,
    legend=False,
    ax=ax,
)

# Stripplot overlay — signature seaborn layering pattern
sns.stripplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Department",
    palette=palette,
    dodge=False,
    jitter=0.25,
    size=2.5,
    alpha=0.25,
    legend=False,
    ax=ax,
)

# Annotate the bimodal Sales distribution to guide the viewer
sales_data = df[df["Department"] == "Sales"]["Salary"]
lower_peak = sales_data[sales_data < 72000].median()
upper_peak = sales_data[sales_data >= 72000].median()

ax.annotate(
    "Junior cohort",
    xy=(1.85, lower_peak),
    xytext=(1.35, lower_peak - 5000),
    fontsize=12,
    fontstyle="italic",
    color="#555555",
    ha="right",
    va="center",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.0},
)
ax.annotate(
    "Senior cohort",
    xy=(1.85, upper_peak),
    xytext=(1.35, upper_peak + 5000),
    fontsize=12,
    fontstyle="italic",
    color="#555555",
    ha="right",
    va="center",
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.0},
)

# Style
ax.set_xlabel("Department", fontsize=20, labelpad=12)
ax.set_ylabel("Salary ($)", fontsize=20, labelpad=12)
ax.set_title("violin-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.yaxis.grid(True, alpha=0.3, linewidth=0.6, color="#CCCCCC")
ax.set_axisbelow(True)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}k"))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
