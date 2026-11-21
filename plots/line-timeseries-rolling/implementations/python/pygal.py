"""anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 7  # rolling window in days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VALUE = "Temperature (°C)"  # role: value
ROLLING_AVG = "7-Day Rolling Average"  # role: rolling_avg

# Data: replace this block with your own table, for example df = pd.read_csv("sensor.csv", parse_dates=[DATE])
rng = np.random.default_rng(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
seasonal = 5 + 8 * np.arange(n_days) / n_days
df = pd.DataFrame({DATE: dates, VALUE: (seasonal + rng.normal(0, 3, n_days)).round(1)})
df[ROLLING_AVG] = df[VALUE].rolling(WINDOW).mean().round(1)

# Plot: reads only df and the constants above
title = "line-timeseries-rolling · python · pygal · anyplot.ai"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

chart = pygal.DateTimeLine(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=DATE,
    y_title=VALUE,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    x_value_formatter=lambda d: d.strftime("%b %d"),
    x_labels=[d.to_pydatetime() for d in pd.date_range(df[DATE].min(), df[DATE].max(), freq="MS")]
    + [d.to_pydatetime() for d in pd.date_range(df[DATE].min(), df[DATE].max(), freq="MS") + pd.Timedelta(days=14)],
)

# Raw data: thin, semi-transparent; rolling average: thick and opaque, starting once the window is filled
raw = list(zip(df[DATE].dt.to_pydatetime(), df[VALUE], strict=True))
rolled = df.dropna(subset=[ROLLING_AVG])
smooth = list(zip(rolled[DATE].dt.to_pydatetime(), rolled[ROLLING_AVG], strict=True))
chart.add("Raw Data", raw, stroke_style={"width": 4, "opacity": 0.55})
chart.add(ROLLING_AVG, smooth, stroke_style={"width": 12})

# Save as theme-suffixed PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
