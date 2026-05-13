""" anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_polar,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsize,
    labs,
    scale_fill_viridis,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — website traffic by hour of day (angular) and day of week (radial)
np.random.seed(42)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

records = []
for d_idx, day in enumerate(days):
    for h in range(24):
        is_weekend = d_idx >= 5
        if not is_weekend:
            if 9 <= h <= 17:
                base = 750
            elif (6 <= h <= 8) or (18 <= h <= 21):
                base = 380
            else:
                base = 80
        else:
            if 11 <= h <= 20:
                base = 550
            elif (21 <= h <= 23) or h == 0:
                base = 260
            else:
                base = 60
        visits = max(10, int(base + np.random.normal(0, base * 0.10)))
        records.append({"day": day, "day_num": d_idx + 1, "hour_mid": h + 0.5, "visits": visits})

df = pd.DataFrame(records)

# Theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=14),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=22, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=14),
    legend_title=element_text(color=INK, size=16),
)

# Plot — polar heatmap: x=hour (angular), y=day_num (radial), fill=visits
plot = (
    ggplot(df, aes(x="hour_mid", y="day_num", fill="visits"))
    + geom_tile(color=PAGE_BG, size=0.5)
    + coord_polar(theta="x")
    + scale_fill_viridis(name="Hourly\nVisits")
    + scale_x_continuous(
        breaks=[0.5, 6.5, 12.5, 18.5], labels=["12am", "6am", "12pm", "6pm"], limits=[0, 24], expand=[0, 0]
    )
    + scale_y_continuous(breaks=list(range(1, 8)), labels=days, limits=[0, 7.5], expand=[0, 0])
    + labs(title="Website Traffic · heatmap-polar · letsplot · anyplot.ai", x="Hour of Day", y="Day of Week")
    + anyplot_theme
    + ggsize(900, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
