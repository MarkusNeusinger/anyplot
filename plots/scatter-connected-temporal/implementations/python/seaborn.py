""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection


# Data - Unemployment vs inflation (Phillips curve dynamics, 1990-2023)
np.random.seed(42)
years = np.arange(1990, 2024)
n = len(years)

unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,
        8.1,
        5.4,
        3.6,
        3.6,
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        2.9,
        2.3,
        1.6,
        2.2,
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,
        1.2,
        4.7,
        8.0,
        4.1,
    ]
)

df = pd.DataFrame({"Unemployment Rate (%)": unemployment, "Inflation Rate (%)": inflation, "Year": years})

# Plot setup with seaborn theme
sns.set_theme(style="ticks", rc={"axes.facecolor": "#f0f0f0", "figure.facecolor": "white", "font.family": "sans-serif"})
fig, ax = plt.subplots(figsize=(16, 9))

# Temporal color palette using seaborn's blend palette - darker start for better contrast
palette = sns.color_palette("blend:#5b8db8,#0d1f3c", n_colors=n)
cmap = sns.color_palette("blend:#5b8db8,#0d1f3c", as_cmap=True)

# Connected path using LineCollection for smooth color gradient per segment
points = np.column_stack([unemployment, inflation])
segments = np.array([[points[i], points[i + 1]] for i in range(n - 1)])
norm = plt.Normalize(years[0], years[-1])
lc = LineCollection(segments, cmap=cmap, norm=norm, linewidths=2.8, zorder=2)
lc.set_array(years[:-1].astype(float))
ax.add_collection(lc)

# Scatter markers using seaborn scatterplot with temporal hue
sns.scatterplot(
    data=df,
    x="Unemployment Rate (%)",
    y="Inflation Rate (%)",
    hue="Year",
    palette="blend:#5b8db8,#0d1f3c",
    s=180,
    edgecolor="white",
    linewidth=1.8,
    legend=False,
    zorder=3,
    ax=ax,
)

# Annotate key economic turning points with well-separated positions
key_points = {
    0: (-25, 20),  # 1990 - start, high inflation era
    10: (18, 14),  # 2000 - dot-com boom, low unemployment
    19: (18, -22),  # 2009 - Great Recession peak unemployment
    22: (-40, -22),  # 2012 - recovery midpoint
    29: (-50, -18),  # 2019 - pre-pandemic low unemployment
    n - 1: (20, 14),  # 2023 - post-pandemic normalization
}

for idx, offset in key_points.items():
    color = palette[idx]
    ax.annotate(
        str(years[idx]),
        (unemployment[idx], inflation[idx]),
        textcoords="offset points",
        xytext=offset,
        fontsize=14,
        fontweight="bold",
        color=color,
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.3, "connectionstyle": "arc3,rad=0.2"},
    )

# Narrative subtitle for data storytelling
ax.text(
    0.5,
    1.02,
    "U.S. Phillips Curve Dynamics: Tracing Unemployment vs. Inflation (1990\u20132023)",
    transform=ax.transAxes,
    fontsize=14,
    color="#555555",
    ha="center",
    va="bottom",
    style="italic",
)

# Axis styling - y-only grid for cleaner look
ax.set_xlabel("Unemployment Rate (%)", fontsize=20)
ax.set_ylabel("Inflation Rate (%)", fontsize=20)
ax.set_title("scatter-connected-temporal \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=28)
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.set_xlim(unemployment.min() - 0.8, unemployment.max() + 0.8)
ax.set_ylim(inflation.min() - 1.2, inflation.max() + 1.2)

# Colorbar for temporal encoding
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02, aspect=30, shrink=0.85)
cbar.set_label("Year", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
