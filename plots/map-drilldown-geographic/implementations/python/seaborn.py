""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle


# Set seaborn theme with subtle grid
sns.set_theme(style="whitegrid", context="talk", font_scale=1.0)
plt.rcParams["grid.alpha"] = 0.25

# Seed for reproducibility
np.random.seed(42)

# Hierarchical geographic data - Country (World) > State (USA) > City (California)
# Level 1: Countries with approximate centroids and bounding boxes
countries_data = {
    "USA": {"lon": -98, "lat": 39, "value": 4500, "bounds": (-125, -67, 24, 49)},
    "Canada": {"lon": -106, "lat": 56, "value": 1200, "bounds": (-141, -52, 42, 70)},
    "Mexico": {"lon": -102, "lat": 23, "value": 900, "bounds": (-118, -87, 14, 33)},
    "Brazil": {"lon": -53, "lat": -10, "value": 1800, "bounds": (-74, -35, -33, 5)},
    "Argentina": {"lon": -64, "lat": -34, "value": 650, "bounds": (-74, -53, -55, -22)},
}

# Level 2: US States with approximate centroids
us_states_data = {
    "California": {"lon": -119, "lat": 36.5, "value": 1200, "bounds": (-124.5, -114, 32.5, 42)},
    "Texas": {"lon": -100, "lat": 31, "value": 950, "bounds": (-107, -93, 25.5, 36.5)},
    "Florida": {"lon": -82, "lat": 28, "value": 680, "bounds": (-88, -80, 24.5, 31)},
    "New York": {"lon": -75, "lat": 43, "value": 720, "bounds": (-80, -72, 40.5, 45)},
    "Illinois": {"lon": -89, "lat": 40, "value": 480, "bounds": (-91.5, -87, 37, 42.5)},
    "Washington": {"lon": -120, "lat": 47, "value": 350, "bounds": (-125, -117, 45.5, 49)},
}

# Level 3: California cities
ca_cities_data = {
    "Los Angeles": {"lon": -118.25, "lat": 34.05, "value": 450},
    "San Francisco": {"lon": -122.42, "lat": 37.77, "value": 280},
    "San Diego": {"lon": -117.16, "lat": 32.72, "value": 180},
    "San Jose": {"lon": -121.89, "lat": 37.34, "value": 150},
    "Sacramento": {"lon": -121.49, "lat": 38.58, "value": 90},
    "Fresno": {"lon": -119.78, "lat": 36.74, "value": 50},
}

# Create figure with 3 panels showing drill-down hierarchy
fig, axes = plt.subplots(1, 3, figsize=(16, 9))

# Color normalization for consistent choropleth across panels
all_values = (
    [c["value"] for c in countries_data.values()]
    + [s["value"] for s in us_states_data.values()]
    + [c["value"] for c in ca_cities_data.values()]
)
vmin, vmax = min(all_values), max(all_values)
cmap = sns.color_palette("Blues", as_cmap=True)

# Panel 1: Country level (Americas)
ax1 = axes[0]
ax1.set_facecolor("#e8f4f8")

# Draw countries as rectangles (simplified regions)
for name, data in countries_data.items():
    b = data["bounds"]
    color_val = (data["value"] - vmin) / (vmax - vmin)
    rect_color = cmap(color_val)

    # Highlight USA as the drillable region
    edge_color = "#306998" if name == "USA" else "#888888"
    line_width = 3 if name == "USA" else 1.5

    rect = Rectangle(
        (b[0], b[2]),
        b[1] - b[0],
        b[3] - b[2],
        facecolor=rect_color,
        edgecolor=edge_color,
        linewidth=line_width,
        alpha=0.9,
    )
    ax1.add_patch(rect)

    # Country label
    ax1.text(data["lon"], data["lat"], name, fontsize=11, ha="center", va="center", fontweight="bold")
    ax1.text(data["lon"], data["lat"] - 4, f"${data['value']:,}M", fontsize=9, ha="center", va="center")

# Create scatter data for seaborn (centroids)
country_df = pd.DataFrame(
    [{"name": k, "lon": v["lon"], "lat": v["lat"], "value": v["value"]} for k, v in countries_data.items()]
)

ax1.set_xlim(-150, -30)
ax1.set_ylim(-60, 75)
ax1.set_title("Level 1: Countries", fontsize=18, fontweight="bold", pad=10)
ax1.set_xlabel("Longitude (°)", fontsize=14)
ax1.set_ylabel("Latitude (°)", fontsize=14)
ax1.tick_params(axis="both", labelsize=11)

# Breadcrumb for panel 1
ax1.text(
    0.05,
    0.95,
    "World",
    transform=ax1.transAxes,
    fontsize=12,
    fontweight="bold",
    color="#306998",
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

# Panel 2: US States level
ax2 = axes[1]
ax2.set_facecolor("#e8f4f8")

# Draw US states as rectangles
for name, data in us_states_data.items():
    b = data["bounds"]
    color_val = (data["value"] - vmin) / (vmax - vmin)
    rect_color = cmap(color_val)

    # Highlight California as the drillable region
    edge_color = "#306998" if name == "California" else "#888888"
    line_width = 3 if name == "California" else 1.5

    rect = Rectangle(
        (b[0], b[2]),
        b[1] - b[0],
        b[3] - b[2],
        facecolor=rect_color,
        edgecolor=edge_color,
        linewidth=line_width,
        alpha=0.9,
    )
    ax2.add_patch(rect)

    # State label
    ax2.text(data["lon"], data["lat"], name, fontsize=10, ha="center", va="center", fontweight="bold")
    ax2.text(data["lon"], data["lat"] - 2, f"${data['value']:,}M", fontsize=9, ha="center", va="center")

ax2.set_xlim(-130, -65)
ax2.set_ylim(22, 52)
ax2.set_title("Level 2: States (USA)", fontsize=18, fontweight="bold", pad=10)
ax2.set_xlabel("Longitude (°)", fontsize=14)
ax2.set_ylabel("", fontsize=14)
ax2.tick_params(axis="both", labelsize=11)

# Breadcrumb for panel 2
ax2.text(
    0.05,
    0.95,
    "World > USA",
    transform=ax2.transAxes,
    fontsize=12,
    fontweight="bold",
    color="#306998",
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

# Panel 3: California cities level
ax3 = axes[2]
ax3.set_facecolor("#e8f4f8")

# Draw California outline
ca_bounds = us_states_data["California"]["bounds"]
ca_outline = Rectangle(
    (ca_bounds[0], ca_bounds[2]),
    ca_bounds[1] - ca_bounds[0],
    ca_bounds[3] - ca_bounds[2],
    facecolor="#d4e8f0",
    edgecolor="#306998",
    linewidth=2,
    alpha=0.5,
)
ax3.add_patch(ca_outline)

# Create DataFrame for seaborn scatterplot
cities_df = pd.DataFrame(
    [{"name": k, "lon": v["lon"], "lat": v["lat"], "value": v["value"]} for k, v in ca_cities_data.items()]
)

# Use seaborn scatterplot for cities with size encoding
sns.scatterplot(
    data=cities_df,
    x="lon",
    y="lat",
    size="value",
    sizes=(200, 800),
    hue="value",
    palette="Blues",
    alpha=0.85,
    ax=ax3,
    legend="brief",
)

# Customize the size legend
handles, labels = ax3.get_legend_handles_labels()
# Filter to keep only size legend entries (numeric values)
size_handles = []
size_labels = []
for h, lbl in zip(handles, labels, strict=False):
    try:
        val = float(lbl)
        size_handles.append(h)
        size_labels.append(f"${int(val)}M")
    except ValueError:
        pass
ax3.legend(size_handles, size_labels, title="Sales", loc="lower right", fontsize=9, title_fontsize=10, framealpha=0.9)

# City labels - offset San Jose and San Francisco to avoid overlap
for _, row in cities_df.iterrows():
    name = row["name"]
    # Adjust positions for nearby cities to avoid text overlap
    if name == "San Francisco":
        # Move label to the left
        ax3.text(row["lon"] - 0.8, row["lat"] + 0.2, name, fontsize=10, ha="right", va="bottom", fontweight="bold")
        ax3.text(row["lon"] - 0.8, row["lat"] - 0.15, f"${row['value']:,}M", fontsize=9, ha="right", va="top")
    elif name == "San Jose":
        # Move label to the right
        ax3.text(row["lon"] + 0.8, row["lat"] - 0.1, name, fontsize=10, ha="left", va="top", fontweight="bold")
        ax3.text(row["lon"] + 0.8, row["lat"] - 0.5, f"${row['value']:,}M", fontsize=9, ha="left", va="top")
    else:
        ax3.text(row["lon"], row["lat"] + 0.4, name, fontsize=10, ha="center", va="bottom", fontweight="bold")
        ax3.text(row["lon"], row["lat"] - 0.35, f"${row['value']:,}M", fontsize=9, ha="center", va="top")

ax3.set_xlim(-125.5, -113)
ax3.set_ylim(31.5, 43)
ax3.set_title("Level 3: Cities (California)", fontsize=18, fontweight="bold", pad=10)
ax3.set_xlabel("Longitude (°)", fontsize=14)
ax3.set_ylabel("", fontsize=14)
ax3.tick_params(axis="both", labelsize=11)

# Breadcrumb for panel 3
ax3.text(
    0.05,
    0.95,
    "World > USA > California",
    transform=ax3.transAxes,
    fontsize=11,
    fontweight="bold",
    color="#306998",
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

# Draw drill-down arrows between panels using annotation
fig.text(
    0.355,
    0.5,
    "→",
    fontsize=36,
    ha="center",
    va="center",
    transform=fig.transFigure,
    color="#306998",
    fontweight="bold",
)
fig.text(
    0.665,
    0.5,
    "→",
    fontsize=36,
    ha="center",
    va="center",
    transform=fig.transFigure,
    color="#306998",
    fontweight="bold",
)

# Main title
fig.suptitle("map-drilldown-geographic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", y=0.99)

# Subtitle explaining the visualization
fig.text(
    0.5,
    0.94,
    "Geographic Hierarchy: Click regions to drill down (Country → State → City)",
    ha="center",
    fontsize=13,
    style="italic",
    color="#555555",
)

# Adjust layout first to make room for colorbar
plt.subplots_adjust(left=0.06, right=0.95, top=0.85, bottom=0.22, wspace=0.18)

# Add colorbar below the plots with more space
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
cbar = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.025, pad=0.08, aspect=40)
cbar.set_label("Sales Revenue ($M)", fontsize=14)
cbar.ax.tick_params(labelsize=12)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
