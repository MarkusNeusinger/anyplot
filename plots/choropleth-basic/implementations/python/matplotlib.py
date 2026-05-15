""" anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 73/100 | Updated: 2026-05-15
"""

import os
import sys


# Prevent matplotlib.py from shadowing the matplotlib package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PatchCollection  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: World regions life expectancy (years)
# Arranged in geographic approximation layout
regions = {
    # North America
    "Canada": (1, 4),
    "United States": (1, 3),
    "Mexico": (1, 2),
    # Central America & Caribbean
    "Guatemala": (1.5, 1.5),
    "Cuba": (2, 1.5),
    # South America
    "Colombia": (2, 2),
    "Brazil": (2.5, 2),
    "Peru": (2, 1),
    "Argentina": (2, 0),
    # Europe
    "Iceland": (3.5, 4.5),
    "United Kingdom": (3.5, 4),
    "France": (4, 4),
    "Germany": (4.5, 4),
    "Spain": (3.8, 3.8),
    "Italy": (4.2, 3.6),
    "Poland": (4.5, 4.2),
    "Russia": (5, 4),
    # Africa
    "Nigeria": (4.5, 2.5),
    "Egypt": (5, 2.8),
    "South Africa": (5, 1),
    "Kenya": (5.5, 2),
    # Middle East
    "Saudi Arabia": (5.5, 2.5),
    "Iran": (6, 2.5),
    "Israel": (5.5, 2.8),
    # South Asia
    "India": (6.5, 2),
    "Pakistan": (6.5, 2.5),
    "Bangladesh": (7, 2),
    # Southeast Asia
    "Thailand": (7, 1.5),
    "Indonesia": (7.5, 1),
    "Vietnam": (7.5, 1.8),
    "Philippines": (8, 1.5),
    # East Asia
    "China": (7.5, 2.5),
    "Japan": (8.5, 3),
    "South Korea": (8, 3),
    # Oceania
    "Australia": (8.5, 0),
    "New Zealand": (8.5, -0.5),
}

# Life expectancy data (years) - realistic global ranges
life_expectancy = {
    "Canada": 82,
    "United States": 78,
    "Mexico": 75,
    "Guatemala": 74,
    "Cuba": 79,
    "Colombia": 76,
    "Brazil": 76,
    "Peru": 74,
    "Argentina": 76,
    "Iceland": 83,
    "United Kingdom": 81,
    "France": 83,
    "Germany": 82,
    "Spain": 84,
    "Italy": 84,
    "Poland": 79,
    "Russia": 72,
    "Nigeria": 54,
    "Egypt": 72,
    "South Africa": 65,
    "Kenya": 67,
    "Saudi Arabia": 76,
    "Iran": 76,
    "Israel": 82,
    "India": 68,
    "Pakistan": 67,
    "Bangladesh": 73,
    "Thailand": 77,
    "Indonesia": 72,
    "Vietnam": 74,
    "Philippines": 72,
    "China": 78,
    "Japan": 84,
    "South Korea": 83,
    "Australia": 83,
    "New Zealand": 82,
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create patches for each region
patches = []
colors = []
cmap = plt.cm.RdYlGn  # Diverging colormap: Red (low) -> Yellow -> Green (high)

# Normalize values for coloring
values = list(life_expectancy.values())
vmin, vmax = min(values), max(values)
norm = plt.Normalize(vmin=vmin, vmax=vmax)

for country, (col, row) in regions.items():
    # Create rectangle for each country (simplified grid representation)
    rect = mpatches.FancyBboxPatch(
        (col * 1.15, row * 1.15),
        1.0,
        1.0,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=1.5,
        edgecolor=INK_SOFT,
    )

    patches.append(rect)
    # Get color based on life expectancy value
    le = life_expectancy[country]
    colors.append(cmap(norm(le)))

# Create patch collection for countries with data
collection = PatchCollection(patches, facecolors=colors, edgecolors=INK_SOFT, linewidths=1.5)
ax.add_collection(collection)

# Add country labels
abbrev = {
    "Canada": "CA",
    "United States": "US",
    "Mexico": "MX",
    "Guatemala": "GT",
    "Cuba": "CU",
    "Colombia": "CO",
    "Brazil": "BR",
    "Peru": "PE",
    "Argentina": "AR",
    "Iceland": "IS",
    "United Kingdom": "UK",
    "France": "FR",
    "Germany": "DE",
    "Spain": "ES",
    "Italy": "IT",
    "Poland": "PL",
    "Russia": "RU",
    "Nigeria": "NG",
    "Egypt": "EG",
    "South Africa": "ZA",
    "Kenya": "KE",
    "Saudi Arabia": "SA",
    "Iran": "IR",
    "Israel": "IL",
    "India": "IN",
    "Pakistan": "PK",
    "Bangladesh": "BD",
    "Thailand": "TH",
    "Indonesia": "ID",
    "Vietnam": "VN",
    "Philippines": "PH",
    "China": "CN",
    "Japan": "JP",
    "South Korea": "KR",
    "Australia": "AU",
    "New Zealand": "NZ",
}

for country, (col, row) in regions.items():
    le = life_expectancy[country]
    norm_value = norm(le)
    # Use white text on dark backgrounds, dark text on light backgrounds
    text_color = INK if norm_value < 0.4 else "white"

    ax.text(
        col * 1.15 + 0.5,
        row * 1.15 + 0.5,
        abbrev.get(country, country[:2].upper()),
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=text_color,
    )

# Set axis limits and remove axes
ax.set_xlim(-0.5, 9.5)
ax.set_ylim(-1.5, 5.5)
ax.set_aspect("equal")
ax.axis("off")

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label("Life Expectancy (years)", fontsize=18, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
plt.setp(cbar.ax.spines.values(), color=INK_SOFT)

# Title
title = "World Life Expectancy · choropleth-basic · matplotlib · anyplot.ai"
ax.text(0.5, 1.08, title, transform=ax.transAxes, fontsize=24, fontweight="medium", color=INK, ha="center")

plt.tight_layout()

# Save to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, f"plot-{THEME}.png")
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
