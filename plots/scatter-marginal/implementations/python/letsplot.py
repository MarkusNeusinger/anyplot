""" anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data - bivariate data with correlation
np.random.seed(42)
n = 200
x = np.random.randn(n) * 2 + 10
y = x * 0.8 + np.random.randn(n) * 1.5 + 2

df = pd.DataFrame({"x": x, "y": y})

# Calculate axis limits for aligned marginal plots
x_min, x_max = df["x"].min() - 0.5, df["x"].max() + 0.5
y_min, y_max = df["y"].min() - 0.5, df["y"].max() + 0.5

# Main scatter plot
main_scatter = (
    ggplot(df, aes(x="x", y="y"))  # noqa: F405
    + geom_point(color=BRAND, size=4, alpha=0.65)  # noqa: F405
    + labs(  # noqa: F405
        x="Measurement A", y="Measurement B", title="scatter-marginal · letsplot · anyplot.ai"
    )
    + scale_x_continuous(limits=[x_min, x_max])  # noqa: F405
    + scale_y_continuous(limits=[y_min, y_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        axis_text=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT),  # noqa: F405
    )
)

# Top marginal histogram with KDE overlay
top_hist = (
    ggplot(df, aes(x="x"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        fill=BRAND,
        color=PAGE_BG,
        alpha=0.5,
        bins=25,
    )
    + geom_density(color=ACCENT, size=1.5, alpha=0.8)  # noqa: F405
    + scale_x_continuous(limits=[x_min, x_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.15),  # noqa: F405
        axis_title=element_blank(),  # noqa: F405
        axis_text_x=element_blank(),  # noqa: F405
        axis_ticks_x=element_blank(),  # noqa: F405
        axis_text_y=element_text(size=14, color=INK_SOFT),  # noqa: F405
        axis_line_x=element_blank(),  # noqa: F405
    )
)

# Right marginal histogram with KDE overlay
right_hist = (
    ggplot(df, aes(x="y"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        fill=BRAND,
        color=PAGE_BG,
        alpha=0.5,
        bins=25,
    )
    + geom_density(color=ACCENT, size=1.5, alpha=0.8)  # noqa: F405
    + coord_flip()  # noqa: F405
    + scale_x_continuous(limits=[y_min, y_max])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.15),  # noqa: F405
        axis_title=element_blank(),  # noqa: F405
        axis_text_y=element_blank(),  # noqa: F405
        axis_ticks_y=element_blank(),  # noqa: F405
        axis_text_x=element_text(size=14, color=INK_SOFT),  # noqa: F405
        axis_line_y=element_blank(),  # noqa: F405
    )
)

# Combine using ggbunch
combined = (
    ggbunch(  # noqa: F405
        [top_hist, main_scatter, right_hist],
        [
            (0, 0.0, 0.76, 0.18),  # Top histogram
            (0, 0.18, 0.76, 0.82),  # Main scatter plot
            (0.76, 0.18, 0.24, 0.82),  # Right histogram (aligned to bottom of main plot)
        ],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(combined, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(combined, filename=f"plot-{THEME}.html", path=".")
