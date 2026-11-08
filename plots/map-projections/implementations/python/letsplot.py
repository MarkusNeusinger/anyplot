""" anyplot.ai
map-projections: World Map with Different Projections
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-23
"""

import json
import os
import urllib.request

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_map,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_polygon,
    ggplot,
    ggsize,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from PIL import Image as PILImage


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the Tissot circles are the one data series; land is the neutral muted anchor
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
ANYPLOT_MUTED = INK_MUTED

# Constants
WORLD_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_countries.geojson"
)
MERCATOR_LIMIT = 85  # Mercator runs to infinity at the poles; world maps cut it near ±85°
GRATICULE_STEP = 30  # degrees between graticule lines
TISSOT_RADIUS = 8  # degrees of arc on the globe, about 890 km
FILL_ALPHA = 0.55  # land and circles both translucent, so land shows through the circles

# Data: Natural Earth 1:110m country boundaries, one row per outline vertex
with urllib.request.urlopen(WORLD_URL, timeout=60) as response:
    world = json.load(response)

outlines = []
for feature in world["features"]:
    name = feature["properties"]["NAME"]
    geometry = feature["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    for part, polygon in enumerate(polygons):
        # The outer ring; the dataset's only hole is Lesotho, which is drawn as its own country
        ring = np.asarray(polygon[0])
        outlines.append(pd.DataFrame({"country": name, "part": f"{name} {part}", "lon": ring[:, 0], "lat": ring[:, 1]}))
countries = pd.concat(outlines, ignore_index=True)

# Plot: Antarctica's outline reaches the pole, which Mercator cannot draw
countries["lat"] = countries["lat"].clip(-MERCATOR_LIMIT, MERCATOR_LIMIT)
land_label = f"Land ({countries['country'].nunique()} countries)"
tissot_label = f"Tissot indicatrix ({TISSOT_RADIUS}° radius)"
countries["layer"] = land_label

# Graticule: parallels and meridians every GRATICULE_STEP degrees inside the map frame
parallels = range(-90 + GRATICULE_STEP, 90, GRATICULE_STEP)
meridians = range(-180 + GRATICULE_STEP, 180, GRATICULE_STEP)
graticule = pd.concat(
    [pd.DataFrame({"line": f"lat {lat}", "lon": np.linspace(-180, 180, 181), "lat": lat}) for lat in parallels]
    + [
        pd.DataFrame({"line": f"lon {lon}", "lon": lon, "lat": np.linspace(-MERCATOR_LIMIT, MERCATOR_LIMIT, 171)})
        for lon in meridians
    ],
    ignore_index=True,
)

# Tissot indicatrices: true circles of one radius on the sphere, centred on the graticule's
# crossings, so the projection alone changes their drawn size
theta = np.linspace(0, 2 * np.pi, 91)
delta = np.radians(TISSOT_RADIUS)
circles = []
for lat0 in range(-60, 61, GRATICULE_STEP):
    for lon0 in range(-150, 151, 2 * GRATICULE_STEP):
        phi0, lam0 = np.radians(lat0), np.radians(lon0)
        phi = np.arcsin(np.sin(phi0) * np.cos(delta) + np.cos(phi0) * np.sin(delta) * np.cos(theta))
        lam = lam0 + np.arctan2(
            np.sin(theta) * np.sin(delta) * np.cos(phi0), np.cos(delta) - np.sin(phi0) * np.sin(phi)
        )
        circles.append(
            pd.DataFrame(
                {"circle": f"{lat0} {lon0}", "lon": np.degrees(lam), "lat": np.degrees(phi), "layer": tissot_label}
            )
        )
tissot = pd.concat(circles, ignore_index=True)

# Axis ticks on the graticule, labelled with their hemisphere
lon_breaks = list(range(-180, 181, 2 * GRATICULE_STEP))
lon_labels = [f"{abs(v)}°" + ("W" if -180 < v < 0 else "E" if 0 < v < 180 else "") for v in lon_breaks]
lat_breaks = list(parallels)
lat_labels = [f"{abs(v)}°" + ("S" if v < 0 else "N" if v > 0 else "") for v in lat_breaks]

title = "Mercator Projection · map-projections · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_path(data=graticule, mapping=aes(x="lon", y="lat", group="line"), color=INK_SOFT, size=0.3, alpha=0.35)
    + geom_polygon(
        data=countries,
        mapping=aes(x="lon", y="lat", group="part", fill="layer", color="layer"),
        size=0.2,
        alpha=FILL_ALPHA,
        tooltips="none",
        # One layer draws the legend keys, so no key is painted twice at the marks' alpha
        show_legend=False,
    )
    + geom_polygon(
        data=tissot,
        mapping=aes(x="lon", y="lat", group="circle", fill="layer", color="layer"),
        size=0.5,
        alpha=FILL_ALPHA,
        tooltips="none",
    )
    # Country borders in the page color; Tissot circles outlined in their own hue
    + scale_fill_manual(values={land_label: ANYPLOT_MUTED, tissot_label: BRAND}, breaks=[land_label, tissot_label])
    + scale_color_manual(values={land_label: PAGE_BG, tissot_label: BRAND}, breaks=[land_label, tissot_label])
    + guides(fill=guide_legend(nrow=1, override_aes={"alpha": FILL_ALPHA}), color=guide_legend(nrow=1))
    + scale_x_continuous(breaks=lon_breaks, labels=lon_labels)
    + scale_y_continuous(breaks=lat_breaks, labels=lat_labels)
    + coord_map(xlim=[-180, 180], ylim=[-MERCATOR_LIMIT, MERCATOR_LIMIT])
    + labs(
        title=title,
        x="Longitude (°)",
        y="Latitude (°)",
        fill="",
        color="",
        caption="Equal circles on the globe stay round in Mercator but grow toward the poles\n"
        "Boundaries: Natural Earth 1:110m",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=13, face="bold", hjust=0.5, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_text_x=element_text(size=10, angle=0, color=INK_SOFT),
        plot_caption=element_text(size=10, hjust=0.5, color=INK_SOFT),
        legend_position="bottom",
        legend_text=element_text(size=11, color=INK_SOFT),
        legend_title=element_blank(),
        legend_background=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=INK_SOFT, size=0.5),
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")

# Flatten transparent margins to solid PAGE_BG: with the map's fixed aspect, lets-plot leaves
# the canvas outside the plot transparent
img = PILImage.open(f"plot-{THEME}.png").convert("RGBA")
bg = PILImage.new("RGBA", img.size, PAGE_BG)
bg.paste(img, mask=img.split()[3])
bg.convert("RGB").save(f"plot-{THEME}.png")
