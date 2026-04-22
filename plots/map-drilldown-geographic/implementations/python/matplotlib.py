""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection


# Data: Three-level hierarchy showing drill-down from World → USA → California
# Level 1: World regions with sales data (in billions USD)
world_regions = {"North America": 245, "South America": 68, "Europe": 189, "Africa": 42, "Asia": 312, "Oceania": 34}

# Level 2: US states with sales data (in millions USD) - drill into North America
us_states = {
    "California": 42500,
    "Texas": 31200,
    "New York": 28900,
    "Florida": 19800,
    "Illinois": 16500,
    "Pennsylvania": 14200,
    "Ohio": 12800,
    "Georgia": 11500,
    "Michigan": 10200,
    "Washington": 9800,
}

# Level 3: California cities with sales data (in millions USD) - drill into California
ca_cities = {
    "Los Angeles": 12800,
    "San Francisco": 8600,
    "San Diego": 5200,
    "San Jose": 4800,
    "Sacramento": 2400,
    "Oakland": 2100,
    "Fresno": 1800,
    "Long Beach": 1600,
    "Irvine": 1400,
    "Santa Monica": 1200,
}

# Create figure with 3 panels
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor("white")

# Create gridspec for better layout control - improved vertical alignment
gs = fig.add_gridspec(1, 3, left=0.04, right=0.88, top=0.82, bottom=0.15, wspace=0.12)
axes = [fig.add_subplot(gs[0, i]) for i in range(3)]

# Color setup
cmap = plt.cm.Blues

# ========== Panel 1: World Regions ==========
world_positions = {
    "North America": (1, 2),
    "South America": (1, 0),
    "Europe": (2, 2),
    "Africa": (2, 1),
    "Asia": (3, 2),
    "Oceania": (3, 0),
}
world_labels = {
    "North America": "N.AM",
    "South America": "S.AM",
    "Europe": "EUR",
    "Africa": "AFR",
    "Asia": "ASIA",
    "Oceania": "OCE",
}

values1 = list(world_regions.values())
vmin1, vmax1 = min(values1), max(values1)
patches1 = []
colors1 = []

for name in world_positions:
    col, row = world_positions[name]
    rect = mpatches.FancyBboxPatch(
        (col * 1.2, row * 1.2), 1.0, 1.0, boxstyle="round,pad=0.02,rounding_size=0.1", linewidth=2, edgecolor="white"
    )
    patches1.append(rect)
    value = world_regions[name]
    norm_value = (value - vmin1) / (vmax1 - vmin1)
    colors1.append(cmap(0.2 + norm_value * 0.7))

collection1 = PatchCollection(patches1, facecolors=colors1, edgecolors="white", linewidths=2)
axes[0].add_collection(collection1)

for name in world_positions:
    col, row = world_positions[name]
    value = world_regions[name]
    norm_value = (value - vmin1) / (vmax1 - vmin1)
    text_color = "white" if norm_value > 0.4 else "#306998"
    axes[0].text(
        col * 1.2 + 0.5,
        row * 1.2 + 0.5,
        world_labels[name],
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=text_color,
    )

# Highlight North America (drill-down target)
hcol, hrow = world_positions["North America"]
highlight1 = mpatches.FancyBboxPatch(
    (hcol * 1.2 - 0.05, hrow * 1.2 - 0.05),
    1.1,
    1.1,
    boxstyle="round,pad=0.02,rounding_size=0.12",
    linewidth=4,
    edgecolor="#FFD43B",
    facecolor="none",
    zorder=10,
)
axes[0].add_patch(highlight1)

axes[0].set_xlim(0.5, 5.5)
axes[0].set_ylim(-0.5, 4.0)
axes[0].set_aspect("equal")
axes[0].axis("off")
axes[0].set_title("Level 1: Regions", fontsize=16, fontweight="bold", color="#306998", pad=12)
axes[0].text(
    0.5, -0.10, "World", transform=axes[0].transAxes, ha="center", fontsize=12, color="#555555", style="italic"
)

# ========== Panel 2: US States ==========
state_positions = {
    "California": (0, 2),
    "Washington": (0, 3),
    "Texas": (1, 1),
    "Florida": (2, 0),
    "Illinois": (1, 2),
    "New York": (2, 3),
    "Pennsylvania": (2, 2),
    "Ohio": (1, 3),
    "Georgia": (2, 1),
    "Michigan": (0, 4),
}
state_labels = {
    "California": "CA",
    "Washington": "WA",
    "Texas": "TX",
    "Florida": "FL",
    "Illinois": "IL",
    "New York": "NY",
    "Pennsylvania": "PA",
    "Ohio": "OH",
    "Georgia": "GA",
    "Michigan": "MI",
}

values2 = list(us_states.values())
vmin2, vmax2 = min(values2), max(values2)
patches2 = []
colors2 = []

for name in state_positions:
    col, row = state_positions[name]
    rect = mpatches.FancyBboxPatch(
        (col * 1.2, row * 1.2), 1.0, 1.0, boxstyle="round,pad=0.02,rounding_size=0.1", linewidth=2, edgecolor="white"
    )
    patches2.append(rect)
    value = us_states[name]
    norm_value = (value - vmin2) / (vmax2 - vmin2)
    colors2.append(cmap(0.2 + norm_value * 0.7))

collection2 = PatchCollection(patches2, facecolors=colors2, edgecolors="white", linewidths=2)
axes[1].add_collection(collection2)

for name in state_positions:
    col, row = state_positions[name]
    value = us_states[name]
    norm_value = (value - vmin2) / (vmax2 - vmin2)
    text_color = "white" if norm_value > 0.4 else "#306998"
    axes[1].text(
        col * 1.2 + 0.5,
        row * 1.2 + 0.5,
        state_labels[name],
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=text_color,
    )

# Highlight California (drill-down target)
hcol2, hrow2 = state_positions["California"]
highlight2 = mpatches.FancyBboxPatch(
    (hcol2 * 1.2 - 0.05, hrow2 * 1.2 - 0.05),
    1.1,
    1.1,
    boxstyle="round,pad=0.02,rounding_size=0.12",
    linewidth=4,
    edgecolor="#FFD43B",
    facecolor="none",
    zorder=10,
)
axes[1].add_patch(highlight2)

axes[1].set_xlim(-0.5, 4.0)
axes[1].set_ylim(-0.8, 6.2)
axes[1].set_aspect("equal")
axes[1].axis("off")
axes[1].set_title("Level 2: States", fontsize=16, fontweight="bold", color="#306998", pad=12)
axes[1].text(
    0.5,
    -0.10,
    "World > United States",
    transform=axes[1].transAxes,
    ha="center",
    fontsize=12,
    color="#555555",
    style="italic",
)

# ========== Panel 3: California Cities ==========
city_positions = {
    "Los Angeles": (1, 1),
    "San Francisco": (0, 3),
    "San Diego": (1, 0),
    "San Jose": (0, 2),
    "Sacramento": (1, 3),
    "Oakland": (0, 4),
    "Fresno": (1, 2),
    "Long Beach": (2, 1),
    "Irvine": (2, 0),
    "Santa Monica": (0, 1),
}
city_labels = {
    "Los Angeles": "LA",
    "San Francisco": "SF",
    "San Diego": "SD",
    "San Jose": "SJ",
    "Sacramento": "SAC",
    "Oakland": "OAK",
    "Fresno": "FRE",
    "Long Beach": "LB",
    "Irvine": "IRV",
    "Santa Monica": "SM",
}

values3 = list(ca_cities.values())
vmin3, vmax3 = min(values3), max(values3)
patches3 = []
colors3 = []

for name in city_positions:
    col, row = city_positions[name]
    rect = mpatches.FancyBboxPatch(
        (col * 1.2, row * 1.2), 1.0, 1.0, boxstyle="round,pad=0.02,rounding_size=0.1", linewidth=2, edgecolor="white"
    )
    patches3.append(rect)
    value = ca_cities[name]
    norm_value = (value - vmin3) / (vmax3 - vmin3)
    colors3.append(cmap(0.2 + norm_value * 0.7))

collection3 = PatchCollection(patches3, facecolors=colors3, edgecolors="white", linewidths=2)
axes[2].add_collection(collection3)

for name in city_positions:
    col, row = city_positions[name]
    value = ca_cities[name]
    norm_value = (value - vmin3) / (vmax3 - vmin3)
    text_color = "white" if norm_value > 0.4 else "#306998"
    axes[2].text(
        col * 1.2 + 0.5,
        row * 1.2 + 0.5,
        city_labels[name],
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=text_color,
    )

axes[2].set_xlim(-0.5, 4.0)
axes[2].set_ylim(-0.8, 6.2)
axes[2].set_aspect("equal")
axes[2].axis("off")
axes[2].set_title("Level 3: Cities", fontsize=16, fontweight="bold", color="#306998", pad=12)
axes[2].text(
    0.5,
    -0.10,
    "World > United States > California",
    transform=axes[2].transAxes,
    ha="center",
    fontsize=12,
    color="#555555",
    style="italic",
)

# ========== Colorbar ==========
cbar_ax = fig.add_axes([0.91, 0.22, 0.018, 0.45])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Sales Value (relative)", fontsize=14)
cbar.ax.tick_params(labelsize=12)
cbar.set_ticks([0, 0.5, 1])
cbar.set_ticklabels(["Low", "Medium", "High"])

# ========== Drill-down arrows between panels ==========
arrow_style = {"arrowstyle": "-|>", "color": "#FFD43B", "lw": 4, "mutation_scale": 25}
for i in range(2):
    x_start = axes[i].get_position().x1 + 0.01
    x_end = axes[i + 1].get_position().x0 - 0.01
    y_mid = 0.48
    fig.patches.append(
        mpatches.FancyArrowPatch((x_start, y_mid), (x_end, y_mid), transform=fig.transFigure, **arrow_style, zorder=100)
    )

# ========== Title ==========
fig.suptitle("map-drilldown-geographic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", y=0.94)
fig.text(
    0.46,
    0.88,
    "Hierarchical drill-down: Click regions to explore finer geographic detail",
    ha="center",
    fontsize=14,
    color="#666666",
    style="italic",
)

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
