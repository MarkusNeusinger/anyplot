""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: pygal 3.1.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-25
"""

import os
import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with the pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — quarterly sales performance against an annual target
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Semantic threshold colors using Okabe-Ito hues (bad → warn → good)
ZONE_COLORS = ("#D55E00", "#E69F00", "#009E73")

if value < thresholds[0]:
    zone_label = "Poor"
elif value < thresholds[1]:
    zone_label = "Fair"
else:
    zone_label = "Good"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ZONE_COLORS,
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=56,
    tooltip_font_size=40,
)

chart = pygal.Pie(
    width=4800,
    height=2700,
    title=f"Sales: {value}/{max_value} ({zone_label}) · gauge-basic · pygal · anyplot.ai",
    style=custom_style,
    half_pie=True,
    inner_radius=0.55,
    show_legend=True,
    legend_at_bottom=True,
    print_values=False,
    margin=80,
)

# Threshold zones render as colored arcs of the semi-circular gauge
chart.add(f"Poor ({min_value}–{thresholds[0]})", thresholds[0] - min_value)
chart.add(f"Fair ({thresholds[0]}–{thresholds[1]})", thresholds[1] - thresholds[0])
chart.add(f"Good ({thresholds[1]}–{max_value}) — current: {value}", max_value - thresholds[1])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
