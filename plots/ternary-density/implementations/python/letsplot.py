""" anyplot.ai
ternary-density: Ternary Density Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-27
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_contour,
    geom_path,
    geom_point,
    geom_polygon,
    geom_raster,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    guide_colorbar,
    guides,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
    theme,
)
from scipy.stats import gaussian_kde


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp for fields (the colored cells fill the plot), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
CONTOUR_STEP = 0.25  # contour every quarter of the peak density (25 %, 50 %, 75 %)
GRID_SHARES = [0.2, 0.4, 0.6, 0.8]  # ternary grid line every 20 %
GRID_RESOLUTION = 360  # density cells across the triangle's base
SQRT3_2 = np.sqrt(3) / 2  # height of the unit equilateral triangle

# Columns: set these to your table's column names
SAND = "Sand"  # role: component_a
SILT = "Silt"  # role: component_b
CLAY = "Clay"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediment.csv")
rng = np.random.default_rng(42)
clusters = [([8, 2, 1], 180), ([2, 7, 2], 160), ([1, 2, 8], 160)]  # sand-rich, silt-rich, clay-rich samples
parts = np.vstack([rng.dirichlet(alpha, size) * 100 for alpha, size in clusters])
df = pd.DataFrame({SAND: parts[:, 0], SILT: parts[:, 1], CLAY: parts[:, 2]})

# Plot: reads only df and the constants above
# Ternary to Cartesian: bottom-left = Sand, bottom-right = Silt, top = Clay
share = df[[SAND, SILT, CLAY]].div(df[[SAND, SILT, CLAY]].sum(axis=1), axis=0)
points = pd.DataFrame(
    {
        "x": share[SILT] + share[CLAY] / 2,
        "y": SQRT3_2 * share[CLAY],
        SAND: df[SAND].round(1),
        SILT: df[SILT].round(1),
        CLAY: df[CLAY].round(1),
    }
)

# Gaussian KDE on a grid (Scott bandwidth); a missing component leaves the sample out of the density
kde = points.dropna(subset=["x", "y"])
gx = np.linspace(0, 1, GRID_RESOLUTION)
gy = np.linspace(0, SQRT3_2, round(GRID_RESOLUTION * SQRT3_2))
X, Y = np.meshgrid(gx, gy)
density = gaussian_kde(kde[["x", "y"]].to_numpy().T)(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

# Keep the cells that overlap the triangle: a margin of one cell leaves no gap along the slanted edges,
# and the outline covers the sliver that pokes out
margin = 2 * SQRT3_2 / GRID_RESOLUTION
inside = (Y <= 2 * SQRT3_2 * X + margin) & (Y <= 2 * SQRT3_2 * (1 - X) + margin)
density = np.where(inside, density, 0.0)
peak = density.max()
cells = pd.DataFrame({"x": X[inside], "y": Y[inside], "density": density[inside] / peak})

# Contour lines at shares of the peak density come from lets-plot on the same surface
surface = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "density": (density / peak).ravel()})

# Ternary grid: three sets of lines parallel to the triangle's sides
grid = pd.DataFrame(
    [
        segment
        for s in GRID_SHARES
        for segment in (
            {"x": s / 2, "xend": 1 - s / 2, "y": s * SQRT3_2, "yend": s * SQRT3_2},  # constant clay
            {"x": s, "xend": s + (1 - s) / 2, "y": 0.0, "yend": (1 - s) * SQRT3_2},  # constant silt
            {"x": 1 - s, "xend": (1 - s) / 2, "y": 0.0, "yend": (1 - s) * SQRT3_2},  # constant sand
        )
    ]
)
triangle = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, SQRT3_2, 0]})

# Page-colored frame around the triangle (a rectangle with the triangle cut out) hides the cells that poke past the edges
PAD = 0.04
frame = pd.DataFrame(
    {
        "x": [-PAD, 1 + PAD, 1 + PAD, -PAD, -PAD, 0, 0.5, 1, 0, -PAD],
        "y": [-PAD, -PAD, SQRT3_2 + PAD, SQRT3_2 + PAD, -PAD, 0, SQRT3_2, 0, 0, -PAD],
    }
)
vertices = pd.DataFrame({"x": [-0.05, 1.05, 0.5], "y": [-0.05, -0.05, SQRT3_2 + 0.06], "label": [SAND, SILT, CLAY]})

plot = (
    ggplot()
    + geom_raster(aes(x="x", y="y", fill="density"), data=cells)
    + scale_fill_gradientn(
        colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name="Relative density (peak = 1)"
    )
    + geom_polygon(aes(x="x", y="y"), data=frame, fill=PAGE_BG, color=PAGE_BG, size=0)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=grid, color="white", size=0.5, alpha=0.4)
    + geom_contour(aes(x="x", y="y", z="density"), data=surface, binwidth=CONTOUR_STEP, color="white", size=1.2)
    + geom_path(aes(x="x", y="y"), data=triangle, color=INK, size=1.6)
    + geom_point(
        aes(x="x", y="y"),
        data=points,
        size=3,
        alpha=0.01,
        tooltips=layer_tooltips().line(f"{SAND}: @{SAND}%").line(f"{SILT}: @{SILT}%").line(f"{CLAY}: @{CLAY}%"),
    )
    + geom_text(aes(x="x", y="y", label="label"), data=vertices, color=INK, size=9, fontface="bold")
    + labs(title="Sediment Composition · ternary-density · python · letsplot · anyplot.ai", x="", y="")
    + guides(fill=guide_colorbar(barwidth=260, barheight=14))
    + coord_fixed(ratio=1)
    + theme(
        plot_background=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(size=13, face="bold", color=INK),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=11, color=INK_SOFT),
    )
)

# The one-panel grid paints the page color over the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
