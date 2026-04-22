""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    scale_size,
    theme,
    theme_void,
)
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()

np.random.seed(42)

# Country data with hierarchical sales (Country > State/Province > City)
# Only countries shown at this level; children lists indicate drill-down availability
countries = [
    {"id": "usa", "name": "United States", "value": 4850000, "lat": 39.8, "lon": -98.5, "has_children": True},
    {"id": "canada", "name": "Canada", "value": 1420000, "lat": 56.1, "lon": -106.3, "has_children": True},
    {"id": "mexico", "name": "Mexico", "value": 980000, "lat": 23.6, "lon": -102.5, "has_children": False},
    {"id": "brazil", "name": "Brazil", "value": 1650000, "lat": -14.2, "lon": -51.9, "has_children": False},
    {"id": "uk", "name": "UK", "value": 2100000, "lat": 55.4, "lon": -3.4, "has_children": False},
    {"id": "germany", "name": "Germany", "value": 2350000, "lat": 51.2, "lon": 10.5, "has_children": False},
    {"id": "france", "name": "France", "value": 1890000, "lat": 46.2, "lon": 2.2, "has_children": False},
    {"id": "australia", "name": "Australia", "value": 1280000, "lat": -25.3, "lon": 133.8, "has_children": False},
]

# Simplified continent outlines for background context
continent_rows = []

# North America outline
na_coords = [
    (-170, 66),
    (-165, 62),
    (-140, 60),
    (-130, 55),
    (-125, 48),
    (-124, 42),
    (-118, 34),
    (-105, 25),
    (-97, 26),
    (-85, 22),
    (-82, 23),
    (-80, 25),
    (-83, 30),
    (-88, 30),
    (-92, 29),
    (-97, 28),
    (-97, 24),
    (-92, 18),
    (-87, 15),
    (-82, 9),
    (-78, 9),
    (-75, 10),
    (-72, 12),
    (-62, 10),
    (-60, 14),
    (-62, 18),
    (-65, 18),
    (-67, 18),
    (-72, 21),
    (-75, 20),
    (-80, 23),
    (-80, 25),
    (-82, 30),
    (-76, 35),
    (-75, 38),
    (-72, 41),
    (-70, 44),
    (-67, 45),
    (-65, 48),
    (-70, 47),
    (-60, 47),
    (-55, 50),
    (-58, 52),
    (-63, 58),
    (-70, 60),
    (-85, 65),
    (-95, 68),
    (-110, 70),
    (-130, 70),
    (-145, 68),
    (-155, 70),
    (-165, 65),
    (-170, 66),
]
for lon, lat in na_coords:
    continent_rows.append({"lon": lon, "lat": lat, "continent": "North America"})

# South America outline
sa_coords = [
    (-80, 10),
    (-75, 10),
    (-70, 12),
    (-62, 10),
    (-60, 5),
    (-52, 4),
    (-50, 0),
    (-48, -2),
    (-44, -3),
    (-38, -5),
    (-35, -8),
    (-35, -15),
    (-38, -18),
    (-40, -22),
    (-43, -23),
    (-47, -25),
    (-48, -28),
    (-52, -33),
    (-58, -38),
    (-65, -42),
    (-68, -48),
    (-72, -52),
    (-68, -55),
    (-64, -55),
    (-58, -52),
    (-65, -45),
    (-70, -38),
    (-72, -30),
    (-70, -20),
    (-75, -15),
    (-81, -5),
    (-80, 0),
    (-78, 2),
    (-77, 8),
    (-80, 10),
]
for lon, lat in sa_coords:
    continent_rows.append({"lon": lon, "lat": lat, "continent": "South America"})

# Europe outline
europe_coords = [
    (-10, 36),
    (-8, 43),
    (0, 43),
    (3, 42),
    (8, 44),
    (13, 45),
    (14, 42),
    (19, 42),
    (25, 37),
    (28, 41),
    (40, 41),
    (50, 45),
    (55, 50),
    (60, 55),
    (50, 60),
    (60, 70),
    (25, 71),
    (15, 68),
    (5, 62),
    (10, 55),
    (8, 52),
    (-5, 50),
    (-10, 44),
    (-10, 36),
]
for lon, lat in europe_coords:
    continent_rows.append({"lon": lon, "lat": lat, "continent": "Europe"})

# Australia outline
aus_coords = [
    (115, -20),
    (120, -18),
    (128, -15),
    (130, -12),
    (135, -12),
    (137, -16),
    (140, -17),
    (142, -11),
    (145, -15),
    (148, -20),
    (153, -25),
    (153, -30),
    (151, -34),
    (147, -38),
    (143, -38),
    (138, -35),
    (130, -32),
    (125, -35),
    (118, -35),
    (114, -32),
    (114, -26),
    (115, -20),
]
for lon, lat in aus_coords:
    continent_rows.append({"lon": lon, "lat": lat, "continent": "Australia"})

continents = pd.DataFrame(continent_rows)

# Label offsets to avoid overlap (spread European labels more widely)
label_offsets = {
    "usa": (0, -9),
    "canada": (18, 3),
    "mexico": (0, -9),
    "brazil": (0, -11),
    "uk": (-20, 5),  # Far left above bubble
    "germany": (18, 10),  # Far right and up
    "france": (-22, -12),  # Far left and below
    "australia": (-38, 0),
}

# Prepare country data with label positions and drill-down indicator
countries_data = []
for c in countries:
    nudge_x, nudge_y = label_offsets.get(c["id"], (0, -8))
    countries_data.append(
        {
            "name": c["name"],
            "lon": c["lon"],
            "lat": c["lat"],
            "value": c["value"],
            "value_millions": c["value"] / 1_000_000,
            "has_children": c["has_children"],
            "drillable": "▼ Drillable" if c["has_children"] else "Leaf node",
            "stroke_color": "#FF6B35" if c["has_children"] else "#1a3d5c",
            "label_lon": c["lon"] + nudge_x,
            "label_lat": c["lat"] + nudge_y,
            "sales_formatted": f"${c['value'] / 1_000_000:.2f}M",
        }
    )

df = pd.DataFrame(countries_data)
df_drillable = df[df["has_children"]]
df_leaf = df[~df["has_children"]]

# Create static bubble map with visual drill-down indicators
# Orange stroke = drillable (has children), dark blue stroke = leaf node
plot = (
    ggplot()
    # Continent outlines for geographic context
    + geom_polygon(
        data=continents,
        mapping=aes(x="lon", y="lat", group="continent"),
        fill="#E8E8E8",
        color="#CCCCCC",
        alpha=0.7,
        size=0.5,
        tooltips="none",
    )
    # Leaf node bubbles (non-drillable) - dark blue stroke
    + geom_point(
        data=df_leaf,
        mapping=aes(x="lon", y="lat", size="value_millions", fill="value_millions"),
        color="#1a3d5c",
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().title("@name").line("Sales|@sales_formatted").line("@drillable"),
    )
    # Drillable bubbles - orange stroke to indicate drill-down capability
    + geom_point(
        data=df_drillable,
        mapping=aes(x="lon", y="lat", size="value_millions", fill="value_millions"),
        color="#FF6B35",
        alpha=0.85,
        shape=21,
        stroke=2.5,
        tooltips=layer_tooltips().title("@name").line("Sales|@sales_formatted").line("@drillable"),
    )
    # Country labels at adjusted positions
    + geom_text(
        data=df,
        mapping=aes(x="label_lon", y="label_lat", label="name"),
        size=10,
        color="#333333",
        fontface="bold",
        tooltips="none",
    )
    # Scales - hide size legend, only show color gradient
    + scale_size(range=[10, 28], guide="none")
    + scale_fill_gradient(low="#FFD43B", high="#306998", name="Sales (Millions $)")
    # Coordinate and labels - extend xlim to prevent Australia cutoff
    + coord_fixed(ratio=1.3, xlim=[-180, 200], ylim=[-60, 75])
    + labs(
        title="map-drilldown-geographic · letsplot · pyplots.ai",
        subtitle="Global Sales by Country · Orange border = drill-down available",
    )
    + ggsize(1600, 900)
    + theme_void()
    + theme(
        plot_title=element_text(size=28, face="bold", hjust=0.5),
        plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position=[0.88, 0.18],
        plot_background=element_rect(fill="#f0f4f8"),
    )
)

# Save static PNG (scale 3x for 4800 × 2700 px)
export_ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML using lets-plot native export
export_ggsave(plot, "plot.html", path=".", iframe=False)
