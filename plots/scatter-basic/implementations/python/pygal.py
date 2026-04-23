""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: pygal 3.1.0 | Python 3.14.4
Quality: 87/100 | Created: 2026-04-23
"""

import os
import sys


# Script filename shadows the installed `pygal` package when run as `python pygal.py`;
# dropping the script directory from sys.path lets the real package resolve.
sys.path.pop(0)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#8A8A82" if THEME == "light" else "#6E6D66"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — study hours vs exam scores, moderate positive correlation
np.random.seed(42)
n = 180
study_hours = np.random.uniform(1.5, 13.5, n)
exam_scores = study_hours * 4.8 + np.random.normal(0, 6.5, n) + 26
exam_scores = np.clip(exam_scores, 20, 100)

# Visual hierarchy: split at conventional 70% passing threshold to guide the
# viewer's eye and convey the "hours → outcome" narrative beyond a raw cloud.
PASSING = 70.0
above = [(float(h), float(s)) for h, s in zip(study_hours, exam_scores, strict=True) if s >= PASSING]
below = [(float(h), float(s)) for h, s in zip(study_hours, exam_scores, strict=True) if s < PASSING]

font = "DejaVu Sans, Helvetica, Arial, sans-serif"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK_SOFT,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    font_family=font,
    title_font_family=font,
    label_font_family=font,
    major_label_font_family=font,
    legend_font_family=font,
    tooltip_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    tooltip_font_size=28,
    value_font_size=26,
    opacity=0.7,
    opacity_hover=0.95,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-basic · pygal · anyplot.ai",
    x_title="Study Hours per Week (hrs)",
    y_title="Exam Score (%)",
    stroke=False,
    dots_size=17,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=32,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.0f}",
    value_formatter=lambda v: f"{v:.0f}%",
    range=(15, 100),
    xrange=(1, 14),
    x_labels_major_count=7,
    y_labels_major_count=9,
    margin=60,
    print_values=False,
    js=[],
)

chart.add("Passing (≥ 70%)", above)
chart.add("Below 70%", below)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
