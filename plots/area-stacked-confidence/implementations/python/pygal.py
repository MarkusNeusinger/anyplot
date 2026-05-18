""" anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-18
"""

import os
import sys

import numpy as np


sys.path = [p for p in sys.path if p != ""]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

if THEME == "light":
    band_color_a = "#A0E0BB"
    center_color_a = "#009E73"
    band_color_b = "#F0C68A"
    center_color_b = "#D55E00"
    band_color_c = "#7FC4E8"
    center_color_c = "#0072B2"
else:
    band_color_a = "#1FA862"
    center_color_a = "#009E73"
    band_color_b = "#C64500"
    center_color_b = "#D55E00"
    band_color_c = "#0058A3"
    center_color_c = "#0072B2"

np.random.seed(42)
quarters = ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25"]

product_a = np.array([120.0, 125.0, 130.0, 140.0, 145.0, 150.0, 158.0, 165.0])
uncertainty_a = np.array([8.0, 9.0, 8.5, 10.0, 9.5, 11.0, 10.5, 12.0])
a_lower = (product_a - uncertainty_a).tolist()
a_upper = (product_a + uncertainty_a).tolist()
a_center = product_a.tolist()

product_b = np.array([80.0, 85.0, 88.0, 92.0, 95.0, 100.0, 105.0, 110.0])
uncertainty_b = np.array([6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0])
b_lower = (product_b - uncertainty_b).tolist()
b_upper = (product_b + uncertainty_b).tolist()
b_center = product_b.tolist()

product_c = np.array([30.0, 40.0, 55.0, 70.0, 85.0, 95.0, 105.0, 115.0])
uncertainty_c = np.array([12.0, 15.0, 18.0, 20.0, 22.0, 24.0, 25.0, 26.0])
c_lower = (product_c - uncertainty_c).tolist()
c_upper = (product_c + uncertainty_c).tolist()
c_center = product_c.tolist()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(
        band_color_a,
        center_color_a,
        band_color_a,
        band_color_b,
        center_color_b,
        band_color_b,
        band_color_c,
        center_color_c,
        band_color_c,
    ),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

chart = pygal.StackedLine(
    width=4800,
    height=2700,
    style=custom_style,
    title="area-stacked-confidence · Python · pygal · anyplot.ai",
    x_title="Quarter",
    y_title="Revenue ($M)",
    fill=True,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    margin=80,
    spacing=40,
)

chart.x_labels = quarters

chart.add(None, a_lower)
chart.add("Product A (with 90% CI)", a_center)
chart.add(None, a_upper)

chart.add(None, b_lower)
chart.add("Product B (with 90% CI)", b_center)
chart.add(None, b_upper)

chart.add(None, c_lower)
chart.add("Product C (with 90% CI)", c_center)
chart.add(None, c_upper)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
