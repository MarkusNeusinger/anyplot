""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: pygal 3.1.3 | Python 3.13.14
Quality: 81/100 | Updated: 2026-06-30
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data — quarterly sales performance against an annual target (Q3 2024)
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Semantic zone colors: bad → warn → good (Imprint traffic-light anchors)
ZONE_COLORS = ("#AE3030", "#DDCC77", "#009E73")

zone_label = "Poor" if value < thresholds[0] else "Fair" if value < thresholds[1] else "Good"

# Stable descriptive title (does not embed runtime zone/value strings)
_title = "Quarterly Sales Performance · gauge-basic · pygal · anyplot.ai"
# Scale font size down only when title exceeds the 67-char reference length
_title_fs = max(44, round(66 * 67 / max(len(_title), 67)))

# Zone widths for the half-pie arcs (sum = max_value)
_poor_w = thresholds[0] - min_value  # 30
_fair_w = thresholds[1] - thresholds[0]  # 40
_good_w = max_value - thresholds[1]  # 30

# value_formatter: tooltip label shows the zone range in the interactive HTML export
_zone_map = {_poor_w: f"Range 0–{thresholds[0]}", _fair_w: f"Range {thresholds[0]}–{thresholds[1]}"}

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ZONE_COLORS,
    title_font_size=_title_fs,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.Pie(
    width=3200,
    height=1800,
    title=_title,
    style=custom_style,
    half_pie=True,
    inner_radius=0.60,
    show_legend=True,
    legend_at_bottom=True,
    print_values=False,
    margin=60,
    # Rich tooltip labels for the interactive HTML export (LM-02)
    value_formatter=lambda x: f"Span: {int(x)} pts of {max_value}",
)

# Three colored arcs; the "Good" label carries the current value as the status indicator
chart.add(f"Poor  (0–{thresholds[0]})", _poor_w)
chart.add(f"Fair  ({thresholds[0]}–{thresholds[1]})", _fair_w)
chart.add(f"Good  ({thresholds[1]}–{max_value})  ·  current: {value}", _good_w)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
