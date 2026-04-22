""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Data - Net Promoter Score by Department
np.random.seed(42)
departments = [
    "Customer Support",
    "Sales",
    "Engineering",
    "Marketing",
    "Finance",
    "Human Resources",
    "Operations",
    "Legal",
    "Research & Dev",
    "Quality Assurance",
    "IT Services",
    "Product Management",
]

# Simulate NPS scores ranging from -60 to +80
scores = np.array([45, 62, 28, -15, -32, 8, -45, -22, 55, 12, -8, 38])

# Create DataFrame and sort by value
df = pd.DataFrame({"Department": departments, "NPS Score": scores})
df = df.sort_values("NPS Score", ascending=True).reset_index(drop=True)

# Assign colors based on positive/negative values
colors = ["#306998" if x >= 0 else "#FFD43B" for x in df["NPS Score"]]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Horizontal bar chart using seaborn barplot
sns.barplot(data=df, x="NPS Score", y="Department", hue="Department", palette=colors, legend=False, ax=ax, orient="h")

# Add vertical line at zero baseline
ax.axvline(x=0, color="black", linewidth=1.5, linestyle="-", zorder=0)

# Style the plot
ax.set_xlabel("Net Promoter Score", fontsize=20)
ax.set_ylabel("Department", fontsize=20)
ax.set_title("bar-diverging · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-70, 80)

# Add subtle grid on x-axis only
ax.xaxis.grid(True, alpha=0.3, linestyle="--")
ax.yaxis.grid(False)
ax.set_axisbelow(True)

# Add value labels at the end of each bar
for i, (_idx, row) in enumerate(df.iterrows()):
    value = row["NPS Score"]
    ha = "left" if value >= 0 else "right"
    offset = 2 if value >= 0 else -2
    ax.text(value + offset, i, f"{value:+d}", va="center", ha=ha, fontsize=14, fontweight="bold")

# Add legend for color meaning
legend_elements = [
    Patch(facecolor="#306998", label="Positive (Promoters)"),
    Patch(facecolor="#FFD43B", label="Negative (Detractors)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=14, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
