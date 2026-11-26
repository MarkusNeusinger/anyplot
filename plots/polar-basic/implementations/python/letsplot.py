""" anyplot.ai
polar-basic: Basic Polar Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
"""

import math
import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.25)" if THEME == "light" else "rgba(240,239,232,0.25)"
BRAND = "#009E73"  # Imprint palette position 1

# Constants
CYCLE = 24  # one full turn of the circle is 24 hours
LABEL_STEP = 3  # angular labels every 3 hours

# Columns: set these to your table's column names
HOUR = "Hour"  # role: theta
TEMPERATURE = "Temperature (°C)"  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
np.random.seed(42)
hours = np.arange(0, CYCLE)
base_temp = 15 + 10 * np.sin((hours - 6) * math.pi / 12)
df = pd.DataFrame({HOUR: hours, TEMPERATURE: base_temp + np.random.randn(len(hours)) * 2})

# Plot: reads only df and the constants above
# Duplicate the first row at the end of the cycle to close the loop in polar coordinates
closing_row = df.iloc[[0]].copy()
closing_row[HOUR] = CYCLE
df_path = pd.concat([df, closing_row], ignore_index=True)

hour_breaks = list(range(0, CYCLE, LABEL_STEP))
hour_labels = [f"{h:02d}:00" for h in hour_breaks]

# Donut-hole radial scale: the lower limit sits well below the coldest reading so
# no hour collapses onto the origin where the angular gridlines converge.
t_min, t_max = df[TEMPERATURE].min(), df[TEMPERATURE].max()
span = t_max - t_min
radius_limits = [t_min - 0.4 * span, t_max + 0.1 * span]

# Hover tooltips on each hourly reading
point_tooltips = layer_tooltips().line(f"{HOUR}|@{{{HOUR}}}").line(f"{TEMPERATURE}|@{{{TEMPERATURE}}}")

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.4),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=14),
    axis_text=element_text(color=INK_SOFT, size=12),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=16),
)

plot = (
    ggplot(df_path, aes(x=HOUR, y=TEMPERATURE))
    + geom_polygon(fill=BRAND, color=BRAND, size=0, alpha=0.15)
    + geom_path(color=BRAND, size=1.2)
    + geom_point(data=df, color=BRAND, size=3, tooltips=point_tooltips)
    + scale_x_continuous(breaks=hour_breaks, labels=hour_labels, limits=[0, CYCLE], expand=[0, 0])
    + scale_y_continuous(limits=radius_limits, expand=[0, 0])
    + coord_polar(theta="x", start=0, direction=1)
    + labs(title="polar-basic · python · letsplot · anyplot.ai", x="", y=TEMPERATURE)
    + anyplot_theme
)

# The one-panel grid paints the whole square canvas in the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
