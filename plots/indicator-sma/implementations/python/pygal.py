"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-19
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
LABEL_EVERY = 30  # one dated x label per this many rows

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# Geometric Brownian motion for a realistic stock price; each SMA is a rolling mean of the close
np.random.seed(42)
dates = pd.date_range("2025-01-02", periods=300, freq="B")
returns = np.random.normal(0.0003, 0.015, len(dates))
prices = 150.0 * np.cumprod(1 + returns)
df = pd.DataFrame({DATE: dates, CLOSE: prices})
df[SMA_SHORT] = df[CLOSE].rolling(window=20).mean()
df[SMA_MEDIUM] = df[CLOSE].rolling(window=50).mean()
df[SMA_LONG] = df[CLOSE].rolling(window=200).mean()

# Plot: pygal takes plain lists built from df; NaN warm-up values become None so each SMA starts where its window is full
x_labels = [d.strftime("%Y-%m-%d") if i % LABEL_EVERY == 0 else "" for i, d in enumerate(df[DATE])]


def to_list(column):
    return [None if pd.isna(v) else float(v) for v in df[column]]


# Tooltip label on the lowest close (visible in the interactive HTML)
min_idx = int(df[CLOSE].idxmin())
close_annotated = [{"value": v, "label": "Lowest close"} if i == min_idx else v for i, v in enumerate(to_list(CLOSE))]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=".9",
    opacity_hover=".95",
)

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="indicator-sma · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title="Price (USD)",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    show_dots=False,
    legend_at_bottom=True,
    legend_box_size=36,
    margin=40,
    spacing=20,
    value_formatter=lambda x: f"${x:.2f}",
)
chart.x_labels = x_labels

# The close is the heavy solid line; the SMAs are thinner and dashed, longer periods with longer dashes
chart.add(CLOSE, close_annotated, stroke_style={"width": 5})
chart.add(SMA_SHORT, to_list(SMA_SHORT), stroke_style={"width": 3, "dasharray": "6, 3"})
chart.add(SMA_MEDIUM, to_list(SMA_MEDIUM), stroke_style={"width": 3, "dasharray": "12, 4"})
chart.add(SMA_LONG, to_list(SMA_LONG), stroke_style={"width": 4, "dasharray": "18, 6"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
