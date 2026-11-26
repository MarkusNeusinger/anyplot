"""anyplot.ai
area-basic: Basic Area Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os
import sys


# Script is named pygal.py — remove its directory from sys.path first so
# 'import pygal' resolves to the installed package, not this file.
sys.path = [p for p in sys.path if p != os.path.dirname(os.path.abspath(__file__))]

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DAY = "Day of month"  # role: x
VISITORS = "Visitors (per day)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("visitors.csv")
df = pd.DataFrame(
    {
        DAY: list(range(1, 31)),
        VISITORS: [
            # Week 1: baseline, weekend dip
            1250, 1380, 1420, 1180, 980, 890, 920,
            # Week 2: recovery, mid-month dip
            1340, 1520, 1680, 1590, 1450, 1120, 1080,
            # Week 3: growth phase
            1560, 1720, 1890, 2010, 1850, 1420, 1380,
            # Week 4: peak plateau
            1680, 1920, 2150, 2080, 1950, 1620, 1540,
            # Final uptick
            1780, 1920,
        ],
    }
)  # fmt: skip

# Plot
title = "Daily Website Visitors · area-basic · python · pygal · anyplot.ai"
title_font_size = round(66 * 67 / len(title)) if len(title) > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=5,
    opacity=0.4,
    opacity_hover=0.55,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="3,3",
    major_guide_stroke_color=INK_MUTED,
    major_guide_stroke_dasharray="3,3",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_border_radius=8,
)

top = df[VISITORS].max()

# Straight segments between the values (no smoothing); fill=True shades down to the zero baseline
chart = pygal.Line(
    width=3200,
    height=1800,
    title=title,
    x_title=DAY,
    y_title=VISITORS,
    style=custom_style,
    fill=True,
    show_dots=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    show_legend=False,
    range=(0, top * 1.1),
    value_formatter=lambda v: f"{v:,.0f}",
    margin_bottom=60,
    margin_left=80,
    margin_right=60,
    margin_top=60,
    spacing=10,
    tooltip_fancy_mode=True,
)

chart.x_labels = [str(d) if d % 5 == 0 or d == df[DAY].iloc[0] else "" for d in df[DAY]]
chart.x_labels_major = [str(d) for d in df[DAY] if d % 5 == 0]
chart.add(VISITORS, df[VISITORS].tolist())

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
