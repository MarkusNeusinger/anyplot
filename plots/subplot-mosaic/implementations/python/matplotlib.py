""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)

# Time series data for main overview chart
dates = np.arange(100)
sales = np.cumsum(np.random.randn(100) * 5 + 2) + 500

# Category data for bar chart
categories = ["Product A", "Product B", "Product C", "Product D"]
values = [85, 120, 95, 110]

# Scatter data for correlation plot
x_scatter = np.random.normal(50, 15, 80)
y_scatter = x_scatter * 0.8 + np.random.normal(0, 10, 80)

# Histogram data
measurements = np.random.normal(100, 20, 200)

# Metric values for small panels
metrics = {"Growth": 12.5, "Conversion": 3.2, "Retention": 87.4}

# Create mosaic layout: "AAB;AAB;CDE" pattern
# A = large overview (spans 2 rows, 2 cols), B = bar chart (right side, 2 rows)
# C, D, E = three small panels at bottom
mosaic = """
AAB
AAB
CDE
"""

fig, axes = plt.subplot_mosaic(mosaic, figsize=(16, 9))

# A: Main time series overview
axes["A"].plot(dates, sales, linewidth=3, color="#306998")
axes["A"].fill_between(dates, sales.min(), sales, alpha=0.3, color="#306998")
axes["A"].set_xlabel("Day", fontsize=18)
axes["A"].set_ylabel("Cumulative Sales ($)", fontsize=18)
axes["A"].set_title("Sales Overview", fontsize=22)
axes["A"].tick_params(axis="both", labelsize=14)
axes["A"].grid(True, alpha=0.3, linestyle="--")

# B: Bar chart for categories
bars = axes["B"].barh(categories, values, color="#FFD43B", edgecolor="#306998", linewidth=2)
axes["B"].set_xlabel("Units Sold", fontsize=18)
axes["B"].set_title("Product Performance", fontsize=22)
axes["B"].tick_params(axis="both", labelsize=14)
axes["B"].grid(True, alpha=0.3, linestyle="--", axis="x")
# Add value labels
for bar, val in zip(bars, values, strict=True):
    axes["B"].text(val + 2, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=14)

# C: Scatter plot
axes["C"].scatter(x_scatter, y_scatter, s=100, alpha=0.7, color="#306998", edgecolor="white", linewidth=1)
axes["C"].set_xlabel("Feature X", fontsize=16)
axes["C"].set_ylabel("Feature Y", fontsize=16)
axes["C"].set_title("Correlation", fontsize=20)
axes["C"].tick_params(axis="both", labelsize=12)
axes["C"].grid(True, alpha=0.3, linestyle="--")

# D: Histogram
axes["D"].hist(measurements, bins=20, color="#306998", edgecolor="white", linewidth=1, alpha=0.8)
axes["D"].set_xlabel("Value", fontsize=16)
axes["D"].set_ylabel("Frequency", fontsize=16)
axes["D"].set_title("Distribution", fontsize=20)
axes["D"].tick_params(axis="both", labelsize=12)
axes["D"].grid(True, alpha=0.3, linestyle="--", axis="y")

# E: Metrics display
axes["E"].set_xlim(0, 1)
axes["E"].set_ylim(0, 1)
axes["E"].axis("off")
axes["E"].set_title("Key Metrics", fontsize=20)
y_positions = [0.75, 0.45, 0.15]
for (name, value), y_pos in zip(metrics.items(), y_positions, strict=True):
    axes["E"].text(0.5, y_pos, name, ha="center", va="center", fontsize=16, fontweight="bold")
    if name == "Growth":
        axes["E"].text(0.5, y_pos - 0.12, f"+{value}%", ha="center", va="center", fontsize=24, color="#306998")
    elif name == "Conversion":
        axes["E"].text(0.5, y_pos - 0.12, f"{value}%", ha="center", va="center", fontsize=24, color="#306998")
    else:
        axes["E"].text(0.5, y_pos - 0.12, f"{value}%", ha="center", va="center", fontsize=24, color="#306998")
# Add box around metrics
axes["E"].add_patch(plt.Rectangle((0.05, 0.02), 0.9, 0.96, fill=False, edgecolor="#306998", linewidth=2))

# Main title
fig.suptitle("subplot-mosaic · matplotlib · pyplots.ai", fontsize=26, fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
