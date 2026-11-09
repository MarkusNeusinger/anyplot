"""anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
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

# Imprint palette: green for up bars, red (position 5) for down bars
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Constants
TICK_WIDTH = 0.3  # open/close tick length as a share of the spacing between bars

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close
PRICE_LABEL = "Price ($)"

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(77)
n_days = 45
start_price = 185.0
daily_returns = 0.0005 + np.random.normal(0, 0.018, n_days)
closes = start_price * np.cumprod(1 + daily_returns)
opens = np.roll(closes, 1)
opens[0] = start_price
daily_volatility = np.abs(np.random.normal(0.012, 0.006, n_days))
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-07-01", periods=n_days, freq="B"),
        OPEN: opens,
        HIGH: np.maximum(opens, closes) * (1 + daily_volatility),
        LOW: np.minimum(opens, closes) * (1 - daily_volatility),
        CLOSE: closes,
    }
)

# Plot: reads only df and the constants above
dates = pd.to_datetime(df[DATE])
label_every = max(1, len(df) // 9)
date_labels = [{"label": dates.iloc[i].strftime("%b %d"), "value": i} for i in range(0, len(df), label_every)]
x_title = f"{DATE} ({dates.min():%b %Y} – {dates.max():%b %Y})"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    opacity=".95",
    opacity_hover=".85",
    colors=(UP_COLOR, DOWN_COLOR),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="ohlc-bar · python · pygal · anyplot.ai",
    x_title=x_title,
    y_title=PRICE_LABEL,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    truncate_legend=-1,
    stroke=True,
    allow_interruptions=True,
    show_dots=False,
    margin_bottom=40,
    x_labels=date_labels,
    x_labels_major_every=1,
)

# Each bar: vertical line (low to high), open tick to the left, close tick to the right
up_bars = []
down_bars = []
for i, (o, h, lo, c) in enumerate(df[[OPEN, HIGH, LOW, CLOSE]].itertuples(index=False, name=None)):
    x = float(i)
    bar_points = [
        (x, lo),
        (x, h),
        (None, None),
        (x - TICK_WIDTH, o),
        (x, o),
        (None, None),
        (x, c),
        (x + TICK_WIDTH, c),
        (None, None),
    ]
    if c >= o:
        up_bars.extend(bar_points)
    else:
        down_bars.extend(bar_points)

chart.add("Bullish (Close ≥ Open)", up_bars)
chart.add("Bearish (Close < Open)", down_bars)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
