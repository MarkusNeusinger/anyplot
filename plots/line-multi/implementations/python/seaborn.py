""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales patterns for different product categories
# Electronics: Strong growth with holiday spike
electronics = 50 + np.cumsum(np.random.randn(12) * 5 + 3)
electronics[10:] += 30  # Holiday boost

# Apparel: Seasonal with summer and winter peaks
apparel = 40 + 15 * np.sin(np.linspace(0, 2 * np.pi, 12)) + np.random.randn(12) * 3

# Home & Garden: Spring/summer peak
home_garden = 30 + 20 * np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, 12)) + np.random.randn(12) * 4

# Sports: Steady with slight seasonal variation
sports = 35 + 5 * np.sin(np.linspace(0, 2 * np.pi, 12) + np.pi / 4) + np.cumsum(np.random.randn(12) * 2)

# Create long-format DataFrame for seaborn
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales (thousands USD)": np.concatenate([electronics, apparel, home_garden, sports]),
        "Product Line": ["Electronics"] * 12 + ["Apparel"] * 12 + ["Home & Garden"] * 12 + ["Sports"] * 12,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom color palette using Python colors first
colors = ["#306998", "#FFD43B", "#4CAF50", "#E91E63"]

sns.lineplot(
    data=df,
    x="Month",
    y="Sales (thousands USD)",
    hue="Product Line",
    style="Product Line",
    markers=True,
    dashes=False,
    linewidth=3,
    markersize=12,
    palette=colors,
    ax=ax,
)

# Styling
ax.set_title("line-multi · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales (thousands USD)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Set x-ticks to month names
ax.set_xticks(months)
ax.set_xticklabels(month_labels, fontsize=16)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")

# Legend styling
ax.legend(title="Product Line", title_fontsize=18, fontsize=16, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
