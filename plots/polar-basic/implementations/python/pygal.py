""" anyplot.ai
polar-basic: Basic Polar Chart
Library: pygal 3.1.3 | Python 3.13.14
Quality: 88/100 | Updated: 2026-07-24
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

# Imprint palette — first series always brand green
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — hourly temperature readings over a 24-hour cycle
np.random.seed(42)
hours = np.arange(24)
base_temp = 15 + 8 * np.sin((hours - 6) * np.pi / 12)  # peak at noon
temperature = base_temp + np.random.randn(24) * 1.5
peak_idx = int(np.argmax(temperature))

# Angular labels at standard cardinal intervals (00:00, 06:00, 12:00, 18:00),
# plus a callout on the peak hour to emphasize the diurnal cycle's high point
# — dense per-hour labels would crowd a circular axis, so every other point
# stays unlabeled.
cardinal_hours = {0, 6, 12, 18}


def _hour_label(h):
    if h == peak_idx:
        return f"{h:02d}:00 (peak)"
    if h in cardinal_hours:
        return f"{h:02d}:00"
    return ""


hour_labels = [_hour_label(h) for h in hours]

# Style — canonical pygal sizing for the 2400x2400 canvas (native-pixel family)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
)

# Plot — radar chart for cyclical polar data
chart = pygal.Radar(
    style=custom_style,
    width=2400,
    height=2400,
    title="Hourly Temperature (°C) · polar-basic · python · pygal · anyplot.ai",
    show_legend=False,
    fill=True,
    dots_size=9,
    show_y_guides=True,
    inner_radius=0.1,
    margin_top=140,
)

chart.x_labels = hour_labels
chart.add("Temperature (°C)", [float(t) for t in temperature])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
