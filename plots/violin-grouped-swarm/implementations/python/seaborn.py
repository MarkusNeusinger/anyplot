""" pyplots.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Response times across task types and expertise levels
np.random.seed(42)

categories = ["Simple Task", "Moderate Task", "Complex Task"]
groups = ["Novice", "Expert"]

data = []
for cat in categories:
    for grp in groups:
        # Create different distributions based on task complexity and expertise
        if cat == "Simple Task":
            base_mean = 200 if grp == "Novice" else 150
            base_std = 40 if grp == "Novice" else 25
        elif cat == "Moderate Task":
            base_mean = 400 if grp == "Novice" else 280
            base_std = 80 if grp == "Novice" else 50
        else:  # Complex Task
            base_mean = 700 if grp == "Novice" else 450
            base_std = 120 if grp == "Novice" else 80

        values = np.random.normal(base_mean, base_std, 40)
        values = np.clip(values, 50, 1000)  # Keep values in realistic range

        for v in values:
            data.append({"Task Type": cat, "Expertise": grp, "Response Time (ms)": v})

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom color palette using Python colors
colors = {"Novice": "#306998", "Expert": "#FFD43B"}

# Violin plot with transparency
sns.violinplot(
    data=df,
    x="Task Type",
    y="Response Time (ms)",
    hue="Expertise",
    palette=colors,
    alpha=0.5,
    inner=None,  # Remove inner elements, swarm will show data
    ax=ax,
    linewidth=2,
)

# Swarm overlay with matching colors and dodging
sns.swarmplot(
    data=df,
    x="Task Type",
    y="Response Time (ms)",
    hue="Expertise",
    palette=colors,
    dodge=True,
    size=5,
    alpha=0.8,
    ax=ax,
    legend=False,  # Use violin legend only
)

# Labels and styling
ax.set_xlabel("Task Type", fontsize=20)
ax.set_ylabel("Response Time (ms)", fontsize=20)
ax.set_title("violin-grouped-swarm · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Legend styling
ax.legend(title="Expertise", fontsize=14, title_fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
