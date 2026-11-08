""" anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-08
"""

import json
import os
import urllib.request

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    ggtb,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_fill_manual,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)
from scipy.cluster.hierarchy import fcluster, linkage


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order for categorical data
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CLUSTER_DIAMETER = 3.0  # degrees: stores closer together than this share one marker at this zoom level
MARKER_MIN, MARKER_MAX = 8, 24  # cluster marker diameter (lets-plot size) for the smallest and largest count
SINGLE_SIZE = 3.5  # marker size of a store without close neighbors
LABEL_MAX = 7  # count label size cap; smaller markers get a smaller label that fits inside them

# Data: store locations with type, synthetic chain of ~1,100 stores; replace with your own table,
# for example df = pd.read_csv("stores.csv") with lat, lon, label and category columns
rng = np.random.default_rng(42)
types = ["Retail", "Warehouse", "Service Center"]
metros = [
    # metro, lon, lat, stores, share of Retail / Warehouse / Service Center
    ("Seattle", -122.3, 47.6, 60, (0.6, 0.2, 0.2)),
    ("San Francisco", -122.2, 37.7, 110, (0.7, 0.1, 0.2)),
    ("Los Angeles", -118.2, 34.0, 175, (0.7, 0.2, 0.1)),
    ("Phoenix", -112.1, 33.4, 55, (0.3, 0.5, 0.2)),
    ("Denver", -105.0, 39.7, 45, (0.3, 0.2, 0.5)),
    ("Dallas", -96.8, 32.8, 120, (0.3, 0.6, 0.1)),
    ("Kansas City", -94.6, 39.1, 40, (0.2, 0.6, 0.2)),
    ("Minneapolis", -93.3, 45.0, 50, (0.5, 0.2, 0.3)),
    ("Chicago", -87.7, 41.9, 160, (0.6, 0.2, 0.2)),
    ("Atlanta", -84.4, 33.7, 85, (0.4, 0.2, 0.4)),
    ("Miami", -80.3, 25.9, 90, (0.7, 0.1, 0.2)),
    ("New York", -74.0, 40.7, 200, (0.7, 0.1, 0.2)),
]
towns = [
    ("Spokane", -117.4, 47.7),
    ("Boise", -116.2, 43.6),
    ("Reno", -119.8, 39.5),
    ("Salt Lake City", -111.9, 40.8),
    ("Billings", -108.5, 45.8),
    ("Albuquerque", -106.6, 35.1),
    ("El Paso", -106.4, 31.8),
    ("Cheyenne", -104.8, 41.1),
    ("Rapid City", -103.2, 44.1),
    ("Amarillo", -101.8, 35.2),
    ("Bismarck", -100.8, 46.8),
    ("San Antonio", -98.5, 29.4),
    ("Wichita", -97.3, 37.7),
    ("Fargo", -96.8, 46.9),
    ("Omaha", -96.0, 41.3),
    ("Tulsa", -96.0, 36.2),
    ("Des Moines", -93.6, 41.6),
    ("Little Rock", -92.3, 34.7),
    ("Jackson", -90.2, 32.3),
    ("New Orleans", -90.1, 30.0),
    ("Memphis", -90.0, 35.1),
    ("Milwaukee", -87.9, 43.0),
    ("Birmingham", -86.8, 33.5),
    ("Nashville", -86.8, 36.2),
    ("Louisville", -85.8, 38.3),
    ("Detroit", -83.0, 42.3),
    ("Columbus", -83.0, 40.0),
    ("Knoxville", -83.9, 36.0),
    ("Jacksonville", -81.7, 30.3),
    ("Charlotte", -80.8, 35.2),
    ("Pittsburgh", -80.0, 40.4),
    ("Raleigh", -78.6, 35.8),
    ("Richmond", -77.4, 37.5),
    ("Buffalo", -78.9, 42.9),
    ("Burlington", -73.2, 44.5),
    ("Bangor", -68.8, 44.8),
]
stores = []
for metro, lon, lat, n, shares in metros:
    for k in range(n):
        stores.append(
            {
                "label": f"{metro} #{k + 1}",
                "lon": lon + rng.normal(0, 0.45),
                "lat": lat + rng.normal(0, 0.35),
                "category": rng.choice(types, p=shares),
            }
        )
for town, lon, lat in towns:
    # Most towns have one store, some two or three a few kilometres apart
    for k in range(rng.choice([1, 1, 1, 2, 3])):
        stores.append(
            {
                "label": f"{town} #{k + 1}",
                "lon": lon + rng.normal(0, 0.08),
                "lat": lat + rng.normal(0, 0.06),
                "category": rng.choice(types, p=(0.5, 0.25, 0.25)),
            }
        )
df = pd.DataFrame(stores)

# Plot: cluster the stores, one marker per group of stores within CLUSTER_DIAMETER of each other
# (complete linkage bounds every cluster's spread); longitude is scaled to ground distance at
# the map's mean latitude
coords = np.column_stack([df["lon"] * np.cos(np.radians(df["lat"].mean())), df["lat"]])
df["cluster"] = fcluster(linkage(coords, method="complete"), t=CLUSTER_DIAMETER, criterion="distance")
clusters = (
    df.groupby("cluster")
    .agg(
        lon=("lon", "mean"),
        lat=("lat", "mean"),
        count=("label", "size"),
        dominant=("category", lambda s: s.value_counts().idxmax()),
        mix=("category", lambda s: " · ".join(f"{k} {v}" for k, v in s.value_counts().items())),
    )
    .reset_index()
)
groups = clusters[clusters["count"] > 1].copy()
singles = df[df["cluster"].isin(clusters.loc[clusters["count"] == 1, "cluster"])]

# Cluster marker diameter grows with the square root of the count, so the largest groups stand
# out; the count label shrinks with its marker so every number fits inside its circle
groups["marker"] = MARKER_MIN + (MARKER_MAX - MARKER_MIN) * np.sqrt(groups["count"] / groups["count"].max())
groups["text"] = groups["count"].astype(str)
groups["text_size"] = np.minimum(LABEL_MAX, 0.85 * groups["marker"] / groups["text"].str.len())

# Category colors by position, the most frequent type first; the count label on each marker
# takes the darker or lighter ink, whichever contrasts more with its fill (WCAG luminance)
categories = df["category"].value_counts().index.tolist()
colors = {category: IMPRINT_PALETTE[i] for i, category in enumerate(categories)}
DARK_TEXT, LIGHT_TEXT = "#1A1A17", "#FAF8F1"
hexes = [colors[c] for c in categories] + [DARK_TEXT, LIGHT_TEXT]
rgb = np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in hexes]) / 255
luminance = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
fill_lum, dark_lum, light_lum = luminance[:-2], luminance[-2], luminance[-1]
use_dark = (fill_lum + 0.05) / (dark_lum + 0.05) >= (light_lum + 0.05) / (fill_lum + 0.05)
label_colors = dict(zip(categories, np.where(use_dark, DARK_TEXT, LIGHT_TEXT), strict=True))
groups["text_color"] = groups["dominant"].map(label_colors)

# Basemap: US-48 state boundaries from Natural Earth (1:50m, Great Lakes cut out), one polygon
# group per outer ring so islands and multi-part states draw separately
STATES_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    "ne_50m_admin_1_states_provinces_lakes.geojson"
)
with urllib.request.urlopen(STATES_URL, timeout=60) as response:
    states = json.load(response)["features"]
rings = [
    ring_polygon[0]
    for state in states
    if state["properties"]["adm0_a3"] == "USA" and state["properties"]["postal"] not in ("AK", "HI")
    for ring_polygon in (
        state["geometry"]["coordinates"]
        if state["geometry"]["type"] == "MultiPolygon"
        else [state["geometry"]["coordinates"]]
    )
]
df_us = pd.concat(
    [pd.DataFrame(ring, columns=["x", "y"]).assign(group=i) for i, ring in enumerate(rings)], ignore_index=True
)

map_fill = "#E0DDD6" if THEME == "light" else "#2A2A27"
map_border = "#B0ADA6" if THEME == "light" else "#4A4A44"

caption = (
    f"{len(df):,} store locations · {len(groups)} clusters of nearby stores (count on the marker, "
    f"color = most common type) · {len(singles)} single stores"
)

plot = (
    ggplot()
    + geom_polygon(data=df_us, mapping=aes(x="x", y="y", group="group"), fill=map_fill, color=map_border, size=0.3)
    # Stores without close neighbors keep their own location
    + geom_point(
        data=singles,
        mapping=aes(x="lon", y="lat", fill="category"),
        size=SINGLE_SIZE,
        shape=21,
        color=PAGE_BG,
        stroke=0.6,
        tooltips=layer_tooltips().title("@label").line("Type|@category"),
    )
    # Cluster markers at the mean position of their stores
    + geom_point(
        data=groups,
        mapping=aes(x="lon", y="lat", size="marker", fill="dominant"),
        shape=21,
        color=PAGE_BG,
        stroke=1.0,
        tooltips=layer_tooltips().title("@count stores").line("@mix"),
    )
    + geom_text(
        data=groups,
        mapping=aes(x="lon", y="lat", label="text", size="text_size", color="text_color"),
        fontface="bold",
        tooltips="none",
    )
    + scale_size_identity()
    + scale_color_identity()
    + scale_fill_manual(values=colors, breaks=categories, name="Store type")
    + labs(title="map-marker-clustered · python · letsplot · anyplot.ai", caption=caption)
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_caption=element_text(size=10, hjust=0.5, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(800, 450)
    + xlim(-127, -65)
    + ylim(23, 51)
    # Interactive toolbar: zoom and pan into the clusters in the HTML view
    + ggtb()
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
