""" pyplots.ai
box-grouped: Grouped Box Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Employee performance scores by department and experience level
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "Support"]
subcategories = ["Junior", "Mid-Level", "Senior"]

data = []
for cat in categories:
    for subcat in subcategories:
        n = np.random.randint(30, 50)
        # Different distributions per group to show variety
        if cat == "Engineering":
            base = {"Junior": 65, "Mid-Level": 75, "Senior": 85}[subcat]
            spread = {"Junior": 12, "Mid-Level": 10, "Senior": 8}[subcat]
        elif cat == "Marketing":
            base = {"Junior": 60, "Mid-Level": 72, "Senior": 82}[subcat]
            spread = {"Junior": 15, "Mid-Level": 11, "Senior": 9}[subcat]
        elif cat == "Sales":
            base = {"Junior": 55, "Mid-Level": 70, "Senior": 88}[subcat]
            spread = {"Junior": 18, "Mid-Level": 14, "Senior": 10}[subcat]
        else:  # Support
            base = {"Junior": 62, "Mid-Level": 74, "Senior": 80}[subcat]
            spread = {"Junior": 10, "Mid-Level": 9, "Senior": 7}[subcat]

        values = np.random.normal(base, spread, n)
        # Add some outliers
        if np.random.random() > 0.5:
            values = np.append(values, base + spread * np.random.choice([-3, 3], size=2))
        values = np.clip(values, 20, 100)

        for v in values:
            data.append({"Department": cat, "Experience": subcat, "Score": v})

df = pd.DataFrame(data)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Use custom color palette with Python colors
colors = ["#306998", "#FFD43B", "#4B8BBE"]

sns.boxplot(
    data=df,
    x="Department",
    y="Score",
    hue="Experience",
    palette=colors,
    ax=ax,
    width=0.7,
    linewidth=2,
    fliersize=8,
    order=categories,
    hue_order=subcategories,
)

# Styling
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Performance Score", fontsize=20)
ax.set_title("box-grouped · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(title="Experience Level", fontsize=14, title_fontsize=16, loc="upper right")
ax.set_ylim(15, 105)
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.xaxis.grid(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
