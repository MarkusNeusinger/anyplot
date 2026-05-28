""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-08
"""

import os
import sys


# Remove current directory from path to avoid collision with this filename
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Titanic passenger survival by passenger class
class_names = ["1st Class", "2nd Class", "3rd Class"]
survived_counts = [200, 119, 181]
not_survived_counts = [123, 158, 528]
class_totals = [s + n for s, n in zip(survived_counts, not_survived_counts, strict=True)]
grand_total = sum(class_totals)

# Bar widths proportional to marginal (class) frequencies
widths = [t / grand_total for t in class_totals]
x_ranges = []
cumulative = 0.0
for w in widths:
    x_ranges.append((cumulative, cumulative + w))
    cumulative += w

# Conditional proportions within each bar (spine plot segments)
survive_props = [s / t for s, t in zip(survived_counts, class_totals, strict=True)]
not_survive_props = [1.0 - sp for sp in survive_props]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=18,
    value_font_size=16,
)

chart = pygal.Histogram(
    style=custom_style,
    width=4800,
    height=2700,
    title="Titanic Survival by Passenger Class · bar-spine · pygal · anyplot.ai",
    y_title="Survival Rate",
    show_legend=True,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
)

# Spine plot using overlapping Histogram bars:
# Series 1 "Survived" (green #009E73): full-height background bar (value=1.0)
# Series 2 "Not Survived" (orange #C475FD): overlay bar from y=0 to not_survive_prop
# → orange covers the bottom portion; green is visible at top (survive_prop)
survived_data = [
    {"value": (1.0, x_min, x_max), "label": f"{cls} — {sp:.1%} survived"}
    for cls, sp, (x_min, x_max) in zip(class_names, survive_props, x_ranges, strict=True)
]
not_survived_data = [
    {"value": (nsp, x_min, x_max), "label": f"{cls} — {nsp:.1%} not survived"}
    for cls, nsp, (x_min, x_max) in zip(class_names, not_survive_props, x_ranges, strict=True)
]

chart.add("Survived", survived_data)
chart.add("Not Survived", not_survived_data)

# Y-axis in percentage format
chart.y_labels = [
    {"label": "0%", "value": 0},
    {"label": "25%", "value": 0.25},
    {"label": "50%", "value": 0.50},
    {"label": "75%", "value": 0.75},
    {"label": "100%", "value": 1.0},
]

# X-axis labels centered under each variable-width bar (spec requirement)
chart.x_labels = [
    {"label": f"{cls} ({w:.1%})", "value": (x_min + x_max) / 2}
    for cls, w, (x_min, x_max) in zip(class_names, widths, x_ranges, strict=True)
]

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
