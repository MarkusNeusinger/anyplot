"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_blank,
    geom_density,
    geom_histogram,
    geom_point,
    ggbunch,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
ACCENT = IMPRINT_PALETTE[1]

# Constants
TITLE = "scatter-marginal · python · letsplot · anyplot.ai"
N_POINTS = 200

# Columns
X_VALUE = "Measurement A"  # role: x
Y_VALUE = "Measurement B"  # role: y

# Data
np.random.seed(42)
x = np.random.randn(N_POINTS) * 2 + 10
y = x * 0.8 + np.random.randn(N_POINTS) * 1.5 + 2
df = pd.DataFrame({X_VALUE: x, Y_VALUE: y})

# Plot
# Shared axis limits so the marginals line up with the scatter
x_lim = [df[X_VALUE].min() - 0.5, df[X_VALUE].max() + 0.5]
y_lim = [df[Y_VALUE].min() - 0.5, df[Y_VALUE].max() + 0.5]

base_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
)

main_scatter = (
    ggplot(df, aes(x=X_VALUE, y=Y_VALUE))
    + geom_point(color=BRAND, size=3, alpha=0.65)
    + labs(title=TITLE)
    + scale_x_continuous(limits=x_lim)
    + scale_y_continuous(limits=y_lim)
    + base_theme
    + theme(
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
    )
)

top_marginal = (
    ggplot(df, aes(x=X_VALUE))
    + geom_histogram(aes(y="..density.."), fill=BRAND, color=PAGE_BG, alpha=0.5, bins=25)
    + geom_density(color=ACCENT, size=1.2)
    + scale_x_continuous(limits=x_lim)
    + base_theme
    + theme(
        axis_title=element_blank(),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_text_y=element_text(size=9, color=INK_SOFT),
        axis_line_x=element_blank(),
        plot_margin=[0, 3, 0, 13],
    )
)

right_marginal = (
    ggplot(df, aes(x=Y_VALUE))
    + geom_histogram(aes(y="..density.."), fill=BRAND, color=PAGE_BG, alpha=0.5, bins=25)
    + geom_density(color=ACCENT, size=1.2)
    + coord_flip()
    + scale_x_continuous(limits=y_lim)
    + base_theme
    + theme(
        axis_title=element_blank(),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        axis_text_x=element_text(size=9, color=INK_SOFT),
        axis_line_y=element_blank(),
        plot_margin=[19, 0, 27, 0],
    )
)

# Empty top-right corner, filled with the page background
corner = ggplot(df) + geom_blank() + theme_void() + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

combined = ggbunch(
    [top_marginal, main_scatter, right_marginal, corner],
    [
        (0, 0.0, 0.76, 0.18),  # top marginal
        (0, 0.18, 0.76, 0.82),  # main scatter
        (0.76, 0.18, 0.24, 0.82),  # right marginal
        (0.76, 0.0, 0.24, 0.18),  # corner
    ],
) + ggsize(800, 450)

# Save
ggsave(combined, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(combined, filename=f"plot-{THEME}.html", path=".")
