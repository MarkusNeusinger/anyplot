""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Seed for reproducibility
np.random.seed(42)

# Hierarchical geographic data: USA states with performance metrics
# This represents a static view of what would be a drillable map
# Note: plotnine is a static library - interactive drill-down requires
# libraries like plotly, bokeh, or altair

# Simplified US state boundaries (approximate polygons) - 20 states for better coverage
states_data = {
    "California": {
        "coords": [
            (-124.4, 42.0),
            (-124.2, 40.0),
            (-122.4, 37.8),
            (-120.0, 34.5),
            (-117.1, 32.5),
            (-114.6, 32.7),
            (-114.6, 34.9),
            (-120.0, 39.0),
            (-121.5, 41.2),
            (-124.4, 42.0),
        ],
        "value": 85,
        "centroid": (-119.4, 37.2),
        "abbrev": "CA",
    },
    "Texas": {
        "coords": [
            (-106.6, 32.0),
            (-103.0, 32.0),
            (-103.0, 36.5),
            (-100.0, 36.5),
            (-100.0, 34.5),
            (-94.4, 33.6),
            (-93.5, 31.0),
            (-94.0, 29.5),
            (-97.1, 26.0),
            (-99.0, 26.0),
            (-101.4, 29.8),
            (-104.0, 29.5),
            (-106.5, 31.8),
            (-106.6, 32.0),
        ],
        "value": 72,
        "centroid": (-99.5, 31.2),
        "abbrev": "TX",
    },
    "New York": {
        "coords": [
            (-79.8, 43.0),
            (-75.0, 45.0),
            (-73.3, 45.0),
            (-73.3, 41.2),
            (-74.7, 41.4),
            (-75.4, 39.9),
            (-79.8, 42.3),
            (-79.8, 43.0),
        ],
        "value": 91,
        "centroid": (-76.0, 42.8),
        "abbrev": "NY",
    },
    "Florida": {
        "coords": [
            (-87.6, 31.0),
            (-85.0, 31.0),
            (-82.0, 30.4),
            (-81.5, 29.0),
            (-80.4, 25.8),
            (-80.0, 24.5),
            (-82.8, 24.5),
            (-83.0, 27.0),
            (-84.9, 29.7),
            (-87.6, 30.4),
            (-87.6, 31.0),
        ],
        "value": 68,
        "centroid": (-82.5, 28.5),
        "abbrev": "FL",
    },
    "Illinois": {
        "coords": [
            (-91.5, 42.5),
            (-87.5, 42.5),
            (-87.5, 39.5),
            (-88.0, 37.5),
            (-89.5, 36.5),
            (-91.5, 36.9),
            (-91.0, 40.0),
            (-91.5, 42.5),
        ],
        "value": 78,
        "centroid": (-89.8, 40.8),  # Shifted slightly NW to reduce overlap with IN
        "abbrev": "IL",
    },
    "Washington": {
        "coords": [(-124.7, 48.4), (-117.0, 49.0), (-117.0, 46.0), (-119.0, 45.9), (-124.0, 46.3), (-124.7, 48.4)],
        "value": 82,
        "centroid": (-120.5, 47.4),
        "abbrev": "WA",
    },
    "Colorado": {
        "coords": [(-109.0, 41.0), (-102.0, 41.0), (-102.0, 37.0), (-109.0, 37.0), (-109.0, 41.0)],
        "value": 75,
        "centroid": (-105.5, 39.0),
        "abbrev": "CO",
    },
    "Arizona": {
        "coords": [(-114.8, 37.0), (-109.0, 37.0), (-109.0, 31.3), (-111.1, 31.3), (-114.8, 32.5), (-114.8, 37.0)],
        "value": 64,
        "centroid": (-111.9, 34.2),
        "abbrev": "AZ",
    },
    "Georgia": {
        "coords": [
            (-85.6, 35.0),
            (-83.1, 35.0),
            (-83.4, 34.5),
            (-82.2, 33.5),
            (-81.0, 32.1),
            (-80.9, 30.4),
            (-82.0, 30.4),
            (-84.9, 30.7),
            (-85.0, 32.0),
            (-85.6, 35.0),
        ],
        "value": 71,
        "centroid": (-83.5, 32.7),
        "abbrev": "GA",
    },
    "Ohio": {
        "coords": [(-84.8, 41.7), (-80.5, 42.0), (-80.5, 39.5), (-81.7, 38.9), (-84.8, 39.1), (-84.8, 41.7)],
        "value": 69,
        "centroid": (-82.2, 40.8),  # Shifted slightly NE to reduce overlap with IN
        "abbrev": "OH",
    },
    "Pennsylvania": {
        "coords": [(-80.5, 42.0), (-75.0, 42.0), (-75.0, 39.7), (-80.5, 39.7), (-80.5, 42.0)],
        "value": 76,
        "centroid": (-77.8, 40.9),
        "abbrev": "PA",
    },
    "Michigan": {
        "coords": [
            (-90.4, 46.0),
            (-84.0, 46.5),
            (-82.5, 45.0),
            (-82.5, 43.5),
            (-84.5, 41.7),
            (-87.0, 41.7),
            (-87.5, 43.0),
            (-88.0, 45.0),
            (-90.4, 46.0),
        ],
        "value": 73,
        "centroid": (-85.0, 44.5),  # Shifted N slightly to reduce crowding
        "abbrev": "MI",
    },
    "Nevada": {
        "coords": [(-120.0, 42.0), (-114.0, 42.0), (-114.0, 36.0), (-117.0, 36.0), (-120.0, 39.0), (-120.0, 42.0)],
        "value": 79,
        "centroid": (-117.0, 39.5),
        "abbrev": "NV",
    },
    "Oregon": {
        "coords": [(-124.5, 46.0), (-117.0, 46.0), (-117.0, 42.0), (-124.5, 42.0), (-124.5, 46.0)],
        "value": 81,
        "centroid": (-120.5, 44.0),
        "abbrev": "OR",
    },
    "North Carolina": {
        "coords": [(-84.3, 36.6), (-75.5, 36.5), (-75.5, 34.0), (-78.5, 33.8), (-84.0, 35.0), (-84.3, 36.6)],
        "value": 77,
        "centroid": (-79.5, 35.5),
        "abbrev": "NC",
    },
    "Virginia": {
        "coords": [(-83.7, 36.6), (-75.2, 37.2), (-75.5, 38.0), (-77.0, 39.0), (-79.5, 39.5), (-83.7, 36.6)],
        "value": 83,
        "centroid": (-78.5, 37.5),
        "abbrev": "VA",
    },
    "Tennessee": {
        "coords": [(-90.3, 35.0), (-81.7, 36.6), (-81.7, 35.0), (-88.0, 35.0), (-90.3, 35.0)],
        "value": 70,
        "centroid": (-86.5, 35.4),  # Shifted S slightly to avoid NC overlap
        "abbrev": "TN",
    },
    "Missouri": {
        "coords": [(-95.8, 40.6), (-89.1, 40.6), (-89.1, 36.5), (-94.6, 36.5), (-95.8, 37.0), (-95.8, 40.6)],
        "value": 74,
        "centroid": (-92.5, 38.5),
        "abbrev": "MO",
    },
    "Indiana": {
        "coords": [(-88.1, 41.8), (-84.8, 41.8), (-84.8, 38.0), (-88.1, 37.8), (-88.1, 41.8)],
        "value": 67,
        "centroid": (-86.2, 39.0),  # Shifted S to reduce overlap with IL and MI
        "abbrev": "IN",
    },
    "Wisconsin": {
        "coords": [(-92.9, 47.0), (-86.8, 46.0), (-86.8, 42.5), (-90.6, 42.5), (-92.9, 44.0), (-92.9, 47.0)],
        "value": 80,
        "centroid": (-89.5, 44.5),
        "abbrev": "WI",
    },
}

# Build dataframe for state polygons
polygon_rows = []
for state_name, state_info in states_data.items():
    for idx, (lon, lat) in enumerate(state_info["coords"]):
        polygon_rows.append(
            {
                "state": state_name,
                "lon": lon,
                "lat": lat,
                "order": idx,
                "value": state_info["value"],
                "abbrev": state_info["abbrev"],
            }
        )

df_states = pd.DataFrame(polygon_rows)

# State labels (centroids) for annotations
label_rows = []
for state_name, state_info in states_data.items():
    label_rows.append(
        {
            "state": state_name,
            "lon": state_info["centroid"][0],
            "lat": state_info["centroid"][1],
            "value": state_info["value"],
            "abbrev": state_info["abbrev"],
            "label": f"{state_info['abbrev']}\n{state_info['value']}",
        }
    )

df_labels = pd.DataFrame(label_rows)

# Calculate actual data range for accurate legend
min_value = df_labels["value"].min()
max_value = df_labels["value"].max()

# Create breadcrumb navigation indicator (static representation)
breadcrumb_text = "World  >  USA  >  States"

# Build choropleth-style state map with improved layout
plot = (
    ggplot()
    # State polygons with value-based fill (choropleth)
    + geom_polygon(
        aes(x="lon", y="lat", group="state", fill="value"), data=df_states, color="#FFFFFF", size=1.5, alpha=0.92
    )
    # State labels with abbreviation and value - larger font
    + geom_text(
        aes(x="lon", y="lat", label="label"),
        data=df_labels,
        size=10,
        color="#1a1a1a",
        fontweight="bold",
        va="center",
        ha="center",
    )
    # Color scale - limits match actual data range (64-91) for legend accuracy
    # Using explicit breaks to ensure full range is displayed
    + scale_fill_gradient(
        low="#FEE08B",  # Light yellow
        high="#1A5276",  # Deep blue
        name="Performance\nScore",
        limits=(min_value, max_value),
        breaks=[64, 70, 76, 82, 88, 91],  # Explicit breaks covering full range
    )
    # Longitude axis - tighter limits to reduce empty space on left
    + scale_x_continuous(
        breaks=[-120, -110, -100, -90, -80], labels=["120°W", "110°W", "100°W", "90°W", "80°W"], limits=(-126, -72)
    )
    # Latitude axis with degree labels for geographic context
    + scale_y_continuous(
        breaks=[25, 30, 35, 40, 45, 50], labels=["25°N", "30°N", "35°N", "40°N", "45°N", "50°N"], limits=(22, 51)
    )
    # Fixed aspect ratio for geographic accuracy
    + coord_fixed(ratio=1.3)
    # Breadcrumb as annotation - positioned within tighter bounds
    + annotate("text", x=-125, y=50, label=breadcrumb_text, size=14, color="#1A5276", fontweight="bold", ha="left")
    # Click instruction annotation
    + annotate(
        "text",
        x=-125,
        y=48.8,
        label="Click any state to drill down (interactive version)",
        size=9,
        color="#555555",
        ha="left",
        fontstyle="italic",
    )
    # Title and labels with geographic axis context
    + labs(
        title="map-drilldown-geographic · plotnine · pyplots.ai",
        subtitle="US Regional Performance Scores (Static View - Drill-down requires interactive library)",
        x="Longitude",
        y="Latitude",
    )
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=28, weight="bold", ha="center"),
        plot_subtitle=element_text(size=16, ha="center", color="#555555"),
        axis_title=element_text(size=18, color="#444444"),
        axis_text=element_text(size=14, color="#666666"),
        axis_ticks=element_line(color="#CCCCCC", size=0.5),
        panel_grid_major=element_line(color="#D0D0D0", size=0.2, alpha=0.25),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#EDF4F7"),
        plot_background=element_rect(fill="white"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",  # Standard right position
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
