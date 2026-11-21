"""anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os
import sys

import numpy as np
import pandas as pd


# This directory holds a pygal.py next to the real package: drop it from the import path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 = up candles, position 5 = down candles
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close
VOLUME = "Volume (shares)"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("ohlcv.csv")
np.random.seed(42)
n_periods = 60
close_prices = 100 + np.cumsum(np.random.normal(0.3, 1.5, n_periods))
open_prices = close_prices + np.random.normal(0, 0.4, n_periods)
high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 1.2, n_periods))
low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 1.2, n_periods))
df = pd.DataFrame(
    {
        DATE: pd.bdate_range("2024-01-02", periods=n_periods),
        OPEN: open_prices,
        HIGH: high_prices,
        LOW: low_prices,
        CLOSE: close_prices,
        VOLUME: np.random.uniform(1e6, 4e6, n_periods),
    }
)

# Plot: pygal has one coordinate system, so both panes share one y axis. The price pane takes the
# upper 70 % of its range, the volume pane the lower 25 %, and custom tick labels name each pane.
PRICE_SHARE, VOLUME_SHARE = 0.70, 0.25
x = np.arange(len(df), dtype=float)
is_up = (df[CLOSE] >= df[OPEN]).to_numpy()

price_lo = df[LOW].min() - 1.0
price_hi = df[HIGH].max() + 1.0
total = (price_hi - price_lo) / PRICE_SHARE
y_min = price_hi - total
vol_base = y_min
vol_scale = VOLUME_SHARE * total / df[VOLUME].max()


def segments(xs, y_from, y_to, mask):
    """Vertical line segments (x, y_from)-(x, y_to), None-separated, for the rows in mask."""
    points = []
    for xi, a, b in zip(xs[mask], y_from[mask], y_to[mask], strict=True):
        points += [(float(xi), float(a)), (float(xi), float(b)), (float(xi), None)]
    return points


body_lo = np.minimum(df[OPEN], df[CLOSE]).to_numpy()
body_hi = np.maximum(df[OPEN], df[CLOSE]).to_numpy()
vol_top = vol_base + df[VOLUME].to_numpy() * vol_scale
vol_zero = np.full(len(df), vol_base)

# Axis labels: prices in the upper pane, volumes in the lower pane
price_step = 5 if price_hi - price_lo > 20 else 2
price_ticks = np.arange(np.ceil(price_lo / price_step) * price_step, price_hi, price_step)
vol_step = 10 ** int(np.floor(np.log10(df[VOLUME].max())))
vol_ticks = np.arange(0, df[VOLUME].max() + 1, vol_step)
y_labels = [{"value": float(v * vol_scale + vol_base), "label": f"{v / 1e6:g}M"} for v in vol_ticks] + [
    {"value": float(p), "label": f"{p:g}"} for p in price_ticks
]

date_labels = df[DATE].dt.strftime("%b %d").tolist()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(color for up in is_up for color in [UP_COLOR if up else DOWN_COLOR] * 3),
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=38,
    legend_font_size=40,
    value_font_size=30,
    stroke_width="inherit",
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="2,8",
    opacity=1.0,
    opacity_hover=1.0,
)

# Every candle is three series (wick, body, volume bar); each takes its width from its own group
WIDTHS = (6, 36, 36)

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title="Tesla Stock OHLC with Volume · candlestick-volume · python · pygal · anyplot.ai",
    x_title=f"{DATE}  ·  green: close at or above open, red: close below open",
    y_title="Volume (shares)  ·  Price (USD)",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    range=(float(y_min), float(price_hi)),
    y_labels=y_labels,
    x_labels=[float(i) for i in x[::10]],
    x_value_formatter=lambda i: date_labels[int(round(i))],
    include_x_axis=False,
    dots_size=0,
    margin_top=30,
    margin_bottom=20,
    margin_left=30,
    margin_right=60,
    truncate_legend=-1,
    stroke_style={"linecap": "butt"},
)

# One two-point series per wick, body and volume bar: pygal joins the points of a series, so a
# candle cannot share a series with its neighbours. Colors follow the style's color list in order.
for i in range(len(df)):
    for (lo, hi), width in zip(
        ((df[LOW][i], df[HIGH][i]), (body_lo[i], body_hi[i]), (vol_base, vol_top[i])), WIDTHS, strict=True
    ):
        chart.add("", [(x[i], float(lo)), (x[i], float(hi))], stroke_style={"width": width}, show_dots=False)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
