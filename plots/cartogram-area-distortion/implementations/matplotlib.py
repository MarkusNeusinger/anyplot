"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-13
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


# Data - US states with approximate geographic centroids, population (thousands), and GDP per capita
np.random.seed(42)

states = {
    "WA": (-122.0, 47.5, 7615, 78000),
    "OR": (-120.5, 44.0, 4218, 56000),
    "CA": (-119.5, 37.0, 39538, 81000),
    "NV": (-116.8, 39.0, 3104, 55000),
    "ID": (-114.5, 44.5, 1839, 45000),
    "MT": (-109.5, 47.0, 1084, 42000),
    "WY": (-107.5, 43.0, 577, 65000),
    "UT": (-111.5, 39.5, 3272, 54000),
    "CO": (-105.5, 39.0, 5773, 70000),
    "AZ": (-111.5, 34.5, 7279, 52000),
    "NM": (-106.0, 34.5, 2117, 46000),
    "ND": (-100.5, 47.5, 779, 63000),
    "SD": (-100.0, 44.5, 887, 58000),
    "NE": (-99.8, 41.5, 1962, 61000),
    "KS": (-98.5, 38.5, 2937, 55000),
    "OK": (-97.5, 35.5, 3959, 48000),
    "TX": (-99.0, 31.5, 29145, 62000),
    "MN": (-94.5, 46.0, 5640, 65000),
    "IA": (-93.5, 42.0, 3190, 59000),
    "MO": (-92.5, 38.5, 6154, 50000),
    "AR": (-92.5, 35.0, 3012, 41000),
    "LA": (-92.0, 31.0, 4657, 49000),
    "WI": (-89.5, 44.5, 5822, 56000),
    "IL": (-89.0, 40.0, 12812, 68000),
    "MI": (-84.5, 44.0, 10077, 51000),
    "IN": (-86.0, 40.0, 6733, 53000),
    "OH": (-82.5, 40.5, 11799, 57000),
    "KY": (-85.5, 37.8, 4506, 46000),
    "TN": (-86.0, 35.8, 6911, 52000),
    "MS": (-89.5, 32.5, 2961, 38000),
    "AL": (-86.8, 32.8, 5024, 44000),
    "GA": (-83.5, 33.0, 10712, 58000),
    "FL": (-81.5, 28.5, 21538, 51000),
    "SC": (-81.0, 34.0, 5119, 46000),
    "NC": (-79.5, 35.5, 10439, 56000),
    "VA": (-79.0, 37.5, 8631, 63000),
    "WV": (-80.5, 38.8, 1794, 40000),
    "PA": (-77.5, 41.0, 13002, 65000),
    "NY": (-74.5, 43.0, 20201, 82000),
    "NJ": (-74.5, 40.0, 9289, 72000),
    "MD": (-76.5, 39.0, 6177, 62000),
    "DE": (-75.5, 39.0, 990, 73000),
    "CT": (-72.7, 41.6, 3606, 76000),
    "RI": (-71.5, 41.7, 1098, 58000),
    "MA": (-71.8, 42.3, 7029, 82000),
    "VT": (-72.6, 44.0, 643, 52000),
    "NH": (-71.5, 43.5, 1377, 60000),
    "ME": (-69.0, 45.0, 1362, 46000),
}

names = list(states.keys())
lons = np.array([states[s][0] for s in names])
lats = np.array([states[s][1] for s in names])
populations = np.array([states[s][2] for s in names])
gdp_per_capita = np.array([states[s][3] for s in names])

# Scale circle radii proportional to sqrt(population) for area proportionality
max_pop = populations.max()
radii = np.sqrt(populations / max_pop) * 2.8

# Collision avoidance: push overlapping circles apart to reduce NE crowding
adjusted_lons = lons.copy()
adjusted_lats = lats.copy()
for _ in range(40):
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            dx = adjusted_lons[j] - adjusted_lons[i]
            dy = adjusted_lats[j] - adjusted_lats[i]
            dist = np.sqrt(dx**2 + dy**2)
            min_dist = (radii[i] + radii[j]) * 1.15
            if dist < min_dist and dist > 0:
                overlap = min_dist - dist
                push = overlap / 2
                nx, ny = dx / dist, dy / dist
                adjusted_lons[i] -= nx * push * 0.3
                adjusted_lats[i] -= ny * push * 0.3
                adjusted_lons[j] += nx * push * 0.3
                adjusted_lats[j] += ny * push * 0.3

# Plot
fig = plt.figure(figsize=(16, 9))
ax = fig.add_axes([0.05, 0.08, 0.70, 0.82])

norm = Normalize(vmin=gdp_per_capita.min(), vmax=gdp_per_capita.max())
cmap = plt.cm.YlGnBu

# Draw circles with sorted order so smaller circles render on top
sort_idx = np.argsort(-populations)
for i in sort_idx:
    circle = plt.Circle(
        (adjusted_lons[i], adjusted_lats[i]),
        radii[i],
        facecolor=cmap(norm(gdp_per_capita[i])),
        edgecolor="white",
        linewidth=1.5,
        alpha=0.92,
        zorder=2 + (max_pop - populations[i]) / max_pop,
    )
    ax.add_patch(circle)
    if populations[i] > 4000:
        ax.text(
            adjusted_lons[i],
            adjusted_lats[i],
            names[i],
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color="#1a1a2e",
            zorder=4,
        )

# Annotations: highlight key data insights
ca_idx = names.index("CA")
ax.annotate(
    "California\n39.5M people",
    xy=(adjusted_lons[ca_idx], adjusted_lats[ca_idx] - radii[ca_idx]),
    xytext=(adjusted_lons[ca_idx] + 4, adjusted_lats[ca_idx] - 6),
    fontsize=14,
    fontweight="bold",
    color="#1a1a2e",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#555555", "lw": 1.5},
    zorder=5,
)

ny_idx = names.index("NY")
ax.annotate(
    "New York  $82K GDP/cap",
    xy=(adjusted_lons[ny_idx], adjusted_lats[ny_idx] + radii[ny_idx]),
    xytext=(adjusted_lons[ny_idx] - 8, adjusted_lats[ny_idx] + 5),
    fontsize=14,
    fontweight="bold",
    color="#1a1a2e",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#555555", "lw": 1.5},
    zorder=5,
)

ms_idx = names.index("MS")
ax.annotate(
    "Mississippi\n$38K GDP/cap\n(lowest)",
    xy=(adjusted_lons[ms_idx], adjusted_lats[ms_idx]),
    xytext=(adjusted_lons[ms_idx] - 8, adjusted_lats[ms_idx] + 3),
    fontsize=12,
    color="#555555",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#888888", "lw": 1.2},
    zorder=5,
)

# Colorbar
sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.78, 0.15, 0.02, 0.55])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("GDP per Capita (USD)", fontsize=20, labelpad=10)
cbar.ax.tick_params(labelsize=16)
cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x / 1000:.0f}K"))
cbar.outline.set_linewidth(0.5)

# Size legend (bottom-right of main axes)
legend_x = -68.0
legend_y_base = 27.5
ax.text(
    legend_x,
    legend_y_base + 12.0,
    "Population",
    fontsize=16,
    fontweight="bold",
    ha="center",
    va="center",
    color="#333333",
)
legend_pops = [30000, 10000, 1000]
legend_labels = ["30M", "10M", "1M"]
legend_radii = [np.sqrt(p / max_pop) * 2.8 for p in legend_pops]

y_pos = legend_y_base
for r, label in zip(legend_radii, legend_labels, strict=True):
    circle_y = y_pos + r
    legend_circle = plt.Circle(
        (legend_x - 1.5, circle_y), r, facecolor="#e8e8e8", edgecolor="#555555", linewidth=1.2, zorder=2
    )
    ax.add_patch(legend_circle)
    ax.text(legend_x + 1.8, circle_y, label, fontsize=16, va="center", ha="left", color="#555555")
    y_pos += r * 2 + 1.0

# Reference inset: simplified US outline for geographic comparison
inset_ax = fig.add_axes([0.05, 0.08, 0.16, 0.25])
us_outline_lon = [
    -124,
    -122,
    -120,
    -117,
    -115,
    -111,
    -109,
    -109,
    -111,
    -114,
    -117,
    -120,
    -124,
    -124,
    -123,
    -122,
    -117,
    -104,
    -104,
    -100,
    -97,
    -95,
    -94,
    -90,
    -89,
    -84,
    -82,
    -81,
    -81,
    -80,
    -75,
    -73,
    -70,
    -67,
    -67,
    -69,
    -71,
    -72,
    -74,
    -76,
    -76,
    -78,
    -80,
    -81,
    -82,
    -85,
    -87,
    -88,
    -90,
    -89,
    -90,
    -94,
    -97,
    -97,
    -100,
    -104,
    -109,
    -111,
    -117,
    -120,
    -122,
    -124,
    -124,
]
us_outline_lat = [
    42,
    42,
    39,
    37,
    33,
    32,
    32,
    37,
    41,
    42,
    42,
    46,
    46,
    48,
    49,
    49,
    49,
    49,
    43,
    43,
    37,
    37,
    33,
    33,
    30,
    30,
    30,
    25,
    27,
    32,
    35,
    41,
    42,
    44,
    47,
    47,
    45,
    43,
    41,
    39,
    38,
    39,
    39,
    35,
    30,
    30,
    30,
    30,
    29,
    29,
    30,
    29,
    26,
    26,
    37,
    41,
    37,
    32,
    33,
    37,
    42,
    42,
    42,
]
inset_ax.fill(us_outline_lon, us_outline_lat, color="#d4e6f1", edgecolor="#7f8c8d", linewidth=1.0, alpha=0.6)
inset_ax.set_xlim(-128, -64)
inset_ax.set_ylim(23, 52)
inset_ax.set_aspect("equal")
inset_ax.set_title("Actual Geography", fontsize=11, fontweight="bold", color="#777777", pad=2)
for spine in inset_ax.spines.values():
    spine.set_edgecolor("#cccccc")
    spine.set_linewidth(0.6)
inset_ax.set_xticks([])
inset_ax.set_yticks([])
inset_ax.patch.set_alpha(0.85)

# Main plot styling
ax.set_xlim(-128, -64)
ax.set_ylim(25, 50)
ax.set_aspect("equal")
ax.set_facecolor("#fafbfc")
fig.patch.set_facecolor("#fafbfc")

# Title
fig.text(
    0.40,
    0.95,
    "US States by Population · cartogram-area-distortion · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    ha="center",
    va="center",
    color="#1a1a2e",
)

# Subtitle
fig.text(
    0.40,
    0.02,
    "Circle area proportional to state population  |  Color encodes GDP per capita",
    fontsize=16,
    ha="center",
    va="center",
    color="#666666",
    style="italic",
)

for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xticks([])
ax.set_yticks([])

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
