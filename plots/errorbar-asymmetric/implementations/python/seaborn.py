""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data: Battery life measurements across device models (10th-90th percentile)
np.random.seed(42)

devices = ["Model A", "Model B", "Model C", "Model D", "Model E", "Model F", "Model G", "Model H"]
x = np.arange(len(devices))

# Central values (median battery life in hours)
y = np.array([8.5, 12.3, 6.2, 15.8, 9.7, 11.2, 7.4, 14.1])

# Asymmetric errors (10th-90th percentile bounds)
# Lower errors: distance from median to 10th percentile
error_lower = np.array([1.2, 2.5, 0.8, 3.2, 1.5, 2.0, 1.0, 2.8])
# Upper errors: distance from median to 90th percentile
error_upper = np.array([2.8, 1.5, 2.2, 1.8, 3.5, 1.2, 2.6, 1.4])

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot points using seaborn scatterplot
sns.scatterplot(x=x, y=y, s=400, color="#306998", zorder=5, ax=ax)

# Add asymmetric error bars using matplotlib errorbar (seaborn doesn't have native asymmetric errorbar)
ax.errorbar(
    x=x,
    y=y,
    yerr=[error_lower, error_upper],
    fmt="none",
    ecolor="#306998",
    elinewidth=3,
    capsize=10,
    capthick=3,
    zorder=4,
)

# Style
ax.set_xticks(x)
ax.set_xticklabels(devices, fontsize=16)
ax.set_xlabel("Device Model", fontsize=20)
ax.set_ylabel("Battery Life (hours)", fontsize=20)
ax.set_title("errorbar-asymmetric · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="y", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Add annotation explaining the error bars
ax.annotate(
    "10th–90th percentile",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.8},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
