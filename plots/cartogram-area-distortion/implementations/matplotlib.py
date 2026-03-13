""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-13
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


# Data - US states with approximate geographic centroids, population, and GDP per capita
np.random.seed(42)

states = {
    "WA": (-122.0, 47.5, 7615),
    "OR": (-120.5, 44.0, 4218),
    "CA": (-119.5, 37.0, 39538),
    "NV": (-116.8, 39.0, 3104),
    "ID": (-114.5, 44.5, 1839),
    "MT": (-109.5, 47.0, 1084),
    "WY": (-107.5, 43.0, 577),
    "UT": (-111.5, 39.5, 3272),
    "CO": (-105.5, 39.0, 5773),
    "AZ": (-111.5, 34.5, 7279),
    "NM": (-106.0, 34.5, 2117),
    "ND": (-100.5, 47.5, 779),
    "SD": (-100.0, 44.5, 887),
    "NE": (-99.8, 41.5, 1962),
    "KS": (-98.5, 38.5, 2937),
    "OK": (-97.5, 35.5, 3959),
    "TX": (-99.0, 31.5, 29145),
    "MN": (-94.5, 46.0, 5640),
    "IA": (-93.5, 42.0, 3190),
    "MO": (-92.5, 38.5, 6154),
    "AR": (-92.5, 35.0, 3012),
    "LA": (-92.0, 31.0, 4657),
    "WI": (-89.5, 44.5, 5822),
    "IL": (-89.0, 40.0, 12812),
    "MI": (-84.5, 44.0, 10077),
    "IN": (-86.0, 40.0, 6733),
    "OH": (-82.5, 40.5, 11799),
    "KY": (-85.5, 37.8, 4506),
    "TN": (-86.0, 35.8, 6911),
    "MS": (-89.5, 32.5, 2961),
    "AL": (-86.8, 32.8, 5024),
    "GA": (-83.5, 33.0, 10712),
    "FL": (-81.5, 28.5, 21538),
    "SC": (-81.0, 34.0, 5119),
    "NC": (-79.5, 35.5, 10439),
    "VA": (-79.0, 37.5, 8631),
    "WV": (-80.5, 38.8, 1794),
    "PA": (-77.5, 41.0, 13002),
    "NY": (-75.5, 43.0, 20201),
    "NJ": (-74.5, 40.0, 9289),
    "MD": (-76.5, 39.0, 6177),
    "DE": (-75.5, 39.0, 990),
    "CT": (-72.7, 41.6, 3606),
    "RI": (-71.5, 41.7, 1098),
    "MA": (-71.8, 42.3, 7029),
    "VT": (-72.6, 44.0, 643),
    "NH": (-71.5, 43.5, 1377),
    "ME": (-69.0, 45.0, 1362),
}

names = list(states.keys())
lons = np.array([states[s][0] for s in names])
lats = np.array([states[s][1] for s in names])
populations = np.array([states[s][2] for s in names])  # in thousands

# GDP per capita (synthetic but realistic ranges)
gdp_per_capita = np.array(
    [
        78000,
        56000,
        81000,
        55000,
        45000,
        42000,
        65000,
        54000,
        70000,
        52000,
        46000,
        63000,
        58000,
        61000,
        55000,
        48000,
        62000,
        65000,
        59000,
        50000,
        41000,
        49000,
        56000,
        68000,
        51000,
        53000,
        57000,
        46000,
        52000,
        38000,
        44000,
        58000,
        51000,
        46000,
        56000,
        63000,
        40000,
        65000,
        82000,
        72000,
        62000,
        73000,
        76000,
        58000,
        82000,
        52000,
        60000,
        46000,
    ]
)

# Scale circle radii proportional to sqrt(population) for area proportionality
max_pop = populations.max()
radii = np.sqrt(populations / max_pop) * 2.8

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

norm = Normalize(vmin=gdp_per_capita.min(), vmax=gdp_per_capita.max())
cmap = plt.cm.YlGnBu

for i, name in enumerate(names):
    circle = plt.Circle(
        (lons[i], lats[i]),
        radii[i],
        facecolor=cmap(norm(gdp_per_capita[i])),
        edgecolor="white",
        linewidth=1.2,
        alpha=0.9,
    )
    ax.add_patch(circle)
    if populations[i] > 5000:
        ax.text(lons[i], lats[i], name, ha="center", va="center", fontsize=11, fontweight="bold", color="#1a1a2e")

# Colorbar
sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=25)
cbar.set_label("GDP per Capita (USD)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Size legend - representative population circles (largest at top)
legend_pops = [30000, 10000, 1000]
legend_labels = ["30M", "10M", "1M"]
legend_radii = [np.sqrt(p / max_pop) * 2.8 for p in legend_pops]

legend_x = -68.5
legend_y_base = 28.0
ax.text(
    legend_x,
    legend_y_base + 12.0,
    "Population",
    fontsize=14,
    fontweight="bold",
    ha="center",
    va="center",
    color="#333333",
)
y_pos = legend_y_base
for r, label in zip(legend_radii, legend_labels, strict=True):
    circle_y = y_pos + r
    legend_circle = plt.Circle((legend_x - 1.5, circle_y), r, facecolor="none", edgecolor="#555555", linewidth=1.5)
    ax.add_patch(legend_circle)
    ax.text(legend_x + 1.8, circle_y, label, fontsize=13, va="center", ha="left", color="#555555")
    y_pos += r * 2 + 1.0

# Style
ax.set_xlim(-128, -64)
ax.set_ylim(25, 50)
ax.set_aspect("equal")
ax.set_title(
    "US States by Population · cartogram-area-distortion · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.set_xticks([])
ax.set_yticks([])

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
