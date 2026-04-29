""" anyplot.ai
radar-basic: Basic Radar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-29
"""

import importlib
import os
import sys


# Prevent this file (pygal.py) from shadowing the installed pygal package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: three employees with distinct competency profiles — technical expert,
# collaborative leader, and creative visionary — to highlight trade-offs.
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]

employee_a = [85, 92, 78, 88, 72, 80]  # Technical Expert: peaks at Technical Skills
employee_b = [80, 68, 92, 82, 88, 74]  # Team Leader: peaks at Teamwork & Leadership
employee_c = [72, 76, 70, 74, 85, 95]  # Creative Visionary: peaks at Creativity & Leadership

# Style — font sizes corrected to pixel-based minimums for 3600px canvas
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,  # axis category labels: minimum 22px
    major_label_font_size=18,  # major labels: minimum 18px
    legend_font_size=18,
    value_font_size=16,  # spoke value labels: minimum 16px
    opacity=0.25,
    opacity_hover=0.6,
)

# Plot
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="radar-basic · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    fill=True,
    dots_size=8,
    stroke_style={"width": 5, "linecap": "round", "linejoin": "round"},
    show_y_guides=True,
    y_labels_major_every=2,
    range=(0, 100),
)

chart.x_labels = categories
chart.add("Employee A — Technical Expert", employee_a)
chart.add("Employee B — Team Leader", employee_b)
chart.add("Employee C — Creative Visionary", employee_c)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
