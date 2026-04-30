""" anyplot.ai
rug-basic: Basic Rug Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-04-30
"""

import os
import sys

import numpy as np


# Pop script directory so local pygal.py doesn't shadow the installed package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - API response times (ms) with realistic multi-modal distribution
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(150, 20, 60),  # Typical fast responses
        np.random.normal(250, 30, 25),  # Medium responses
        np.random.normal(400, 15, 10),  # Slow outlier cluster
        np.random.uniform(50, 100, 5),  # Very fast cache hits
    ]
)
values = np.clip(values, 30, 500)
values = np.sort(values)

# Style - single color so all rug ticks share brand green
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),  # All ticks cycle through brand green only
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=8,
    opacity=0.7,
)

# Plot - XY chart used as rug plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="rug-basic · pygal · anyplot.ai",
    x_title="Response Time (ms)",
    y_title=None,
    show_legend=False,
    show_dots=False,
    stroke=True,
    show_x_guides=False,
    show_y_guides=False,
    show_y_labels=False,
    print_values=False,
    explicit_size=True,
    margin=100,
    margin_top=220,
    margin_bottom=300,
    xrange=(30, 520),
    range=(0, 0.2),
)

# Rug ticks - short vertical marks along the x-axis
tick_bottom = 0.0
tick_top = 0.15

for val in values:
    chart.add(
        f"{val:.1f} ms", [(float(val), tick_bottom), (float(val), tick_top)], stroke_style={"width": 8}, show_dots=False
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
