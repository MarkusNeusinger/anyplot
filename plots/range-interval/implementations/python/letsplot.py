""" anyplot.ai
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT1 = "#D55E00"  # Okabe-Ito position 2
ACCENT2 = "#0072B2"  # Okabe-Ito position 3

# Data: Monthly temperature ranges (°C) for a weather station
data = {
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "min_temp": [-2, 0, 4, 8, 13, 17, 19, 18, 14, 9, 4, 0],
    "max_temp": [6, 8, 12, 17, 22, 26, 29, 28, 24, 18, 11, 7],
}

df = pd.DataFrame(data)

# Calculate midpoint for reference markers
df["mid_temp"] = (df["min_temp"] + df["max_temp"]) / 2

# Preserve month order
df["month"] = pd.Categorical(df["month"], categories=data["month"], ordered=True)

# Create range interval chart
plot = (
    ggplot(df)
    # Range bars as thick vertical segments (data-driven)
    + geom_segment(aes(x="month", xend="month", y="min_temp", yend="max_temp"), size=8, color=BRAND, alpha=0.7)
    # Min endpoint markers (hollow circles)
    + geom_point(aes(x="month", y="min_temp"), size=5, color=BRAND, shape=1, stroke=2)
    # Max endpoint markers (triangles)
    + geom_point(aes(x="month", y="max_temp"), size=5, color=ACCENT1, shape=2, stroke=2)
    # Midpoint markers (solid circles)
    + geom_point(aes(x="month", y="mid_temp"), size=4, color=ACCENT2, shape=16)
    # Labels and title
    + labs(x="Month", y="Temperature (°C)", title="range-interval · python · letsplot · anyplot.ai")
    # Theme for large canvas and theme-adaptive styling
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.4),
        axis_line_y=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")

# Save as HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html", path=".")
