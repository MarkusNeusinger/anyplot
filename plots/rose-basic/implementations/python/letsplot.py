"""anyplot.ai
rose-basic: Basic Rose Chart
Library: letsplot 4.11.0 | Python 3.13.14
Quality: pending | Updated: 2026-07-25
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    gggrid,
    ggplot,
    ggsize,
    labs,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme-adaptive chrome (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — the only series

# Constants
TITLE = "Monthly Rainfall Distribution · rose-basic · python · letsplot · anyplot.ai"

# Columns
MONTH = "Month"  # role: category
RAINFALL = "Rainfall (mm)"  # role: value

# Data - Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 65, 82, 95, 120, 145, 168, 155, 130, 105, 85, 70]
df = pd.DataFrame({MONTH: months, RAINFALL: rainfall})

# Plot - Rose chart using polar coordinates; single metric uses one Imprint hue
rose = (
    ggplot(df, aes(x=MONTH, y=RAINFALL))
    + geom_bar(stat="identity", width=0.9, fill=BRAND, alpha=0.9, color=PAGE_BG, size=0.8)
    + coord_polar()
    + labs(title=TITLE, x="")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_major_x=element_blank(),  # drop angular spokes, keep radial rings
        panel_grid_minor=element_blank(),  # minor gridlines also draw angular spokes in polar coords
        plot_title=element_text(size=11, face="bold", color=INK),
        axis_title_y=element_text(size=12, color=INK),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=10, color=INK_SOFT),
    )
)

# coord_polar keeps a fixed aspect and leaves the rest of the canvas transparent;
# a one-panel grid paints the whole square canvas with the page color.
plot = gggrid([rose]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
