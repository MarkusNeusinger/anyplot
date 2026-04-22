""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

data = []
for condition in conditions:
    # Different distributions per condition to show varied shapes
    if condition == "Control":
        values = np.random.normal(450, 80, n_per_group)
    elif condition == "Low Dose":
        values = np.random.normal(400, 60, n_per_group)
    elif condition == "Medium Dose":
        # Bimodal distribution
        values = np.concatenate(
            [np.random.normal(320, 40, n_per_group // 2), np.random.normal(400, 30, n_per_group // 2)]
        )
    else:  # High Dose
        values = np.random.normal(300, 50, n_per_group)

    for v in values:
        data.append({"Condition": condition, "Reaction Time (ms)": v})

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Violin plot with transparency
sns.violinplot(
    data=df,
    x="Condition",
    y="Reaction Time (ms)",
    hue="Condition",
    palette=["#306998", "#FFD43B", "#4A90A4", "#E8A838"],
    alpha=0.4,
    inner=None,
    legend=False,
    ax=ax,
)

# Swarm plot overlay with contrasting darker color
sns.swarmplot(
    data=df,
    x="Condition",
    y="Reaction Time (ms)",
    hue="Condition",
    palette=["#1a3d5c", "#b39500", "#2d5a66", "#a67520"],
    size=6,
    legend=False,
    ax=ax,
)

# Styling
ax.set_title("violin-swarm · seaborn · pyplots.ai", fontsize=24)
ax.set_xlabel("Condition", fontsize=20)
ax.set_ylabel("Reaction Time (ms)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
