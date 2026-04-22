""" pyplots.ai
area-stacked: Stacked Area Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_theme(style="whitegrid")

# Data: Monthly revenue by product category over 2 years
np.random.seed(42)
months = pd.date_range("2023-01", periods=24, freq="ME")

# Create realistic revenue trends with seasonality
base_electronics = 45 + np.sin(np.linspace(0, 4 * np.pi, 24)) * 8
base_clothing = 35 + np.sin(np.linspace(0.5, 4.5 * np.pi, 24)) * 6
base_home = 25 + np.sin(np.linspace(1, 5 * np.pi, 24)) * 5
base_sports = 20 + np.sin(np.linspace(1.5, 5.5 * np.pi, 24)) * 4

# Add slight growth trend and noise
growth = np.linspace(1, 1.15, 24)
electronics = (base_electronics * growth + np.random.randn(24) * 2).clip(20)
clothing = (base_clothing * growth + np.random.randn(24) * 1.5).clip(15)
home = (base_home * growth + np.random.randn(24) * 1.2).clip(10)
sports = (base_sports * growth + np.random.randn(24) * 1).clip(8)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors - Python Blue as primary, then harmonious palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]
labels = ["Electronics", "Clothing", "Home & Garden", "Sports"]

# Stack the areas (ordered by typical size, largest at bottom)
ax.stackplot(months, electronics, clothing, home, sports, labels=labels, colors=colors, alpha=0.85)

# Style the plot
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Revenue (Million $)", fontsize=20)
ax.set_title("area-stacked · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

# Configure legend
ax.legend(loc="upper left", fontsize=16, framealpha=0.9, title="Product Category", title_fontsize=18)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Ensure baseline starts at zero
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
