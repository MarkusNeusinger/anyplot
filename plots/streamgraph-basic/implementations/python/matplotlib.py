""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Monthly streaming hours by music genre over two years
np.random.seed(42)

# 24 months of data
months = np.arange(24)
month_labels = [
    "Jan'23",
    "Feb'23",
    "Mar'23",
    "Apr'23",
    "May'23",
    "Jun'23",
    "Jul'23",
    "Aug'23",
    "Sep'23",
    "Oct'23",
    "Nov'23",
    "Dec'23",
    "Jan'24",
    "Feb'24",
    "Mar'24",
    "Apr'24",
    "May'24",
    "Jun'24",
    "Jul'24",
    "Aug'24",
    "Sep'24",
    "Oct'24",
    "Nov'24",
    "Dec'24",
]

# Generate realistic genre streaming data with trends
# Pop - consistently high, slight growth
pop = 50 + 10 * np.sin(months / 6) + np.random.randn(24) * 3 + months * 0.3

# Rock - stable with seasonal variation
rock = 35 + 8 * np.cos(months / 4) + np.random.randn(24) * 2

# Hip-Hop - growing trend
hiphop = 25 + months * 0.8 + 5 * np.sin(months / 3) + np.random.randn(24) * 3

# Electronic - summer peaks
electronic = 20 + 15 * np.sin((months - 3) / 6 * np.pi) + np.random.randn(24) * 2

# Jazz - steady, slight decline
jazz = 18 - months * 0.15 + 4 * np.cos(months / 5) + np.random.randn(24) * 1.5

# Classical - winter peaks
classical = 15 + 8 * np.cos((months) / 6 * np.pi) + np.random.randn(24) * 1.5

# Ensure all values are positive
pop = np.maximum(pop, 5)
rock = np.maximum(rock, 5)
hiphop = np.maximum(hiphop, 5)
electronic = np.maximum(electronic, 5)
jazz = np.maximum(jazz, 5)
classical = np.maximum(classical, 5)

# Stack the data
data = np.vstack([pop, rock, hiphop, electronic, jazz, classical])
categories = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

# Colors - starting with Python Blue/Yellow, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#E07A5F", "#81B29A", "#F2CC8F", "#3D405B"]

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Create streamgraph with symmetric baseline (wiggle for stream-like appearance)
ax.stackplot(months, data, labels=categories, colors=colors, baseline="wiggle", alpha=0.85)

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_title("streamgraph-basic · matplotlib · pyplots.ai", fontsize=24)

# X-axis labels
ax.set_xticks(months[::3])
ax.set_xticklabels([month_labels[i] for i in range(0, 24, 3)], fontsize=16)
ax.tick_params(axis="y", labelsize=16)

# Remove y-axis ticks for cleaner stream appearance (values are relative)
ax.set_yticks([])

# Add legend
ax.legend(loc="upper left", fontsize=16, framealpha=0.9)

# Subtle styling - remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

# Set x limits to remove padding
ax.set_xlim(0, 23)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
