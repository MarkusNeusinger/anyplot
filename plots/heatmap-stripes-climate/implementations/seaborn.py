""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-06
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

baseline_trend = np.concatenate(
    [
        np.linspace(-0.3, -0.2, 60),
        np.linspace(-0.2, -0.1, 40),
        np.linspace(-0.1, 0.1, 30),
        np.linspace(0.1, 0.5, 25),
        np.linspace(0.5, 1.3, 20),
    ]
)
noise = np.random.normal(0, 0.12, n_years)
anomalies = baseline_trend + noise

anomaly_matrix = anomalies.reshape(1, -1)

# Plot
cmap = mcolors.LinearSegmentedColormap.from_list(
    "warming_stripes",
    ["#08306b", "#2171b5", "#6baed6", "#c6dbef", "#ffffff", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
)
vmax = max(abs(anomalies.min()), abs(anomalies.max()))

fig, ax = plt.subplots(figsize=(16, 5))

sns.heatmap(
    anomaly_matrix,
    ax=ax,
    cmap=cmap,
    center=0,
    vmin=-vmax,
    vmax=vmax,
    cbar=False,
    xticklabels=False,
    yticklabels=False,
    square=False,
)

# Style
ax.set_axis_off()

fig.subplots_adjust(left=0, right=1, top=0.88, bottom=0.02)
fig.text(
    0.5,
    0.94,
    "heatmap-stripes-climate \u00b7 seaborn \u00b7 pyplots.ai",
    ha="center",
    va="center",
    fontsize=20,
    fontweight="medium",
)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
