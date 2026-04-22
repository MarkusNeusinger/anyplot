""" pyplots.ai
strip-basic: Basic Strip Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Survey response scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
data = {"Department": [], "Satisfaction Score": []}

# Create varied distributions for each department
for dept in departments:
    if dept == "Engineering":
        # Higher scores, tighter distribution
        scores = np.random.normal(78, 8, 35)
    elif dept == "Marketing":
        # Medium scores, wider spread
        scores = np.random.normal(72, 12, 40)
    elif dept == "Sales":
        # Bimodal-ish distribution with some outliers
        scores = np.concatenate([np.random.normal(65, 6, 25), np.random.normal(80, 5, 15)])
    else:  # HR
        # Lower average, moderate spread
        scores = np.random.normal(68, 10, 30)

    # Clip scores to realistic range
    scores = np.clip(scores, 40, 100)

    data["Department"].extend([dept] * len(scores))
    data["Satisfaction Score"].extend(scores)

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.stripplot(
    data=df,
    x="Department",
    y="Satisfaction Score",
    hue="Department",
    palette=["#306998", "#FFD43B", "#4B8BBE", "#646464"],
    alpha=0.7,
    size=12,
    jitter=0.25,
    ax=ax,
    legend=False,
)

# Add horizontal lines for group means
means = df.groupby("Department")["Satisfaction Score"].mean()
for i, dept in enumerate(departments):
    ax.hlines(means[dept], i - 0.35, i + 0.35, colors="#D62728", linewidth=2.5, linestyles="--")

# Styling
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Satisfaction Score", fontsize=20)
ax.set_title("strip-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(35, 105)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Add legend for mean line
ax.plot([], [], color="#D62728", linestyle="--", linewidth=2.5, label="Group Mean")
ax.legend(fontsize=14, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
