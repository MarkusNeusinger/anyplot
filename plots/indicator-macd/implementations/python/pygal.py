"""anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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
FAST_SPAN, SLOW_SPAN, SIGNAL_SPAN = 12, 26, 9  # standard MACD parameters
LABEL_EVERY = 20  # one date label per this many periods

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD (12,26)"  # role: macd
SIGNAL = "Signal (9)"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv")
np.random.seed(42)
n_days = 150
warmup = 50  # periods dropped until the averages are filled
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
price = pd.Series(100 + np.cumsum(np.random.randn(n_days) * 2 + 0.05))
macd_full = price.ewm(span=FAST_SPAN, adjust=False).mean() - price.ewm(span=SLOW_SPAN, adjust=False).mean()
signal_full = macd_full.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame(
    {DATE: dates, MACD: macd_full.values, SIGNAL: signal_full.values, HISTOGRAM: (macd_full - signal_full).values}
).iloc[warmup:]

# Plot: reads only df and the constants above
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    # histogram up (green), histogram down (red), MACD (blue), signal (ochre), zero line
    colors=(IMPRINT_PALETTE[0], IMPRINT_PALETTE[4], IMPRINT_PALETTE[2], IMPRINT_PALETTE[3], INK_MUTED),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="indicator-macd · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title="MACD value",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    legend_at_bottom=True,
    legend_box_size=36,
    margin=40,
    show_dots=False,
    fill=False,
)

chart.x_labels = [d.strftime("%b %d") if i % LABEL_EVERY == 0 else "" for i, d in enumerate(df[DATE])]

hist = df[HISTOGRAM]
chart.add("Histogram (+)", hist.clip(lower=0).tolist(), fill=True, stroke_style={"width": 0})
chart.add("Histogram (−)", hist.clip(upper=0).tolist(), fill=True, stroke_style={"width": 0})
chart.add(MACD, df[MACD].tolist(), stroke_style={"width": 8})
chart.add(SIGNAL, df[SIGNAL].tolist(), stroke_style={"width": 8})
chart.add("Zero", [0] * len(df), stroke_style={"width": 3, "dasharray": "15, 8"})

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
