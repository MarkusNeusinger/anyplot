""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection


# Data: US states arranged in a tile grid map layout (all 50 states)
# Grid positions (col, row) - approximating geographic positions
regions = {
    # Alaska and Hawaii (positioned separately)
    "Alaska": (0, 5),
    "Hawaii": (0, 1),
    # West Coast
    "Washington": (1, 5),
    "Oregon": (1, 4),
    "California": (0, 3),
    "Nevada": (1, 3),
    # Mountain West
    "Idaho": (2, 5),
    "Montana": (3, 5),
    "Wyoming": (3, 4),
    "Utah": (2, 3),
    "Arizona": (2, 2),
    "Colorado": (3, 3),
    "New Mexico": (3, 2),
    # Great Plains
    "North Dakota": (4, 5),
    "South Dakota": (4, 4),
    "Nebraska": (4, 3),
    "Kansas": (4, 2),
    "Oklahoma": (4, 1),
    "Texas": (3, 1),
    # Midwest
    "Minnesota": (5, 5),
    "Iowa": (5, 4),
    "Missouri": (5, 3),
    "Arkansas": (5, 2),
    "Louisiana": (5, 1),
    "Wisconsin": (6, 5),
    "Illinois": (6, 4),
    "Indiana": (7, 4),
    "Michigan": (7, 5),
    "Ohio": (8, 4),
    "Kentucky": (7, 3),
    "Tennessee": (6, 3),
    "Mississippi": (6, 2),
    "Alabama": (7, 2),
    # Southeast
    "Georgia": (8, 2),
    "Florida": (8, 1),
    "South Carolina": (9, 2),
    "North Carolina": (9, 3),
    "Virginia": (9, 4),
    "West Virginia": (8, 3),
    # Northeast
    "Pennsylvania": (10, 4),
    "New York": (10, 5),
    "Vermont": (11, 5),
    "New Hampshire": (11, 4),
    "Maine": (12, 5),
    "Massachusetts": (11, 3),
    "Rhode Island": (12, 3),
    "Connecticut": (11, 2),
    "New Jersey": (10, 3),
    "Delaware": (10, 2),
    "Maryland": (9, 1),
    # District of Columbia (no data - demonstrates missing data handling)
    "District of Columbia": (10, 1),
}

# Population density values (simulated but realistic ranges)
# Note: District of Columbia intentionally omitted to demonstrate missing data handling
density_values = {
    "Alaska": 1,
    "Hawaii": 226,
    "California": 253,
    "Texas": 112,
    "Florida": 411,
    "New York": 408,
    "Pennsylvania": 286,
    "Illinois": 227,
    "Ohio": 289,
    "Georgia": 185,
    "North Carolina": 218,
    "Michigan": 177,
    "New Jersey": 1263,
    "Virginia": 218,
    "Washington": 117,
    "Arizona": 64,
    "Massachusetts": 901,
    "Tennessee": 167,
    "Indiana": 189,
    "Missouri": 89,
    "Maryland": 636,
    "Wisconsin": 108,
    "Colorado": 57,
    "Minnesota": 71,
    "South Carolina": 173,
    "Alabama": 99,
    "Louisiana": 107,
    "Kentucky": 114,
    "Oregon": 44,
    "Oklahoma": 58,
    "Connecticut": 733,
    "Iowa": 57,
    "Mississippi": 63,
    "Arkansas": 58,
    "Utah": 40,
    "Nevada": 28,
    "Kansas": 36,
    "New Mexico": 17,
    "Nebraska": 25,
    "West Virginia": 74,
    "Idaho": 23,
    "Maine": 44,
    "New Hampshire": 154,
    "Rhode Island": 1061,
    "Montana": 8,
    "Delaware": 508,
    "South Dakota": 12,
    "North Dakota": 11,
    "Vermont": 68,
    "Wyoming": 6,
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create patches for each region
patches = []
missing_patches = []
colors = []
cmap = plt.cm.Blues

# Normalize values for coloring
values = list(density_values.values())
vmin, vmax = min(values), max(values)

for state, (col, row) in regions.items():
    # Create rectangle for each state (simplified grid representation)
    rect = mpatches.FancyBboxPatch(
        (col * 1.1, row * 1.1), 1.0, 1.0, boxstyle="round,pad=0.02,rounding_size=0.1", linewidth=2, edgecolor="white"
    )

    # Handle missing data (state not in density_values)
    if state not in density_values:
        missing_patches.append(rect)
    else:
        patches.append(rect)
        # Get color based on density value
        density = density_values[state]
        norm_value = (density - vmin) / (vmax - vmin)
        colors.append(cmap(norm_value))

# Create patch collection for states with data
collection = PatchCollection(patches, facecolors=colors, edgecolors="white", linewidths=2)
ax.add_collection(collection)

# Create patch collection for missing data (gray with hatched pattern)
missing_collection = PatchCollection(
    missing_patches, facecolors="#d0d0d0", edgecolors="white", linewidths=2, hatch="///"
)
ax.add_collection(missing_collection)

# Add state labels
# State abbreviation dictionary (all 50 states + DC)
abbrev = {
    "Alaska": "AK",
    "Hawaii": "HI",
    "Washington": "WA",
    "Oregon": "OR",
    "California": "CA",
    "Nevada": "NV",
    "Idaho": "ID",
    "Montana": "MT",
    "Wyoming": "WY",
    "Utah": "UT",
    "Arizona": "AZ",
    "Colorado": "CO",
    "New Mexico": "NM",
    "North Dakota": "ND",
    "South Dakota": "SD",
    "Nebraska": "NE",
    "Kansas": "KS",
    "Oklahoma": "OK",
    "Texas": "TX",
    "Minnesota": "MN",
    "Iowa": "IA",
    "Missouri": "MO",
    "Arkansas": "AR",
    "Louisiana": "LA",
    "Wisconsin": "WI",
    "Illinois": "IL",
    "Indiana": "IN",
    "Michigan": "MI",
    "Ohio": "OH",
    "Kentucky": "KY",
    "Tennessee": "TN",
    "Mississippi": "MS",
    "Alabama": "AL",
    "Georgia": "GA",
    "Florida": "FL",
    "South Carolina": "SC",
    "North Carolina": "NC",
    "Virginia": "VA",
    "West Virginia": "WV",
    "Pennsylvania": "PA",
    "New York": "NY",
    "Vermont": "VT",
    "New Hampshire": "NH",
    "Maine": "ME",
    "Massachusetts": "MA",
    "Rhode Island": "RI",
    "Connecticut": "CT",
    "New Jersey": "NJ",
    "Delaware": "DE",
    "Maryland": "MD",
    "District of Columbia": "DC",
}

for state, (col, row) in regions.items():
    # Handle text color based on background
    if state not in density_values:
        # Missing data regions have gray background
        text_color = "#333333"
    else:
        density = density_values[state]
        norm_value = (density - vmin) / (vmax - vmin)
        text_color = "white" if norm_value > 0.5 else "#306998"

    ax.text(
        col * 1.1 + 0.5,
        row * 1.1 + 0.5,
        abbrev.get(state, state[:2].upper()),
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=text_color,
    )

# Set axis limits and remove axes
ax.set_xlim(-0.5, 14)
ax.set_ylim(0.3, 6.5)
ax.set_aspect("equal")
ax.axis("off")

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label("Population Density (per sq mile)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Add legend for missing data
missing_patch = mpatches.Patch(facecolor="#d0d0d0", edgecolor="gray", hatch="///", label="No data")
ax.legend(handles=[missing_patch], loc="lower left", fontsize=14, framealpha=0.9)

# Title
ax.set_title(
    "US Population Density · choropleth-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
