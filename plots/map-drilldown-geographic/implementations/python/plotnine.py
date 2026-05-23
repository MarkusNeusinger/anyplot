""" anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 76/100 | Updated: 2026-05-23
"""

import os

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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
PANEL_BG = "#D6EAF8" if THEME == "light" else "#1A2A3A"

# Seed for reproducibility
np.random.seed(42)

# Hierarchical geographic data: USA states with performance metrics
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
        "centroid": (-89.8, 40.8),
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
        "centroid": (-82.2, 40.8),
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
        "centroid": (-85.0, 44.5),
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
        "centroid": (-86.5, 35.4),
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
        "centroid": (-86.2, 39.0),
        "abbrev": "IN",
    },
    "Wisconsin": {
        "coords": [(-92.9, 47.0), (-86.8, 46.0), (-86.8, 42.5), (-90.6, 42.5), (-92.9, 44.0), (-92.9, 47.0)],
        "value": 80,
        "centroid": (-89.5, 44.5),
        "abbrev": "WI",
    },
}

# Identify top-3 and bottom-3 states for focal emphasis
sorted_by_value = sorted(states_data.items(), key=lambda x: x[1]["value"])
bottom_3 = {s[0] for s in sorted_by_value[:3]}  # AZ (64), IN (67), FL (68)
top_3 = {s[0] for s in sorted_by_value[-3:]}  # VA (83), CA (85), NY (91)

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
df_top3 = df_states[df_states["state"].isin(top_3)].copy()
df_bottom3 = df_states[df_states["state"].isin(bottom_3)].copy()

# Nudge centroids for crowded northeastern states to reduce label overlap
centroid_nudge = {
    "New York": (-76.0, 43.3),
    "Tennessee": (-86.3, 35.7),
    "Illinois": (-89.5, 40.2),
    "Wisconsin": (-89.7, 44.8),
    "Michigan": (-85.5, 44.3),
}

label_rows = []
for state_name, state_info in states_data.items():
    centroid = centroid_nudge.get(state_name, state_info["centroid"])
    label_rows.append(
        {
            "state": state_name,
            "lon": centroid[0],
            "lat": centroid[1],
            "value": state_info["value"],
            "abbrev": state_info["abbrev"],
            "label": f"{state_info['abbrev']}\n{state_info['value']}",
        }
    )

df_labels = pd.DataFrame(label_rows)

min_value = df_labels["value"].min()
max_value = df_labels["value"].max()

breadcrumb_text = "World  >  USA  >  States"

# Build choropleth map using anyplot_seq colormap (green → dark azure)
# Highlight outlines: lime for top-3 performers, red for bottom-3
plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="state", fill="value"), data=df_states, color=PAGE_BG, size=1.5, alpha=0.92
    )
    + geom_polygon(aes(x="lon", y="lat", group="state"), data=df_top3, color="#99B314", fill="none", size=2.5)
    + geom_polygon(aes(x="lon", y="lat", group="state"), data=df_bottom3, color="#B71D27", fill="none", size=2.5)
    + geom_text(
        aes(x="lon", y="lat", label="label"),
        data=df_labels,
        size=5,
        color="white",
        fontweight="bold",
        va="center",
        ha="center",
    )
    + scale_fill_gradient(
        low="#009E73",
        high="#003D94",
        name="Performance\nScore",
        limits=(min_value, max_value),
        breaks=[64, 70, 76, 82, 88, 91],
    )
    + scale_x_continuous(
        breaks=[-120, -110, -100, -90, -80], labels=["120°W", "110°W", "100°W", "90°W", "80°W"], limits=(-126, -72)
    )
    + scale_y_continuous(
        breaks=[25, 30, 35, 40, 45, 50], labels=["25°N", "30°N", "35°N", "40°N", "45°N", "50°N"], limits=(22, 51)
    )
    + coord_fixed(ratio=1.3)
    + annotate("text", x=-125, y=50, label=breadcrumb_text, size=9, color=INK, fontweight="bold", ha="left")
    + labs(title="map-drilldown-geographic · python · plotnine · anyplot.ai", x="Longitude", y="Latitude")
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PANEL_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=12, weight="bold", color=INK, ha="center"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
