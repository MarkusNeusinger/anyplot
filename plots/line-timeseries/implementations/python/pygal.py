""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: pygal 3.1.3 | Python 3.14.8
Quality: 80/100 | Updated: 2026-10-28
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-timeseries · pygal · anyplot.ai",
    x_title=DATE,
    y_title=PRICE,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=45,
    show_legend=False,
    show_dots=False,
)

chart.add(PRICE, df[PRICE].tolist())

# Label only the first day of each month; the other days stay blank
is_month_start = df[DATE].dt.day == 1
month_labels = df[DATE].dt.strftime("%b %Y").where(is_month_start, "").tolist()
chart.x_labels = month_labels
chart.x_labels_major = [label for label in month_labels if label]

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
