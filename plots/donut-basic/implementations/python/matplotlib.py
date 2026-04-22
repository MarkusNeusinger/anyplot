""" pyplots.ai
donut-basic: Basic Donut Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt


# Data - Budget allocation by category
categories = ["Marketing", "Development", "Operations", "Sales", "Support"]
values = [25, 35, 15, 18, 7]
total = sum(values)

# Colors - Python Blue as primary, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#5BA0D0", "#8FBC8F", "#DDA0DD"]

# Create plot (3600x3600 px - square for symmetric pie/donut)
fig, ax = plt.subplots(figsize=(12, 12))

# Create donut chart with wedgeprops for ring width
wedges, texts, autotexts = ax.pie(
    values,
    labels=categories,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors,
    wedgeprops={"width": 0.5, "edgecolor": "white", "linewidth": 2},
    pctdistance=0.75,
    labeldistance=1.1,
)

# Style labels and percentages for 3600x3600 px
for text in texts:
    text.set_fontsize(20)
for autotext in autotexts:
    autotext.set_fontsize(16)
    autotext.set_color("white")
    autotext.set_fontweight("bold")

# Add center text with total
ax.text(0, 0, f"Total\n${total}K", ha="center", va="center", fontsize=32, fontweight="bold", color="#306998")

# Ensure circular shape
ax.set_aspect("equal")

ax.set_title("donut-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
