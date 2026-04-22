""" pyplots.ai
pie-basic: Basic Pie Chart
Library: matplotlib 3.10.8 | Python 3.14.0
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt


# Data - Global cloud infrastructure market share (2024)
companies = ["AWS", "Azure", "Google Cloud", "Alibaba Cloud", "Others"]
market_share = [31, 25, 11, 4, 29]

# Colors - Python Blue first, then harmonious colorblind-safe colors
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B", "#95A5A6"]

# Explode the largest slice slightly for emphasis
explode = [0.05, 0, 0, 0, 0]

# Create plot (3600x3600 px - square format ideal for pie charts)
fig, ax = plt.subplots(figsize=(12, 12))

wedges, texts, autotexts = ax.pie(
    market_share,
    labels=companies,
    autopct="%1.1f%%",
    explode=explode,
    colors=colors,
    startangle=90,
    shadow=True,
    textprops={"fontsize": 22},
    wedgeprops={"linewidth": 2.5, "edgecolor": "white"},
    pctdistance=0.55,
)

# Style percentage labels
for autotext in autotexts:
    autotext.set_fontsize(20)
    autotext.set_fontweight("bold")
    autotext.set_color("white")

# Title
ax.set_title("pie-basic · matplotlib · pyplots.ai", fontsize=28, fontweight="medium", pad=30)

# Legend with contextual title
ax.legend(
    wedges,
    [f"{c} ({s}%)" for c, s in zip(companies, market_share, strict=True)],
    title="Cloud Providers",
    loc="lower center",
    bbox_to_anchor=(0.5, -0.05),
    fontsize=18,
    title_fontsize=20,
    ncol=3,
    framealpha=0.9,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
