"""pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-06
"""

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
sns.set_style("white")
sns.set_context("talk", font_scale=1.2)

cmap = sns.diverging_palette(h_neg=240, h_pos=15, s=85, l=35, sep=1, as_cmap=True)
vmax = max(abs(anomalies.min()), abs(anomalies.max()))

fig, ax = plt.subplots(figsize=(18, 6))

ax.set_position([0.01, 0.05, 0.98, 0.75])

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
    linewidths=0,
    linecolor="none",
)

# Style
ax.set_axis_off()
sns.despine(fig=fig, left=True, bottom=True, right=True, top=True)
fig.patch.set_facecolor("#f0f0f0")

fig.text(
    0.5,
    0.90,
    "heatmap-stripes-climate \u00b7 seaborn \u00b7 pyplots.ai",
    ha="center",
    va="center",
    fontsize=24,
    fontweight="medium",
    color="#333333",
    fontstyle="italic",
)

# Year markers
fig.text(0.02, 0.02, str(years[0]), fontsize=16, color="#555555", ha="left")
fig.text(0.98, 0.02, str(years[-1]), fontsize=16, color="#555555", ha="right")

# Save
plt.savefig("plot.png", dpi=300, facecolor=fig.get_facecolor())
