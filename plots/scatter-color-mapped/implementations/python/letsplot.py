""" anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import element_line, element_rect, element_text, theme
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Simulating temperature readings across a spatial grid
np.random.seed(42)
n_points = 150

# Create spatial coordinates with some clustering
x = np.concatenate(
    [
        np.random.normal(20, 8, n_points // 3),
        np.random.normal(50, 10, n_points // 3),
        np.random.normal(75, 6, n_points - 2 * (n_points // 3)),
    ]
)
y = np.concatenate(
    [
        np.random.normal(30, 10, n_points // 3),
        np.random.normal(60, 12, n_points // 3),
        np.random.normal(40, 8, n_points - 2 * (n_points // 3)),
    ]
)

# Temperature as third variable - correlated with position
temperature = 15 + 0.2 * x + 0.15 * y + np.random.normal(0, 3, n_points)

df = pd.DataFrame({"x": x, "y": y, "temperature": temperature})

# Create the color-mapped scatter plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, linetype="solid"),
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
)

plot = (
    ggplot(df, aes(x="x", y="y", color="temperature"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=6.5,
        alpha=0.8,
        tooltips=layer_tooltips()  # noqa: F405
        .line("X Coord|@x")
        .line("Y Coord|@y")
        .line("Temperature|@temperature"),
    )
    + scale_color_viridis(name="Temperature (°C)")  # noqa: F405
    + labs(  # noqa: F405
        x="X Coordinate (m)", y="Y Coordinate (m)", title="scatter-color-mapped · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x to get 4800 × 2700 px)
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
