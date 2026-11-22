"""anyplot.ai
range-interval: Range Interval Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND, ACCENT1, ACCENT2 = IMPRINT_PALETTE[:3]

# Columns
MONTH = "Month"  # role: category
MIN_TEMP = "Minimum (°C)"  # role: min_value
MAX_TEMP = "Maximum (°C)"  # role: max_value
MID_TEMP = "Midpoint (°C)"

# Data: monthly temperature ranges (°C) for a weather station
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        MIN_TEMP: [-2, 0, 4, 8, 13, 17, 19, 18, 14, 9, 4, 0],
        MAX_TEMP: [6, 8, 12, 17, 22, 26, 29, 28, 24, 18, 11, 7],
    }
)
df[MID_TEMP] = (df[MIN_TEMP] + df[MAX_TEMP]) / 2

# Plot
plot = (
    ggplot(df)
    + geom_segment(aes(x=MONTH, xend=MONTH, y=MIN_TEMP, yend=MAX_TEMP), size=4, color=BRAND, alpha=0.7)
    + geom_point(aes(x=MONTH, y=MIN_TEMP), size=2.5, color=BRAND, shape=1, stroke=1)
    + geom_point(aes(x=MONTH, y=MAX_TEMP), size=2.5, color=ACCENT1, shape=2, stroke=1)
    + geom_point(aes(x=MONTH, y=MID_TEMP), size=2, color=ACCENT2, shape=16)
    + labs(x=MONTH, y="Temperature (°C)", title="range-interval · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.2),
        axis_line_y=element_line(color=INK_SOFT, size=0.2),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
