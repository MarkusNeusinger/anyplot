""" anyplot.ai
line-filled: Filled Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 70/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.25)" if THEME == "light" else "rgba(240,239,232,0.25)"  # top of the 15-25 % band: read through the fill
BRAND = "#009E73"  # Imprint palette position 1, the single series
BRAND_FILL = "rgba(0, 158, 115, 0.35)"  # BRAND at 35 % opacity, for the area under the line

# Columns: set these to your table's column names
MONTH = "Month (2024)"  # role: x
PAGE_VIEWS = "Page views"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
seasonal = np.array([0.8, 0.85, 0.95, 1.0, 1.1, 1.15, 1.2, 1.1, 1.05, 0.95, 0.9, 1.3])  # holiday spike in December
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        PAGE_VIEWS: (50000 * seasonal + np.random.normal(0, 2000, 12)).astype(int),
    }
)

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(BRAND_FILL, BRAND),
    guide_stroke_color=GRID,
    major_guide_stroke_color=GRID,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=36,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=7,
    stroke_width_hover=9,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-filled · python · pygal · anyplot.ai",
    x_title=MONTH,
    y_title=PAGE_VIEWS,
    fill=True,
    include_x_axis=True,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=11,
    spacing=24,
    margin=40,
    value_formatter=lambda views: f"{views:,.0f}",
)

chart.x_labels = df[MONTH].astype(str).tolist()
values = [None if pd.isna(views) else float(views) for views in df[PAGE_VIEWS]]
# pygal fills and strokes one path, so the translucent area and the solid line are two layers of the same values
chart.add(PAGE_VIEWS, values, fill=True, show_dots=False)
chart.add(PAGE_VIEWS, values, fill=False)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
