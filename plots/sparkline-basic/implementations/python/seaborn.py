""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - simulated monthly revenue trend (24 months)
np.random.seed(42)
values = 100 + np.cumsum(np.random.randn(24) * 5)

# Create figure with proper canvas size (4800x2700 at dpi=300)
# Sparkline is placed centrally with appropriate padding
fig, ax = plt.subplots(figsize=(16, 9))

# Set background color for visual appeal
fig.patch.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

# Plot sparkline using seaborn lineplot
x = np.arange(len(values))
sns.lineplot(x=x, y=values, ax=ax, color="#306998", linewidth=4)

# Add subtle fill under the line for area effect
ax.fill_between(x, values.min() - 5, values, alpha=0.15, color="#306998")

# Highlight min and max points with colored dots
min_idx = np.argmin(values)
max_idx = np.argmax(values)
ax.scatter([min_idx], [values[min_idx]], color="#d62728", s=300, zorder=5, edgecolors="white", linewidths=2)
ax.scatter([max_idx], [values[max_idx]], color="#2ca02c", s=300, zorder=5, edgecolors="white", linewidths=2)

# Highlight first and last points for reference
ax.scatter([0], [values[0]], color="#FFD43B", s=200, zorder=5, edgecolors="#306998", linewidths=2)
ax.scatter([len(values) - 1], [values[-1]], color="#FFD43B", s=200, zorder=5, edgecolors="#306998", linewidths=2)

# Remove all chart chrome for sparkline aesthetic (no axes, labels, gridlines)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

# Adjust y-limits to give breathing room
y_range = values.max() - values.min()
ax.set_ylim(values.min() - y_range * 0.15, values.max() + y_range * 0.25)

# Title
ax.set_title("sparkline-basic · seaborn · pyplots.ai", fontsize=28, pad=30, fontweight="bold")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
