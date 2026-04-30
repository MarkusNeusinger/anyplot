"""anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: pygal | Python 3.13
Quality: pending | Created: 2026-04-30
"""

import os
import sys

import numpy as np


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Stock prices with highlighted events
np.random.seed(42)
dates = np.arange(2006, 2016, 0.1)
price = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
recession_mask = (dates >= 2008) & (dates < 2010)
price[recession_mask] -= np.linspace(0, 30, recession_mask.sum())
price[dates >= 2010] -= 30
price = price + np.abs(price.min()) + 50

y_min = 40.0
y_max = float(price.max()) + 20

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    opacity=".25",
    opacity_hover=".4",
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Plot
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="span-basic · pygal · anyplot.ai",
    x_title="Year",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(y_min, y_max),
    xrange=(2005.5, 2016.5),
    fill=True,
    stroke=True,
    dots_size=0,
)

# Vertical span: Recession Period (2008-2009) — closed polygon
recession_span = [(2008, y_min), (2008, y_max), (2009, y_max), (2009, y_min), (2008, y_min)]
chart.add("Recession Period", recession_span)

# Horizontal span: Risk Zone (price 60–80) — closed polygon
risk_span = [(2005.5, 60), (2005.5, 80), (2016.5, 80), (2016.5, 60), (2005.5, 60)]
chart.add("Risk Zone", risk_span)

# Main line (no fill, stroke only)
main_data = [(float(x), float(y)) for x, y in zip(dates, price, strict=True)]
chart.add("Stock Price", main_data, fill=False, stroke=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
