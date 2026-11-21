""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SMOOTHING_FRAC = 0.3  # LOWESS bandwidth: share of the points in each local fit (spec: 0.3-0.5)

# Columns: set these to your table's column names
DISCHARGE_TIME = "Discharge time (h)"  # role: x
CELL_VOLTAGE = "Cell voltage (V)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("battery.csv")
# Li-ion cell discharged at constant current: quick initial sag, long plateau, steep end-of-discharge knee
rng = np.random.default_rng(42)
hours = np.sort(rng.uniform(0, 10, 220))
trend = 4.1 - 0.07 * hours - 0.25 * np.exp(-hours / 0.35) - 1.3 * np.exp((hours - 10) / 0.8)
volts = trend + rng.normal(0, 0.03 + 0.012 * hours, hours.size)
df = pd.DataFrame({DISCHARGE_TIME: hours, CELL_VOLTAGE: volts})

# Plot
smooth = lowess(df[CELL_VOLTAGE], df[DISCHARGE_TIME], frac=SMOOTHING_FRAC, return_sorted=True)

title = "LOWESS Smoothing of Battery Discharge · scatter-regression-lowess · python · pygal · anyplot.ai"
title_font_size = round(66 * 67 / len(title)) if len(title) > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=max(title_font_size, 44),
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=9,
    opacity=0.7,
    opacity_hover=0.9,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=DISCHARGE_TIME,
    y_title=CELL_VOLTAGE,
    show_dots=True,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
)

# Observations: translucent points at their exact values
chart.add("Measured voltage", list(zip(df[DISCHARGE_TIME], df[CELL_VOLTAGE], strict=True)), stroke=False, dots_size=9)

# LOWESS curve: solid line spanning the full x range, no markers
chart.add(
    f"LOWESS fit (frac = {SMOOTHING_FRAC})",
    list(zip(smooth[:, 0], smooth[:, 1], strict=True)),
    stroke=True,
    show_dots=False,
    stroke_style={"width": 9},
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
