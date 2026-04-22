""" pyplots.ai
box-notched: Notched Box Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Salary distributions across departments with varying characteristics
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support", "HR"]
data = []

# Engineering: higher salaries, moderate spread
data.extend([{"Department": "Engineering", "Salary": val} for val in np.random.normal(95000, 15000, 80)])

# Marketing: medium salaries, narrow spread
data.extend([{"Department": "Marketing", "Salary": val} for val in np.random.normal(72000, 10000, 60)])

# Sales: wide spread with some high outliers
sales_base = np.random.normal(68000, 18000, 55)
sales_outliers = np.array([130000, 145000, 155000])  # High performers
data.extend([{"Department": "Sales", "Salary": val} for val in np.concatenate([sales_base, sales_outliers])])

# Support: lower salaries, tight distribution
data.extend([{"Department": "Support", "Salary": val} for val in np.random.normal(52000, 8000, 45)])

# HR: medium salaries, overlapping with Marketing (for notch comparison)
data.extend([{"Department": "HR", "Salary": val} for val in np.random.normal(70000, 11000, 50)])

df = pd.DataFrame(data)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom color palette using Python colors first, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E07A5F", "#81B29A"]

# Create notched box plot
sns.boxplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Department",
    palette=colors,
    notch=True,
    width=0.6,
    linewidth=2,
    fliersize=8,
    flierprops={"marker": "o", "markerfacecolor": "gray", "alpha": 0.6},
    ax=ax,
    legend=False,
)

# Styling
ax.set_title("box-notched · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Annual Salary ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format y-axis to show dollar amounts
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}K"))

# Subtle grid
ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add annotation explaining notches
ax.text(
    0.98,
    0.02,
    "Notches show 95% CI around median\nNon-overlapping notches suggest significant difference",
    transform=ax.transAxes,
    fontsize=12,
    ha="right",
    va="bottom",
    alpha=0.7,
    style="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
