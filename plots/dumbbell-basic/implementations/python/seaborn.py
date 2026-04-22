""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Employee satisfaction scores before and after policy changes
data = {
    "Department": [
        "Engineering",
        "Marketing",
        "Sales",
        "HR",
        "Finance",
        "Operations",
        "Legal",
        "Customer Support",
        "Research",
        "IT",
    ],
    "Before": [65, 58, 72, 61, 55, 68, 52, 70, 63, 59],
    "After": [78, 75, 85, 80, 71, 82, 68, 88, 79, 76],
}
df = pd.DataFrame(data)

# Sort by difference to reveal patterns
df["Difference"] = df["After"] - df["Before"]
df = df.sort_values("Difference", ascending=True).reset_index(drop=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw connecting lines between start and end dots
for i, row in df.iterrows():
    ax.plot([row["Before"], row["After"]], [i, i], color="#888888", linewidth=2, zorder=1)

# Plot dots using seaborn
sns.scatterplot(x=df["Before"], y=range(len(df)), color="#306998", s=400, label="Before Policy", ax=ax, zorder=2)
sns.scatterplot(
    x=df["After"],
    y=range(len(df)),
    color="#FFD43B",
    s=400,
    label="After Policy",
    ax=ax,
    zorder=2,
    edgecolor="#888888",
    linewidth=1,
)

# Style
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["Department"])
ax.set_xlabel("Satisfaction Score (%)", fontsize=20)
ax.set_ylabel("Department", fontsize=20)
ax.set_title("dumbbell-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="x")
ax.legend(fontsize=16, loc="lower right")
ax.set_xlim(45, 95)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
