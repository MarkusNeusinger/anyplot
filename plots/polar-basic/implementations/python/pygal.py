""" anyplot.ai
polar-basic: Basic Polar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-30
"""

import importlib
import os
import sys

import numpy as np


# Remove script dir so 'pygal' resolves to the installed package, not this file
_d = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _d]
os.chdir(_d)

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — Hourly temperature readings over a 24-hour cycle
np.random.seed(42)
hours = np.arange(24)
base_temp = 15 + 8 * np.sin((hours - 6) * np.pi / 12)  # Peak at noon
temperature = base_temp + np.random.randn(24) * 1.5

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=4,
)

# Plot — Radar chart for polar/cyclic data
chart = pygal.Radar(
    style=custom_style,
    width=3600,
    height=3600,
    title="Hourly Temperature (°C) · polar-basic · pygal · anyplot.ai",
    show_legend=False,
    fill=True,
    dots_size=8,
    stroke_style={"width": 5},
    show_y_guides=True,
    inner_radius=0.1,
)

chart.x_labels = [f"{h:02d}:00" for h in hours]
chart.add("Temperature (°C)", [float(t) for t in temperature])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
