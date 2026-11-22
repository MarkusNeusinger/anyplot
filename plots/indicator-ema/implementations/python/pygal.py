"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-19
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
SHORT_SPAN = 12  # fast EMA period in trading days
LONG_SPAN = 26  # slow EMA period in trading days
LABEL_EVERY = 20  # one major x label per this many trading days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price (USD/bbl)"  # role: close
EMA_SHORT = "EMA 12-day"  # role: ema_short
EMA_LONG = "EMA 26-day"  # role: ema_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# A commodity (crude oil) trading in a range for months, then breaking out upward late in the period.
rng = np.random.default_rng(7)
n_days = 150
n_range = 105
noise = rng.normal(0, 0.9, n_days)
level = np.empty(n_days)
level[0] = 78.0
for t in range(1, n_days):
    pull = 0.12 * (78.0 - level[t - 1]) if t < n_range else 0.0
    drift = 0.0 if t < n_range else 0.55
    level[t] = level[t - 1] + pull + drift + noise[t]
close_series = pd.Series(level)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-02", periods=n_days, freq="B"),
        CLOSE: close_series.round(2),
        EMA_SHORT: close_series.ewm(span=SHORT_SPAN, adjust=False).mean().round(2),
        EMA_LONG: close_series.ewm(span=LONG_SPAN, adjust=False).mean().round(2),
    }
)

# Plot
gap = df[EMA_SHORT] - df[EMA_LONG]
crossed = (gap * gap.shift(1)) < 0
crossovers = df[CLOSE].where(crossed).tolist()
crossovers = [None if pd.isna(v) else float(v) for v in crossovers]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], IMPRINT_PALETTE[3], IMPRINT_PALETTE[4]),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=6,
    opacity=1.0,
    opacity_hover=1.0,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="indicator-ema · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=CLOSE,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    stroke_style={"width": 6},
    truncate_label=-1,
    x_label_rotation=0,
    show_minor_x_labels=False,
    range=(float(np.floor(df[[CLOSE, EMA_SHORT, EMA_LONG]].min().min() / 5) * 5), None),
)

dates = df[DATE].dt.strftime("%b %d")
chart.x_labels = dates.tolist()
chart.x_labels_major = dates.iloc[::LABEL_EVERY].tolist()

chart.add("Close price", df[CLOSE].tolist(), stroke_style={"width": 6})
chart.add(EMA_SHORT, df[EMA_SHORT].tolist(), stroke_style={"width": 4, "dasharray": "14,8"})
chart.add(EMA_LONG, df[EMA_LONG].tolist(), stroke_style={"width": 4})
chart.add("EMA crossover", crossovers, show_dots=True, stroke=False, dots_size=9)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
