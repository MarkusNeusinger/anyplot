""" anyplot.ai
line-stepwise: Step Line Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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

# Imprint palette: first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONSUMPTION = "Monthly consumption (kWh)"  # role: x
PRICE = "Energy price (ct/kWh)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("tariff.csv")
# Tiered electricity tariff: the unit price jumps when consumption crosses a tier limit
tier_limits = [0, 100, 250, 450, 700]
tier_prices = [18.0, 24.5, 31.0, 38.5, 46.0]
consumption = np.arange(0, 1001, 25)
tier_index = np.searchsorted(tier_limits, consumption, side="right") - 1
df = pd.DataFrame({CONSUMPTION: consumption, PRICE: np.array(tier_prices)[tier_index]})

# Plot: post-aligned steps, each price is held from its own x until the next row
valid = df.dropna(subset=[CONSUMPTION, PRICE])  # a missing value draws no mark
x = valid[CONSUMPTION].astype(float).tolist()
y = valid[PRICE].astype(float).tolist()
points = [(x[0], y[0])]
for i in range(1, len(x)):
    points.append((x[i], y[i - 1]))  # hold the previous value up to this x
    if y[i] != y[i - 1]:
        points.append((x[i], y[i]))  # vertical jump at the data x

x_ticks = np.linspace(min(x), max(x), 6).tolist()
top = max(y)

title = "Tiered Electricity Tariff · line-stepwise · python · pygal · anyplot.ai"
title_font_size = round(66 * min(1.0, 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=CONSUMPTION,
    y_title=PRICE,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=False,
    x_labels=x_ticks,
    x_labels_major_every=1,
    show_minor_x_labels=True,
    x_label_rotation=0,
    range=(0, top * 1.15),
    xrange=(min(x), max(x)),
    value_formatter=lambda v: f"{v:g}",
    x_value_formatter=lambda v: f"{v:g}",
)
chart.add("Unit price", points)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
