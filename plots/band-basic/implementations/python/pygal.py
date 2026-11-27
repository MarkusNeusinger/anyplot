"""anyplot.ai
band-basic: Basic Band Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-29
"""

import os
import sys


# Prevent self-import: script named 'pygal.py' would shadow the real package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: band=green (first series), center line=blue for contrast against the band
IMPRINT_PALETTE = ("#009E73", "#4467A3", "#C475FD", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
SMOOTH_WINDOW = 7  # moving-average width that turns the noisy readings into the sensor mean

# Columns: set these to your table's column names
HOURS = "Time (hours)"  # role: x
LOWER = "Lower 95% bound (%)"  # role: y_lower
UPPER = "Upper 95% bound (%)"  # role: y_upper
CENTER = "Soil Moisture (%)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("sensor.csv")
# Soil moisture sensor readings with a 95% confidence interval
np.random.seed(42)
n_points = 80
hours = np.linspace(0, 48, n_points)
base_trend = 38 - 0.3 * hours + 4.0 * np.sin(2 * np.pi * hours / 24) + 8.0 * np.exp(-((hours - 40) ** 2) / 8)
y_raw = base_trend + np.random.randn(n_points) * 0.6
y_smooth = np.convolve(y_raw, np.ones(SMOOTH_WINDOW) / SMOOTH_WINDOW, mode="valid")
pad_left = (n_points - len(y_smooth)) // 2
pad_right = n_points - len(y_smooth) - pad_left
y_center = np.concatenate([np.full(pad_left, y_smooth[0]), y_smooth, np.full(pad_right, y_smooth[-1])])
# Wider during the dry midday, narrower after rain
uncertainty = 1.2 + 0.8 * np.sin(2 * np.pi * hours / 24) ** 2 + 0.04 * hours
df = pd.DataFrame({HOURS: hours, LOWER: y_center - uncertainty, UPPER: y_center + uncertainty, CENTER: y_center})

# Plot
x_vals = df[HOURS].astype(float).tolist()
y_lo = 4 * (int(df[LOWER].min()) // 4)
y_hi = 4 * (int(df[UPPER].max()) // 4 + 1)
y_label_values = list(range(y_lo, y_hi + 1, 4))
x_ticks = list(range(0, int(df[HOURS].max()) + 1, 6))

# Custom style — Imprint palette, theme-adaptive chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    opacity=".25",
    opacity_hover=".40",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    stroke_width=2.5,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_colors=("transparent",),
    tooltip_font_size=32,
    font_family='Helvetica, Arial, "DejaVu Sans", sans-serif',
)

title = "band-basic · python · pygal · anyplot.ai"

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    explicit_size=True,
    title=title,
    x_title=HOURS,
    y_title=CENTER,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    fill=True,
    stroke=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=28,
    truncate_legend=-1,
    x_label_rotation=0,
    range=(y_lo - 1, y_hi + 1),
    y_labels=y_label_values,
    x_labels=x_ticks,
    x_labels_major=x_ticks[::2],
    show_minor_x_labels=True,
    show_minor_y_labels=True,
    print_values=False,
    x_value_formatter=lambda x: f"{x:.0f}h",
    value_formatter=lambda x: f"{x:.1f}%",
    tooltip_border_radius=8,
    margin_top=30,
    margin_bottom=130,
    margin_left=30,
    margin_right=50,
    spacing=18,
)


# Band as closed polygon: upper boundary forward, then lower boundary reversed
upper_pts = list(zip(x_vals, df[UPPER].astype(float).tolist(), strict=True))
lower_pts = list(zip(x_vals, df[LOWER].astype(float).tolist(), strict=True))
chart.add("95% Confidence Band", upper_pts + lower_pts[::-1], stroke_style={"width": 0.01}, show_dots=False)

# Central line on top of the band
chart.add(
    "Sensor Mean",
    list(zip(x_vals, df[CENTER].astype(float).tolist(), strict=True)),
    fill=False,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 10, "linecap": "round", "linejoin": "round"},
)

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
