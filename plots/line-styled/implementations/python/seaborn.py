""" pyplots.ai
line-styled: Styled Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Temperature trends across seasons
np.random.seed(42)
months = np.arange(1, 13)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Temperature patterns for different regions (°C)
base_temp = np.array([5, 7, 12, 16, 21, 25, 28, 27, 23, 17, 11, 6])
coastal = base_temp + np.random.randn(12) * 0.5 + 3
continental = base_temp + np.random.randn(12) * 0.5 - 2
mountain = base_temp + np.random.randn(12) * 0.5 - 8
mediterranean = base_temp + np.random.randn(12) * 0.5 + 5

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Line styles: solid, dashed, dotted, dashdot
line_styles = ["-", "--", ":", "-."]
colors = ["#306998", "#FFD43B", "#2E8B57", "#DC143C"]
labels = ["Coastal", "Continental", "Mountain", "Mediterranean"]
data_series = [coastal, continental, mountain, mediterranean]

for data, label, ls, color in zip(data_series, labels, line_styles, colors, strict=True):
    sns.lineplot(x=months, y=data, ax=ax, linestyle=ls, linewidth=3.5, color=color, label=label)

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-styled · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(months)
ax.set_xticklabels(month_names, fontsize=14)
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
