""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os
import random
from datetime import datetime, timedelta

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Stock Price (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
random.seed(42)
price = 150.0
prices = []
for _ in range(365):
    price = max(100, price + random.gauss(0.1, 2.5))
    prices.append(round(price, 2))
df = pd.DataFrame({DATE: [datetime(2024, 1, 1) + timedelta(days=i) for i in range(365)], PRICE: prices})

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT_PALETTE,
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

# A true date axis: each point sits at its own timestamp, labels and guides at calendar month starts
series = df.dropna(subset=[DATE]).sort_values(DATE)
month_starts = pd.date_range(series[DATE].min(), series[DATE].max(), freq="MS")
span_days = (series[DATE].max() - series[DATE].min()).days
date_format = "%b %d" if span_days <= 62 else "%b %Y" if span_days <= 3 * 365 else "%Y"

chart = pygal.DateTimeLine(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-timeseries · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=PRICE,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=30,
    spacing=24,
    show_legend=False,
    show_dots=False,
    allow_interruptions=True,
    x_value_formatter=lambda moment: moment.strftime(date_format),
)
chart.x_labels = month_starts.to_pydatetime().tolist()
chart.add(PRICE, list(zip(series[DATE].dt.to_pydatetime(), series[PRICE].tolist(), strict=True)))

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
