""" anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-08
"""

import os
import sys


# Work around naming conflict between this file (plotnine.py) and the plotnine package
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _p in (_script_dir, "", "."):
    if _p in sys.path:
        sys.path.remove(_p)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_path,
    geom_polygon,
    geom_rect,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradient,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: 16 African countries on a schematic grid that keeps rough geographic adjacency, plus their real
# centroids (lon, lat) for the undistorted reference map.
# (name, abbrev, grid_x, grid_y, lon, lat, population_M, total_area_thousand_km2, urbanization_pct)
COUNTRIES = [
    ("Morocco", "MA", -3.0, 10.0, -6.5, 31.8, 38.0, 447, 65),
    ("Algeria", "DZ", 4.0, 10.0, 2.6, 28.0, 46.0, 2382, 75),
    ("Egypt", "EG", 14.0, 10.0, 30.0, 26.5, 105.0, 1001, 43),
    ("Mali", "ML", 0.0, 5.0, -2.0, 17.5, 23.0, 1240, 44),
    ("Niger", "NE", 8.0, 5.0, 9.4, 17.6, 27.0, 1267, 17),
    ("Sudan", "SD", 14.0, 4.5, 30.0, 15.5, 46.0, 1886, 36),
    ("Ethiopia", "ET", 20.0, 3.0, 39.6, 8.6, 126.0, 1104, 24),
    ("Nigeria", "NG", 2.0, -1.0, 8.1, 9.6, 220.0, 924, 54),
    ("Ghana", "GH", -3.0, -4.5, -1.0, 7.9, 33.0, 239, 58),
    ("Cameroon", "CM", 9.0, -1.0, 12.7, 5.7, 28.0, 475, 59),
    ("Kenya", "KE", 18.0, -3.0, 37.9, 0.2, 55.0, 580, 29),
    ("DR Congo", "CD", 11.0, -7.0, 23.6, -2.9, 100.0, 2345, 46),
    ("Tanzania", "TZ", 17.5, -8.5, 34.9, -6.4, 65.0, 947, 38),
    ("Angola", "AO", 8.0, -13.0, 17.5, -12.3, 36.0, 1247, 68),
    ("Zambia", "ZM", 14.0, -13.0, 27.8, -13.1, 20.0, 753, 46),
    ("Mozambique", "MZ", 20.5, -13.0, 35.5, -17.3, 33.0, 802, 38),
]
df = pd.DataFrame(COUNTRIES, columns=["country", "abbrev", "x", "y", "lon", "lat", "pop", "area", "urb"])

# Coarse coastline of the African continent (lon, lat) for the reference map inset
AFRICA_COAST = [
    (-17, 21), (-16, 28), (-10, 30), (-6, 36), (10, 37), (11, 33), (20, 31), (25, 32), (32, 31), (35, 28),
    (39, 22), (43, 12), (51, 12), (42, -1), (40, -10), (40, -16), (35, -24), (32, -29), (26, -34), (20, -35),
    (18, -32), (12, -18), (13, -12), (9, -1), (9, 4), (5, 6), (-3, 5), (-8, 4), (-13, 8), (-17, 14), (-17, 21),
]  # fmt: skip
coast = pd.DataFrame(AFRICA_COAST, columns=["lon", "lat"])

# Plot: hexagon area ∝ population; the dashed outline is the same hexagon with its area ∝ the country's
# total area, scaled so both sets cover the same total, which makes the outline the undistorted reference
BASE_R = 1.6  # radius of a country with the median population, in data units
median_pop = df["pop"].median()
total_pop = df["pop"].sum()
people_per_area = total_pop / df["area"].sum()  # million people per thousand km², the group's average density
df["r_pop"] = BASE_R * np.sqrt(df["pop"] / median_pop)
df["r_area"] = BASE_R * np.sqrt(df["area"] * people_per_area / median_pop)

# Closed pointy-top hexagon: seven vertices, the last repeating the first
angles = np.linspace(0, 2 * np.pi, 7) + np.pi / 6
vertices = df.merge(pd.DataFrame({"dx": np.cos(angles), "dy": np.sin(angles)}), how="cross")
for kind in ("pop", "area"):
    vertices[f"x_{kind}"] = vertices["x"] + vertices[f"r_{kind}"] * vertices["dx"]
    vertices[f"y_{kind}"] = vertices["y"] + vertices[f"r_{kind}"] * vertices["dy"]

x_min = vertices[["x_pop", "x_area"]].min().min()
x_max = vertices[["x_pop", "x_area"]].max().max()
y_min = vertices[["y_pop", "y_area"]].min().min()
y_max = vertices[["y_pop", "y_area"]].max().max()
pad = 0.03 * (y_max - y_min)

# Reference map inset in the lower-left corner: the real geography, each country a hexagon at its true
# centroid with its area ∝ land area, so the reader can compare against the distorted layout above
geo_vertices = pd.concat([coast[["lon", "lat"]], df[["lon", "lat"]]])
lon_lo, lon_hi = geo_vertices["lon"].min(), geo_vertices["lon"].max()
lat_lo, lat_hi = geo_vertices["lat"].min(), geo_vertices["lat"].max()
inset_scale = 0.26 * (x_max - x_min) / (lon_hi - lon_lo)  # inset spans about a quarter of the map's width
inset_x0 = x_min + 0.6 * pad
inset_y0 = y_min + 0.6 * pad
coast["ix"] = inset_x0 + (coast["lon"] - lon_lo) * inset_scale
coast["iy"] = inset_y0 + (coast["lat"] - lat_lo) * inset_scale
km_per_degree = 111.0
geo_r = 0.75 * np.sqrt(vertices["area"] * 1000 / np.pi) / km_per_degree * inset_scale  # 0.75 × true scale
vertices["ix"] = inset_x0 + (vertices["lon"] - lon_lo) * inset_scale + geo_r * vertices["dx"]
vertices["iy"] = inset_y0 + (vertices["lat"] - lat_lo) * inset_scale + geo_r * vertices["dy"]
frame = pd.DataFrame(
    {
        "xmin": [inset_x0 - 0.4 * pad],
        "xmax": [coast["ix"].max() + 0.4 * pad],
        "ymin": [inset_y0 - 0.4 * pad],
        "ymax": [coast["iy"].max() + 0.4 * pad],
    }
)

subtitle = (
    f"Hexagon area ∝ population: {total_pop:.0f}M people in {len(df)} African countries\n"
    "Dashed outline = the country's total area at the same scale; inset = the real map"
)
caption = (
    "Fill larger than its dashed outline: denser than the group average of "
    f"{people_per_area * 1000:.0f} people per km²\n"
    "Color = share of the population living in cities (2024)"
)

plot = (
    ggplot(vertices)
    # Cartogram hexagons filled by urbanization rate (Imprint sequential: green = rural → blue = urban)
    + geom_polygon(aes(x="x_pop", y="y_pop", group="country", fill="urb"), color=INK, size=0.35, alpha=0.9)
    # Dashed reference outlines on top, so they read inside and outside the fill alike
    + geom_path(aes(x="x_area", y="y_area", group="country"), color=INK, size=0.4, linetype="dashed", alpha=0.75)
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Urbanization\nRate (%)", guide=guide_colorbar(nbin=100))
    # Reference map inset: real coastline and true country positions, hexagon area ∝ land area
    + geom_rect(
        frame,
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        inherit_aes=False,
        fill=ELEVATED_BG,
        color=INK_SOFT,
        size=0.3,
    )
    + geom_polygon(coast, aes(x="ix", y="iy"), inherit_aes=False, fill=PAGE_BG, color=INK_SOFT, size=0.35)
    + geom_polygon(aes(x="ix", y="iy", group="country", fill="urb"), color=INK, size=0.2, alpha=0.9)
    + annotate(
        "text",
        x=frame["xmin"].iloc[0],
        y=frame["ymax"].iloc[0] + 0.3 * pad,
        label="Undistorted map: area ∝ land area",
        ha="left",
        va="bottom",
        size=6.5,
        color=INK_SOFT,
        fontstyle="italic",
    )
    + geom_label(
        df,
        aes(x="x", y="y", label="abbrev"),
        color=INK,
        fill=ELEVATED_BG,
        size=7,
        fontweight="bold",
        label_padding=0.2,
        label_size=0.3,
    )
    + coord_fixed(ratio=1.0, xlim=(x_min - pad, x_max + pad), ylim=(y_min - pad, y_max + pad), expand=False)
    + labs(title="cartogram-area-distortion · python · plotnine · anyplot.ai", subtitle=subtitle, caption=caption)
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title_position="plot",
        plot_caption_position="plot",
        plot_title=element_text(size=10.5, ha="left", weight="bold", color=INK, margin={"b": 4}),
        plot_subtitle=element_text(size=8, ha="left", color=INK_SOFT, linespacing=1.4, margin={"b": 6}),
        plot_caption=element_text(size=7.5, ha="left", color=INK_SOFT, linespacing=1.4, margin={"t": 6}),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        plot_margin=0.02,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
