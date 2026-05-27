"""anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: pygal | Python 3.13
Quality: pending | Updated: 2026-05-27
"""

import io
import os
import sys


# Remove current directory from sys.path to prevent self-import conflict
# (this file is named pygal.py, same as the library package)
_cwd = os.path.abspath(".")
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _cwd]

import numpy as np
import pandas as pd
import pygal
from PIL import Image
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — daily sensor readings over 3 years (1095 points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")
trend = np.linspace(50, 80, 1095)
seasonal = 15 * np.sin(2 * np.pi * np.arange(1095) / 365)
noise = np.random.normal(0, 5, 1095)
values = trend + seasonal + noise

# Navigator selection: Feb 2023 – Aug 2023
selection_start, selection_end = 400, 600
start_label = dates[selection_start].strftime("%b %Y")
end_label = dates[selection_end - 1].strftime("%b %Y")
detail_label = f"{start_label} – {end_label}"

TITLE = "line-navigator · python · pygal · anyplot.ai"

# Main chart: 3200 × 1530 px (85 % of 1800)
main_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

main_chart = pygal.Line(
    width=3200,
    height=1530,
    style=main_style,
    title=TITLE,
    x_title="Date",
    y_title="Sensor Reading (mV)",
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    truncate_legend=-1,
    x_label_rotation=45,
    truncate_label=-1,
    show_dots=False,
    fill=False,
    stroke_style={"width": 3},
    interpolate="cubic",
    margin=80,
)

selected_values = list(values[selection_start:selection_end])
n_sel = selection_end - selection_start  # 200
selected_dates = [dates[i].strftime("%b %d") for i in range(selection_start, selection_end)]
step = max(1, n_sel // 6)  # ~33 → ~6 evenly-spaced labels
main_x_labels = [selected_dates[i] if i % step == 0 else "" for i in range(n_sel)]
main_chart.x_labels = main_x_labels
main_chart.add(detail_label, selected_values)

# Navigator: 3200 × 270 px (15 % of 1800; ~17.6 % of main height)
nav_style = Style(
    background=ELEVATED_BG,
    plot_background=ELEVATED_BG,
    foreground=INK_SOFT,
    foreground_strong=INK_SOFT,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=40,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=30,
    value_font_size=22,
    stroke_width=2,
    opacity=".6",
)

nav_chart = pygal.Line(
    width=3200,
    height=270,
    style=nav_style,
    title=None,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_y_labels=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=16,
    truncate_legend=-1,
    x_label_rotation=0,
    show_dots=False,
    fill=True,
    stroke_style={"width": 1.5},
    margin=30,
)

nav_x_labels = [dates[i].strftime("%Y") if i % 365 == 0 else "" for i in range(len(dates))]
nav_chart.x_labels = nav_x_labels
nav_chart.add("Full Dataset (2022–2024)", list(values))

selection_series = [None] * len(values)
for i in range(selection_start, selection_end):
    selection_series[i] = values[i]
nav_chart.add(f"Selected: {detail_label}", selection_series)

# Combine into single 3200 × 1800 PNG using PIL
main_png = main_chart.render_to_png()
nav_png = nav_chart.render_to_png()
main_img = Image.open(io.BytesIO(main_png))
nav_img = Image.open(io.BytesIO(nav_png))

# Resize to exact targets in case cairosvg introduces a pixel offset
TARGET_W, TARGET_MAIN_H, TARGET_NAV_H = 3200, 1530, 270
if main_img.size != (TARGET_W, TARGET_MAIN_H):
    main_img = main_img.resize((TARGET_W, TARGET_MAIN_H), Image.LANCZOS)
if nav_img.size != (TARGET_W, TARGET_NAV_H):
    nav_img = nav_img.resize((TARGET_W, TARGET_NAV_H), Image.LANCZOS)

combined = Image.new("RGB", (TARGET_W, TARGET_MAIN_H + TARGET_NAV_H), PAGE_BG)
combined.paste(main_img, (0, 0))
combined.paste(nav_img, (0, TARGET_MAIN_H))
combined.save(f"plot-{THEME}.png")

# HTML output — interactive pygal charts in browser viewport dimensions
main_html_chart = pygal.Line(
    width=1200,
    height=540,
    style=main_style,
    title=TITLE,
    x_title="Date",
    y_title="Sensor Reading (mV)",
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    x_label_rotation=45,
    truncate_label=-1,
    show_dots=False,
    fill=False,
    stroke_style={"width": 3},
    interpolate="cubic",
)
main_html_chart.x_labels = main_x_labels
main_html_chart.add(detail_label, selected_values)

nav_html_chart = pygal.Line(
    width=1200,
    height=150,
    style=nav_style,
    title=None,
    show_legend=True,
    legend_at_bottom=True,
    show_dots=False,
    fill=True,
)
nav_html_chart.x_labels = nav_x_labels
nav_html_chart.add("Full Dataset (2022–2024)", list(values))
nav_html_chart.add(f"Selected: {detail_label}", selection_series)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>line-navigator · python · pygal · anyplot.ai</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: {PAGE_BG}; color: {INK}; }}
        .chart-container {{ max-width: 1200px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="chart-container">
        {main_html_chart.render(is_unicode=True)}
        {nav_html_chart.render(is_unicode=True)}
    </div>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
