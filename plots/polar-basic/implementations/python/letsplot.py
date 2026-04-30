"""anyplot.ai
polar-basic: Basic Polar Chart
Library: letsplot | Python 3.13
Quality: 91/100 | Updated: 2026-04-30
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
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Hourly temperature readings (24 hours)
np.random.seed(42)
hours = np.arange(0, 24)
base_temp = 15 + 10 * np.sin((hours - 6) * math.pi / 12)
temperatures = base_temp + np.random.randn(24) * 2

df = pd.DataFrame({"hour": hours, "temperature": temperatures})
# Duplicate first point at hour=24 to close the loop in polar coordinates
df_path = pd.concat([df, df.iloc[[0]].assign(hour=24)], ignore_index=True)

# Hour labels at standard 3-hour intervals
hour_breaks = [0, 3, 6, 9, 12, 15, 18, 21]
hour_labels = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]

# Theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=14),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=24),
)

# Plot using coord_polar for idiomatic lets-plot polar chart
plot = (
    ggplot(df_path, aes(x="hour", y="temperature"))
    + geom_path(color=BRAND, size=1.5)
    + geom_point(data=df, color=BRAND, size=5)
    + scale_x_continuous(breaks=hour_breaks, labels=hour_labels, limits=[0, 24], expand=[0, 0])
    + coord_polar(theta="x", start=0, direction=1)
    + labs(title="polar-basic · letsplot · anyplot.ai", x="", y="Temperature (°C)")
    + ggsize(1200, 1200)
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
