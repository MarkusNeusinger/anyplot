""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from adjustText import adjust_text


# Set seaborn theme for consistent styling
sns.set_theme(style="whitegrid", palette="colorblind")

# Data: Technology companies with revenue vs market cap
np.random.seed(42)
companies = [
    "TechCorp",
    "DataSys",
    "CloudNet",
    "AILabs",
    "CyberSec",
    "NetFlow",
    "AppWorks",
    "CodeBase",
    "DevOps",
    "QuantumX",
    "ByteLogic",
    "StreamIO",
    "VirtualAI",
    "SecureIT",
    "SmartHub",
]
n_points = len(companies)

# Revenue (billions) and Market Cap (billions) - realistic tech company scale
revenue = np.random.uniform(5, 80, n_points)
market_cap = revenue * np.random.uniform(2, 8, n_points) + np.random.randn(n_points) * 10

# Create DataFrame for seaborn
df = pd.DataFrame({"company": companies, "revenue": revenue, "market_cap": market_cap})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn scatterplot with DataFrame
sns.scatterplot(
    data=df,
    x="revenue",
    y="market_cap",
    s=200,
    alpha=0.7,
    color=sns.color_palette("colorblind")[0],
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
)

# Create text annotations with initial offset (collect for adjustText)
texts = []
for _, row in df.iterrows():
    # Start labels slightly offset from points
    offset_x = 3.0
    offset_y = 12.0
    text = ax.text(
        row["revenue"] + offset_x,
        row["market_cap"] + offset_y,
        row["company"],
        fontsize=14,
        color="#333333",
        ha="left",
        va="bottom",
    )
    texts.append(text)

# Use adjustText to prevent label overlaps with connecting lines
adjust_text(
    texts,
    x=df["revenue"].values,
    y=df["market_cap"].values,
    arrowprops={"arrowstyle": "-", "color": "#888888", "alpha": 0.6, "lw": 1.0},
    expand=(1.5, 1.5),
    force_text=(0.3, 0.3),
    force_points=(0.3, 0.3),
    ax=ax,
)

# Labels and styling
ax.set_xlabel("Annual Revenue ($ Billion)", fontsize=20)
ax.set_ylabel("Market Capitalization ($ Billion)", fontsize=20)
ax.set_title("scatter-annotated · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Adjust axis limits to accommodate labels
ax.set_xlim(0, max(revenue) + 15)
ax.set_ylim(min(market_cap) - 30, max(market_cap) + 60)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
