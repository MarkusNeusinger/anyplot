"""anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-07
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_color_gradientn,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint continuous ramp for marks (colored line on the page), as (position, hex) stops
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
INNER_RADIUS = 1.5  # radius of the spiral at the start of the first cycle; one cycle adds 1.0

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TEMPERATURE = "Temp (°C)"  # role: value
CYCLE_PERIOD = "Cycle period"  # role: cycle_period

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv", parse_dates=["Date"])
# 5 years of synthetic daily average temperatures (northern hemisphere); one spiral revolution per year
np.random.seed(42)
dates = pd.date_range("2019-01-01", "2023-12-31", freq="D")
days_in_year = np.where(dates.is_leap_year, 366, 365)
temperature = 15.0 * np.sin(2 * np.pi * (dates.day_of_year.values - 80) / days_in_year) + 12.0
temperature = temperature + np.random.normal(0, 2.0, len(dates))
df = pd.DataFrame({DATE: dates, TEMPERATURE: temperature, CYCLE_PERIOD: "year"})

# Plot: reads only df and the constants above
first_year = df[DATE].dt.year.min()
n_cycles = df[DATE].dt.year.max() - first_year + 1


def spiral_xy(stamps):
    """Archimedean spiral, clockwise from 12 o'clock: one revolution per calendar year, earliest at the center."""
    stamps = pd.DatetimeIndex(stamps)
    year_len = np.where(stamps.is_leap_year, 366, 365)
    turns = (stamps.year - first_year) + (stamps.day_of_year.values - 1) / year_len
    angle = np.pi / 2 - 2 * np.pi * turns
    radius = INNER_RADIUS + turns
    return radius * np.cos(angle), radius * np.sin(angle)


path_x, path_y = spiral_xy(df[DATE])
path = pd.DataFrame({"x": path_x, "y": path_y, TEMPERATURE: df[TEMPERATURE].values})

# Radial grid lines from the center to the spiral at every month start
month_starts = pd.date_range(df[DATE].min().to_period("M").start_time, df[DATE].max(), freq="MS")
gx, gy = spiral_xy(month_starts)
grid = pd.DataFrame({"x": 0.0, "y": 0.0, "xend": gx, "yend": gy})

# Year labels slightly left of the top spoke, at the start of each cycle
label_angle = np.pi / 2 + 0.2
label_r = INNER_RADIUS + np.arange(n_cycles)
year_labels = pd.DataFrame(
    {
        "x": label_r * np.cos(label_angle),
        "y": label_r * np.sin(label_angle),
        "label": [str(first_year + k) for k in range(n_cycles)],
    }
)

# Month labels on the outer ring, at mid-month angles of a leap-year reference
ring_r = INNER_RADIUS + n_cycles + 0.75
mid_month = pd.date_range("2020-01-01", periods=12, freq="MS") + pd.Timedelta(days=14)
mid_angle = np.pi / 2 - 2 * np.pi * (mid_month.day_of_year.values - 1) / 366
month_labels = pd.DataFrame({"x": ring_r * np.cos(mid_angle), "y": ring_r * np.sin(mid_angle), "label": MONTHS})

title = "Daily Temperatures · spiral-timeseries · python · letsplot · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

anyplot_theme = theme_void() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    plot_title=element_text(color=INK, size=title_size),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=14),
    legend_title=element_text(color=INK, size=14),
)

plot = (
    ggplot()
    + geom_segment(data=grid, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, alpha=0.3, size=0.4)
    + geom_path(data=path, mapping=aes(x="x", y="y", color=TEMPERATURE), size=2.2)
    + scale_color_gradientn(colors=[ramp_color(SEQ_MARKS, k / 255) for k in range(256)], name=TEMPERATURE)
    + geom_text(data=year_labels, mapping=aes(x="x", y="y", label="label"), color=INK, size=9, fontface="bold")
    + geom_text(data=month_labels, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=9)
    + coord_fixed()
    + labs(title=title)
    + anyplot_theme
)

# A fixed aspect leaves the canvas edges unpainted: a one-panel grid carries the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
