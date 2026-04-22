""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Programming language popularity survey results
data = {
    "Language": ["Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust", "Swift", "Kotlin"],
    "Respondents": [68, 62, 45, 38, 34, 32, 24, 18, 15, 12],
}
df = pd.DataFrame(data)

# Sort by value for better comparison
df = df.sort_values("Respondents", ascending=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot horizontal bar chart
sns.barplot(
    data=df,
    y="Language",
    x="Respondents",
    hue="Language",
    palette=["#306998"] * len(df),
    legend=False,
    ax=ax,
    orient="h",
)

# Add value labels at the end of each bar
for i, value in enumerate(df["Respondents"]):
    ax.text(value + 1, i, f"{value}%", va="center", fontsize=16, color="#333333")

# Styling
ax.set_xlabel("Percentage of Respondents (%)", fontsize=20)
ax.set_ylabel("Programming Language", fontsize=20)
ax.set_title("bar-horizontal · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Extend x-axis slightly to accommodate labels
ax.set_xlim(0, 78)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
