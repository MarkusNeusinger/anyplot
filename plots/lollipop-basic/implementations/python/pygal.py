""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: pygal 3.1.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-26
"""

import os
import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1
OKABE_ITO = (BRAND, "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — Product sales by category (sorted descending)
categories = ["Smartphones", "Laptops", "Tablets", "Headphones", "Smartwatches", "Cameras", "Speakers", "Gaming"]
values = [892, 654, 478, 312, 287, 198, 156, 134]

sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1], reverse=True)
categories = [item[0] for item in sorted_data]
values = [item[1] for item in sorted_data]

# Style — theme-adaptive chrome, brand-green data
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,) * len(categories),
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    value_label_font_size=36,
    stroke_width=8,
    opacity=1,
    opacity_hover=0.9,
)

# Plot — horizontal lollipop via XY: stem from x=0 to value, baseline node hidden
n = len(categories)
chart = pygal.XY(
    width=4800,
    height=2700,
    title="lollipop-basic · pygal · anyplot.ai",
    x_title="Sales (units)",
    y_title="Product Category",
    style=custom_style,
    show_legend=False,
    dots_size=28,
    stroke=True,
    show_x_guides=True,
    show_y_guides=False,
    margin=120,
    xrange=(0, max(values) * 1.1),
    range=(0.5, n + 0.5),
    y_labels=[{"label": cat, "value": n - i} for i, cat in enumerate(categories)],
)

for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    y_pos = n - i
    chart.add(cat, [{"value": (0, y_pos), "node": {"r": 0}}, {"value": (val, y_pos)}])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
