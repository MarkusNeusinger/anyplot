""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Data - Tech company revenue growth comparison Q1 vs Q4
# Values spaced to avoid label overlap
data = {
    "entity": ["TechCorp", "DataFlow", "CloudNine", "NetWorks", "CodeBase", "ByteSize", "LogicPro", "SoftEdge"],
    "Q1 Revenue ($M)": [145, 72, 215, 52, 178, 98, 125, 162],
    "Q4 Revenue ($M)": [192, 108, 178, 72, 225, 82, 155, 138],
}

df = pd.DataFrame(data)

# Calculate change for color coding
df["change"] = df["Q4 Revenue ($M)"] - df["Q1 Revenue ($M)"]
df["direction"] = df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")

# Sort by Q1 value for better visual layout
df = df.sort_values("Q1 Revenue ($M)").reset_index(drop=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Define colors - Python palette
colors = {"Increase": "#306998", "Decrease": "#FFD43B"}

# Reshape data for seaborn
df_melted = df.melt(
    id_vars=["entity", "direction"],
    value_vars=["Q1 Revenue ($M)", "Q4 Revenue ($M)"],
    var_name="Period",
    value_name="Revenue",
)

# Plot lines for each entity using seaborn
for entity in df["entity"]:
    entity_data = df_melted[df_melted["entity"] == entity]
    direction = entity_data["direction"].iloc[0]
    sns.lineplot(
        data=entity_data,
        x="Period",
        y="Revenue",
        color=colors[direction],
        linewidth=3.5,
        alpha=0.85,
        marker="o",
        markersize=14,
        ax=ax,
    )

# Add entity labels at both ends
for _idx, row in df.iterrows():
    color = colors[row["direction"]]
    q1_val = row["Q1 Revenue ($M)"]
    q4_val = row["Q4 Revenue ($M)"]

    # Left labels (Q1)
    ax.annotate(
        f"{row['entity']} ({q1_val})",
        xy=(0, q1_val),
        xytext=(-12, 0),
        textcoords="offset points",
        fontsize=15,
        color=color,
        ha="right",
        va="center",
        fontweight="bold",
    )
    # Right labels (Q4)
    ax.annotate(
        f"({q4_val}) {row['entity']}",
        xy=(1, q4_val),
        xytext=(12, 0),
        textcoords="offset points",
        fontsize=15,
        color=color,
        ha="left",
        va="center",
        fontweight="bold",
    )

# Style adjustments
ax.set_xlabel("")
ax.set_ylabel("Revenue ($M)", fontsize=20)
ax.set_title("slope-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-0.15, 1.15)

# Add padding to y-axis for labels
y_min = min(df["Q1 Revenue ($M)"].min(), df["Q4 Revenue ($M)"].min())
y_max = max(df["Q1 Revenue ($M)"].max(), df["Q4 Revenue ($M)"].max())
y_padding = (y_max - y_min) * 0.08
ax.set_ylim(y_min - y_padding, y_max + y_padding)

ax.grid(True, alpha=0.3, linestyle="--")

# Add legend for direction
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=3.5, marker="o", markersize=10, label="Increase"),
    Line2D([0], [0], color="#FFD43B", linewidth=3.5, marker="o", markersize=10, label="Decrease"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.subplots_adjust(left=0.22, right=0.78)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
