"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour from now"  # role: x
PM25 = "PM2.5 forecast (µg/m³)"  # role: y
LOWER = "Lower bound"  # role: y_lower
UPPER = "Upper bound"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Hourly PM2.5 air-quality forecast over 48 hours with a diurnal cycle and a 95% interval
rng = np.random.default_rng(42)
hours = np.arange(0, 48)
cycle = 22 + 9 * np.sin((hours - 6) * 2 * np.pi / 24)
forecast = cycle + rng.normal(0, 1.5, len(hours))
half_width = 1.96 * (0.8 + hours * 0.07)
df = pd.DataFrame({HOUR: hours, PM25: forecast, LOWER: forecast - half_width, UPPER: forecast + half_width})

# Plot
SERIES = "Series"
BAND_LABEL = "95% prediction interval"
LINE_LABEL = "Forecast"
band_df = df.assign(**{"Series": BAND_LABEL})
line_df = df.assign(**{"Series": LINE_LABEL})

plot = (
    ggplot(df, aes(x=HOUR))
    + geom_ribbon(aes(ymin=LOWER, ymax=UPPER, fill=SERIES), data=band_df, alpha=0.25, size=0)
    + geom_line(aes(y=PM25, color=SERIES), data=line_df, size=1.5)
    + scale_color_manual(values=[IMPRINT_PALETTE[0]])
    + scale_fill_manual(values=[IMPRINT_PALETTE[0]])
    + scale_x_continuous(breaks=list(range(0, int(df[HOUR].max()) + 1, 6)))
    + labs(x=HOUR, y=PM25, title="line-confidence · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_blank(),
        legend_position="top",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
