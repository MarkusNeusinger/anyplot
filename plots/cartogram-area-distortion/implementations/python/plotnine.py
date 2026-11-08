""" anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 82/100 | Updated: 2026-06-08
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
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_path,
    geom_polygon,
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

# Data: 16 African countries on a schematic grid that keeps rough geographic adjacency.
# (name, abbrev, centroid_x, centroid_y, population_M, total_area_thousand_km2, urbanization_pct)
COUNTRIES = [
    ("Morocco", "MA", -3.0, 10.0, 38.0, 447, 65),
    ("Algeria", "DZ", 4.0, 10.0, 46.0, 2382, 75),
    ("Egypt", "EG", 14.0, 10.0, 105.0, 1001, 43),
    ("Mali", "ML", 0.0, 5.0, 23.0, 1240, 44),
    ("Niger", "NE", 8.0, 5.0, 27.0, 1267, 17),
    ("Sudan", "SD", 14.0, 4.5, 46.0, 1886, 36),
    ("Ethiopia", "ET", 20.0, 3.0, 126.0, 1104, 24),
    ("Nigeria", "NG", 2.0, -1.0, 220.0, 924, 54),
    ("Ghana", "GH", -3.0, -4.5, 33.0, 239, 58),
    ("Cameroon", "CM", 9.0, -1.0, 28.0, 475, 59),
    ("Kenya", "KE", 18.0, -3.0, 55.0, 580, 29),
    ("DR Congo", "CD", 11.0, -7.0, 100.0, 2345, 46),
    ("Tanzania", "TZ", 17.5, -8.5, 65.0, 947, 38),
    ("Angola", "AO", 8.0, -13.0, 36.0, 1247, 68),
    ("Zambia", "ZM", 14.0, -13.0, 20.0, 753, 46),
    ("Mozambique", "MZ", 20.5, -13.0, 33.0, 802, 38),
]
df = pd.DataFrame(COUNTRIES, columns=["country", "abbrev", "x", "y", "pop", "area", "urb"])

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

subtitle = (
    f"Hexagon area ∝ population: {total_pop:.0f}M people in {len(df)} African countries\n"
    "Dashed outline = the country's total area at the same scale"
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
