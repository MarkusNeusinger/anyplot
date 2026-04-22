""" pyplots.ai
swarm-basic: Basic Swarm Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Employee performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
n_per_dept = [45, 38, 52, 40]

data = []
for dept, n in zip(departments, n_per_dept, strict=True):
    if dept == "Engineering":
        # Higher scores, tighter distribution
        scores = np.random.normal(82, 6, n)
    elif dept == "Marketing":
        # Moderate scores, wider spread
        scores = np.random.normal(75, 10, n)
    elif dept == "Sales":
        # Bimodal distribution (high performers and average)
        scores = np.concatenate([np.random.normal(85, 5, n // 2), np.random.normal(68, 7, n - n // 2)])
    else:  # Support
        # Lower scores with some outliers
        scores = np.concatenate(
            [
                np.random.normal(70, 8, n - 3),
                np.array([95, 45, 48]),  # Outliers
            ]
        )

    for score in scores:
        data.append({"Department": dept, "Performance Score": np.clip(score, 30, 100)})

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.swarmplot(
    data=df,
    x="Department",
    y="Performance Score",
    hue="Department",
    palette=["#306998", "#FFD43B", "#4ECDC4", "#E76F51"],
    size=8,
    alpha=0.8,
    ax=ax,
    legend=False,
)

# Add median markers
medians = df.groupby("Department")["Performance Score"].median()
for i, dept in enumerate(departments):
    ax.scatter(i, medians[dept], marker="D", s=150, color="#1a1a2e", edgecolor="white", linewidth=2, zorder=10)

# Styling
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Performance Score", fontsize=20)
ax.set_title("swarm-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")
ax.set_ylim(25, 105)

# Add legend note for median marker
ax.scatter([], [], marker="D", s=100, color="#1a1a2e", edgecolor="white", linewidth=2, label="Median")
ax.legend(fontsize=14, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
