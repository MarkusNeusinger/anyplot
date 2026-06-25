"""anyplot.ai
contour-basic: Basic Contour Plot
Library: plotnine 0.15.7 | Python 3.13
Quality: 80/100 | Updated: 2026-06-25
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
_here = os.path.dirname(os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)
if "" in sys.path:
    sys.path.remove("")

import contourpy
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_raster,
    ggplot,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Atmospheric pressure field: two-cell anticyclone system over a regional domain
np.random.seed(42)
lon = np.linspace(-10, 10, 150)
lat = np.linspace(-8, 8, 150)
Lon, Lat = np.meshgrid(lon, lat)

pressure = (
    1013.0
    + 12.0 * np.exp(-((Lon - 3) ** 2 + (Lat - 2) ** 2) / 8)
    + 7.0 * np.exp(-((Lon + 5) ** 2 + (Lat + 3) ** 2) / 10)
    - 5.0 * np.exp(-((Lon - 1) ** 2 + (Lat + 5) ** 2) / 4)
)

raster_df = pd.DataFrame({"lon": Lon.ravel(), "lat": Lat.ravel(), "hpa": pressure.ravel()})

# Extract isoline segments via contourpy (plotnine 0.15 lacks geom_contour)
p_levels = np.linspace(pressure.min(), pressure.max(), 12)
generator = contourpy.contour_generator(x=Lon, y=Lat, z=pressure)
segments = [
    (np.asarray(seg), gid)
    for gid, seg in enumerate(s for lvl in p_levels for s in generator.lines(lvl))
    if np.asarray(seg).shape[0] >= 2
]
line_df = pd.concat(
    [pd.DataFrame({"lon": seg[:, 0], "lat": seg[:, 1], "group": gid}) for seg, gid in segments], ignore_index=True
)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=10),
    legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
)

plot = (
    ggplot()
    + geom_raster(raster_df, aes(x="lon", y="lat", fill="hpa"))
    + geom_path(line_df, aes(x="lon", y="lat", group="group"), color="#FFFDF6", size=0.5, alpha=0.65)
    + annotate("text", x=3.0, y=2.2, label="H", color=INK, size=4)
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Pressure\n(hPa)")
    + labs(x="Longitude (°E)", y="Latitude (°N)", title="contour-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
