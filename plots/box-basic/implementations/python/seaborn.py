""" pyplots.ai
box-basic: Basic Box Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

dept_params = {
    "Engineering": {"loc": 95000, "scale": 15000, "n": 80},
    "Marketing": {"loc": 75000, "scale": 12000, "n": 60},
    "Sales": {"loc": 70000, "scale": 20000, "n": 100},
    "HR": {"loc": 65000, "scale": 10000, "n": 50},
    "Finance": {"loc": 85000, "scale": 18000, "n": 70},
}

data = []
for dept, params in dept_params.items():
    if dept == "Sales":
        # Right-skewed distribution to show distributional diversity
        values = np.random.exponential(scale=15000, size=params["n"]) + 45000
    else:
        values = np.random.normal(params["loc"], params["scale"], params["n"])
    outliers = np.random.uniform(values.min() - 20000, values.max() + 25000, 3)
    values = np.concatenate([values, outliers])
    for v in values:
        data.append({"Department": dept, "Salary": v})

df = pd.DataFrame(data)

# Seaborn context for global scaling
sns.set_context("talk", font_scale=1.1)

# Plot
palette = ["#306998", "#E8A838", "#4CAF50", "#FF7043", "#9C27B0"]

fig, ax = plt.subplots(figsize=(16, 9))

sns.boxplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Department",
    palette=palette,
    linewidth=2.5,
    fliersize=0,
    width=0.6,
    legend=False,
    ax=ax,
)

sns.stripplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Department",
    palette=palette,
    size=5,
    alpha=0.4,
    jitter=0.25,
    legend=False,
    ax=ax,
)

# Style
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Salary ($)", fontsize=20)
ax.set_title("box-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
sns.despine(ax=ax)

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}K"))

# Tighten y-axis to reduce empty space
y_min = df["Salary"].min() - 5000
y_max = df["Salary"].max() + 8000
ax.set_ylim(y_min, y_max)

# Data storytelling: annotate key insights
medians = df.groupby("Department")["Salary"].median()
spreads = df.groupby("Department")["Salary"].apply(lambda x: x.quantile(0.75) - x.quantile(0.25))

highest_dept = medians.idxmax()
widest_dept = spreads.idxmax()

dept_positions = {dept: i for i, dept in enumerate(dept_params.keys())}

# Annotate highest median (Engineering, position 0)
ax.annotate(
    f"Highest median: ${medians[highest_dept] / 1000:.0f}K",
    xy=(dept_positions[highest_dept], medians[highest_dept]),
    xytext=(dept_positions[highest_dept] + 1.6, y_max - (y_max - y_min) * 0.05),
    fontsize=13,
    fontweight="bold",
    color="#306998",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.8, "connectionstyle": "arc3,rad=-0.2"},
)

# Annotate widest spread (Finance, position 4)
ax.annotate(
    f"Widest IQR: ${spreads[widest_dept] / 1000:.0f}K spread",
    xy=(dept_positions[widest_dept], medians[widest_dept]),
    xytext=(dept_positions[widest_dept] - 1.6, y_min + (y_max - y_min) * 0.07),
    fontsize=13,
    fontweight="bold",
    color="#9C27B0",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#9C27B0", "lw": 1.8, "connectionstyle": "arc3,rad=0.2"},
)

# Annotate right-skewed Sales distribution
sales_pos = dept_positions["Sales"]
sales_q3 = df[df["Department"] == "Sales"]["Salary"].quantile(0.75)
ax.annotate(
    "Right-skewed\ndistribution",
    xy=(sales_pos, sales_q3),
    xytext=(sales_pos + 0.8, sales_q3 + (y_max - y_min) * 0.13),
    fontsize=13,
    fontweight="bold",
    color="#4CAF50",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#4CAF50", "lw": 1.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
