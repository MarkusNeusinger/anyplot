""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Top 10 programming languages by popularity (example survey)
np.random.seed(42)
categories = ["Python", "JavaScript", "Java", "C++", "TypeScript", "C#", "Go", "Rust", "PHP", "Swift"]
values = [68.2, 62.5, 45.8, 42.1, 38.7, 33.5, 28.4, 25.1, 22.8, 18.3]

# Sort by value for better visual comparison (smallest to largest, so largest at top)
sorted_indices = np.argsort(values)
categories = [categories[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Horizontal bar chart
y_positions = np.arange(len(categories))
bars = ax.barh(y_positions, values, height=0.65, color="#306998", edgecolor="#1e4c6b", linewidth=1.5)

# Add value labels at the end of bars
for bar, value in zip(bars, values, strict=True):
    ax.text(
        bar.get_width() + 1.2,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.1f}%",
        va="center",
        ha="left",
        fontsize=16,
        color="#333333",
    )

# Labels and styling
ax.set_xlabel("Popularity (%)", fontsize=20)
ax.set_ylabel("Programming Language", fontsize=20)
ax.set_title("bar-horizontal · matplotlib · pyplots.ai", fontsize=24)
ax.set_yticks(y_positions)
ax.set_yticklabels(categories)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, max(values) * 1.2)

# Subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
