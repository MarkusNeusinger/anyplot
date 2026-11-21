"""anyplot.ai
line-markers: Line Plot with Markers
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MARKER_SHAPES = ["o", "s", "^", "D", "v", "P", "X", "*"]  # one distinct shape per series

# Columns: set these to your table's column names
WEEK = "Week"  # role: x
SESSIONS = ["Organic search", "Email", "Social media"]  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("sessions.csv")
df = pd.DataFrame(
    {
        WEEK: list(range(1, 13)),
        # steady growth
        SESSIONS[0]: [42.1, 44.3, 43.8, 47.2, 49.5, 51.0, 50.2, 54.8, 57.1, 58.6, 61.3, 63.9],
        # spikes in campaign weeks
        SESSIONS[1]: [18.5, 17.9, 26.4, 19.2, 18.8, 27.9, 20.1, 19.5, 29.3, 21.0, 20.4, 31.2],
        # one viral week, then a decay
        SESSIONS[2]: [12.3, 13.1, 12.8, 14.6, 13.9, 38.5, 31.2, 24.8, 19.6, 16.4, 15.1, 14.3],
    }
)

# Plot
CHANNEL = "Channel"
VALUE = "Sessions (thousands)"
long_df = df.melt(id_vars=WEEK, value_vars=SESSIONS, var_name=CHANNEL, value_name=VALUE)
series = list(SESSIONS)
title = "line-markers · python · plotnine · anyplot.ai"

anyplot_theme = theme(
    figure_size=(8, 4.5),
    text=element_text(size=7),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=12, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    legend_position="right",
)

plot = (
    ggplot(long_df, aes(x=WEEK, y=VALUE, color=CHANNEL, shape=CHANNEL))
    + geom_line(size=1.0, alpha=0.85)
    + geom_point(size=2.5)
    + scale_x_continuous(breaks=sorted(df[WEEK].dropna().unique().tolist()))
    + scale_color_manual(values=IMPRINT_PALETTE, limits=series)
    + scale_shape_manual(values=MARKER_SHAPES, limits=series)
    + labs(title=title)
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
