""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Population pyramid showing age distribution by gender
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_population = [4200, 4500, 5100, 5400, 4800, 4200, 3500, 2200, 1100]
female_population = [4000, 4300, 4900, 5200, 4700, 4400, 3800, 2800, 1700]

# Create DataFrame with male values as negative for left-side display
df = pd.DataFrame(
    {
        "Age Group": age_groups * 2,
        "Population": [-m for m in male_population] + female_population,
        "Gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use barplot with hue for proper color distinction
sns.barplot(
    data=df,
    y="Age Group",
    x="Population",
    hue="Gender",
    hue_order=["Male", "Female"],
    palette={"Male": "#306998", "Female": "#FFD43B"},
    ax=ax,
    dodge=False,
    orient="h",
    width=0.8,
)

# Styling
ax.set_xlabel("Population (thousands)", fontsize=20)
ax.set_ylabel("Age Group", fontsize=20)
ax.set_title("pyramid-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Make x-axis symmetric
max_val = max(max(male_population), max(female_population))
ax.set_xlim(-max_val * 1.15, max_val * 1.15)

# Custom x-tick labels to show absolute values
ticks = [-6000, -4000, -2000, 0, 2000, 4000, 6000]
ax.set_xticks(ticks)
ax.set_xticklabels([f"{abs(t):,}" for t in ticks])

# Add subtle vertical line at center
ax.axvline(x=0, color="black", linewidth=1.5, alpha=0.6)

# Grid
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Legend
ax.legend(title="Gender", fontsize=14, title_fontsize=16, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
