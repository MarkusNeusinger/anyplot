""" pyplots.ai
donut-basic: Basic Donut Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Budget allocation by department
data = pd.DataFrame(
    {
        "category": ["Marketing", "Engineering", "Operations", "Sales", "HR", "R&D"],
        "value": [25000, 45000, 18000, 32000, 12000, 28000],
    }
)

# Calculate percentages
total = data["value"].sum()
data["percentage"] = (data["value"] / total * 100).round(1)

# Set seaborn style
sns.set_theme(style="white")

# Create figure (square for symmetric donut)
fig, ax = plt.subplots(figsize=(12, 12))

# Define colors using seaborn color palette
colors = sns.color_palette("Set2", n_colors=len(data))

# Create donut chart using matplotlib pie (seaborn is built on matplotlib)
wedges, texts, autotexts = ax.pie(
    data["value"],
    labels=data["category"],
    autopct="%1.1f%%",
    startangle=90,
    colors=colors,
    wedgeprops={"width": 0.5, "edgecolor": "white", "linewidth": 2},
    pctdistance=0.75,
    labeldistance=1.15,
)

# Style the text for large canvas
for text in texts:
    text.set_fontsize(20)
    text.set_fontweight("medium")

for autotext in autotexts:
    autotext.set_fontsize(16)
    autotext.set_fontweight("bold")
    autotext.set_color("white")

# Add center text with total
center_text = f"Total\n${total:,.0f}"
ax.text(0, 0, center_text, ha="center", va="center", fontsize=28, fontweight="bold", color="#333333")

# Title
ax.set_title("donut-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Equal aspect ratio for circular shape
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
