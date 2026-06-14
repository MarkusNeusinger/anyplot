"""anyplot.ai
burndown-sprint: Agile Sprint Burndown Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import os
import sys


# Remove script directory from sys.path to avoid self-import (file is named pygal.py)
_here = os.path.dirname(os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)

import pygal
from pygal.style import Style


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
ANYPLOT_NEUTRAL = INK  # semantic anchor — reference lines / baseline (theme-adaptive)

# Title (45 chars < 67-char baseline — no scaling needed)
title = "burndown-sprint · python · pygal · anyplot.ai"
title_font_size = 66

# Data — 2-week sprint: 10 working days + Sat/Sun
# Starting scope: 40 story points
# Wed of week 1 (Wed*): +8 scope change — completed 6 pts but added 8 → net uptick
x_labels = ["Start", "Mon", "Tue", "Wed*", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]

# Ideal burndown: 4 pts/working day from 40 → 0; flat on Sat and Sun
ideal = [40, 36, 32, 28, 24, 20, 20, 20, 16, 12, 8, 4, 0]

# Actual remaining: scope change on Wed* pushes line above ideal mid-sprint
# (30 pts remaining → −6 completed + 8 added → 32 at end of Wed*)
actual = [40, 36, 30, 32, 27, 22, 22, 22, 16, 10, 5, 2, 0]

# Pygal style — actual in Imprint green (pos 1), ideal in theme-adaptive neutral
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], ANYPLOT_NEUTRAL),
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
)

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Sprint Day  (* Wed = scope +8 pts  |  Sat–Sun = weekend)",
    y_title="Remaining Story Points",
    show_x_guides=False,
    show_y_guides=True,
    show_dots=True,
    dots_size=8,
    stroke=True,
    x_label_rotation=0,
)

chart.x_labels = x_labels

# Actual burndown — Imprint green (#009E73), heavier stroke
chart.add("Actual", actual, stroke_style={"width": 5})

# Ideal burndown — neutral reference line, dashed
chart.add("Ideal", ideal, stroke_style={"width": 3, "dasharray": "8, 6"})

# Save PNG and interactive HTML (pygal is interactive)
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
