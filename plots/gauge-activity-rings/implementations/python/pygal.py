"""anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-14
"""

import os
import sys


# Remove script's own directory from sys.path so `import pygal` finds the
# installed package, not this file (which is also named pygal.py).
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first 3 positions used for the 3 activity rings
IMPRINT_PALETTE = (
    "#009E73",  # Move — brand green (always first series)
    "#C475FD",  # Exercise — lavender
    "#4467A3",  # Stand — blue
    "#BD8233",
    "#AE3030",
    "#2ABCCD",
    "#954477",
    "#99B314",
)

# Daily fitness goals: canonical 3-ring example from the spec
metrics = ["Move", "Exercise", "Stand"]
values = [420, 25, 9]
goals = [600, 30, 12]
units = ["kcal", "min", "hr"]
percentages = [min(v / g * 100, 100) for v, g in zip(values, goals, strict=False)]

# Title with descriptive prefix; font scaled because it exceeds the 67-char baseline
title_str = "Daily Fitness Goals · gauge-activity-rings · python · pygal · anyplot.ai"
n = len(title_str)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(44, round(66 * ratio))

# Style — all Imprint tokens live here for pygal
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fontsize,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    stroke_width=3.0,
)

# Square canvas; full-circle concentric solid gauge — activity rings style
chart = pygal.SolidGauge(
    style=custom_style,
    width=2400,
    height=2400,
    inner_radius=0.40,
    half_pie=False,
    title=title_str,
    legend_at_bottom=True,
    value_formatter=lambda x: f"{x:.0f}%",
)

# Add rings from outermost (Move) to innermost (Stand)
for metric, pct, value, goal, unit in zip(metrics, percentages, values, goals, units, strict=False):
    chart.add(f"{metric}  {value}/{goal} {unit}", [{"value": round(pct, 1), "max_value": 100}])

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
