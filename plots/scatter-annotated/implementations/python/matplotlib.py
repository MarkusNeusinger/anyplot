""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Technology companies with market cap and revenue
# Points intentionally spread out to minimize annotation overlap
np.random.seed(42)
companies = [
    "TechCorp",
    "DataSys",
    "CloudNet",
    "ByteWorks",
    "QuantumAI",
    "NexGen",
    "CyberFlow",
    "InfoPrime",
    "CodeLabs",
    "DigiCore",
    "NetSphere",
    "AlgoTech",
    "VisionX",
    "PulseTech",
    "ZetaLogic",
]
# Market cap in billions (x-axis)
market_cap = np.array([55, 135, 105, 18, 225, 70, 120, 45, 165, 85, 30, 195, 150, 175, 60])
# Annual revenue in billions (y-axis)
revenue = np.array([12, 42, 30, 4, 65, 18, 38, 10, 52, 24, 6, 58, 45, 50, 15])

# Create figure (16:9 landscape)
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter plot with Python Blue color
ax.scatter(market_cap, revenue, s=250, alpha=0.7, color="#306998", edgecolors="white", linewidths=2, zorder=3)

# Custom annotation offsets for each point to avoid overlap
# Positive x_offset = right, negative = left
# Positive y_offset = up, negative = down
offsets = [
    (10, -10),  # TechCorp - below right
    (-10, 8),  # DataSys - above left
    (10, 8),  # CloudNet - above right
    (-10, -12),  # ByteWorks - below left
    (10, 8),  # QuantumAI - above right
    (-10, 8),  # NexGen - above left
    (10, -10),  # CyberFlow - below right
    (10, -10),  # InfoPrime - below right (adjusted)
    (-12, 8),  # CodeLabs - above left (adjusted)
    (10, 8),  # DigiCore - above right
    (-10, -10),  # NetSphere - below left (adjusted)
    (10, -12),  # AlgoTech - below right
    (10, 8),  # VisionX - above right (adjusted)
    (10, 10),  # PulseTech - above right (adjusted)
    (-10, -10),  # ZetaLogic - below left (adjusted)
]

# Annotate each point with company name
for i, company in enumerate(companies):
    x_offset, y_offset = offsets[i]
    ha = "left" if x_offset > 0 else "right"

    ax.annotate(
        company,
        xy=(market_cap[i], revenue[i]),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        fontsize=13,
        color="#333333",
        fontweight="medium",
        ha=ha,
        va="center",
        arrowprops={"arrowstyle": "-", "color": "#888888", "lw": 1, "connectionstyle": "arc3,rad=0"},
        zorder=4,
    )

# Styling
ax.set_xlabel("Market Capitalization ($ Billions)", fontsize=20)
ax.set_ylabel("Annual Revenue ($ Billions)", fontsize=20)
ax.set_title("scatter-annotated · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", zorder=1)

# Set axis limits with padding
ax.set_xlim(0, 240)
ax.set_ylim(0, 70)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
