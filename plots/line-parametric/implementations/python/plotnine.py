"""anyplot.ai
line-parametric: Parametric Curve Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-06-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    ggplot,
    guide_colorbar,
    guide_legend,
    guides,
    labs,
    scale_color_gradientn,
    scale_fill_manual,
    scale_shape_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap — brand green → blue (single-polarity, direction of t)
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Marker fills from Imprint palette: green = start (matches gradient low), red = end (contrast)
MARKER_START = "#009E73"  # brand green
MARKER_END = "#AE3030"  # matte red — semantic contrast against blue path end

# Data — normalize t to [0, 1] per curve so both panels use the full color gradient
n_points = 1000
t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)
t_norm_liss = np.linspace(0, 1, n_points)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral) / (4 * np.pi)
y_spiral = t_spiral * np.sin(t_spiral) / (4 * np.pi)
t_norm_spiral = np.linspace(0, 1, n_points)

df = pd.concat(
    [
        pd.DataFrame(
            {"x": x_lissajous, "y": y_lissajous, "t_norm": t_norm_liss, "curve": "Lissajous · x = sin(3t), y = sin(2t)"}
        ),
        pd.DataFrame(
            {"x": x_spiral, "y": y_spiral, "t_norm": t_norm_spiral, "curve": "Spiral · x = t·cos(t), y = t·sin(t)"}
        ),
    ],
    ignore_index=True,
)

# Start and end markers for direction cues
markers = pd.concat(
    [
        pd.DataFrame(
            {
                "x": [x_lissajous[0], x_spiral[0]],
                "y": [y_lissajous[0], y_spiral[0]],
                "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
                "endpoint": ["Start (t = 0)", "Start (t = 0)"],
            }
        ),
        pd.DataFrame(
            {
                "x": [x_lissajous[-1], x_spiral[-1]],
                "y": [y_lissajous[-1], y_spiral[-1]],
                "curve": ["Lissajous · x = sin(3t), y = sin(2t)", "Spiral · x = t·cos(t), y = t·sin(t)"],
                "endpoint": ["End (t = tmax)", "End (t = tmax)"],
            }
        ),
    ],
    ignore_index=True,
)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="t_norm"))
    + geom_path(aes(group="curve"), size=1.0, alpha=0.94)
    + geom_point(
        aes(shape="endpoint", fill="endpoint"), data=markers, color=INK, size=3.5, stroke=0.8, show_legend=True
    )
    + scale_shape_manual(name="Direction", values={"Start (t = 0)": "o", "End (t = tmax)": "D"})
    + scale_fill_manual(name="Direction", values={"Start (t = 0)": MARKER_START, "End (t = tmax)": MARKER_END})
    + facet_wrap("curve", scales="free")
    + scale_color_gradientn(
        name="Parameter t",
        colors=IMPRINT_SEQ,
        breaks=[0.0, 0.25, 0.5, 0.75, 1.0],
        labels=["0", "¼", "½", "¾", "tmax"],
        guide=guide_colorbar(nbin=200),
    )
    + coord_equal()
    + labs(
        title="line-parametric · python · plotnine · anyplot.ai",
        x="Horizontal Position  x(t)",
        y="Vertical Position  y(t)",
    )
    + guides(shape=guide_legend(order=2), fill=guide_legend(order=2))
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 8}),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 6}),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 6}),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_ticks=element_blank(),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_box_margin=4,
        strip_text=element_text(size=9, weight="bold", color=INK, margin={"b": 6}),
        strip_background=element_rect(fill=ELEVATED_BG, color="none"),
        panel_spacing_x=0.1,
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.15),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        plot_margin=0.01,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
