""" anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-06-14
"""

import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Zone colors — semantic mapping to Imprint palette
# Z1 recovery→grey(muted), Z2 endurance→blue, Z3 aerobic→green(brand),
# Z4 threshold→ochre, Z5 maximum→matte-red
ZONE_COLORS = (
    INK_MUTED,  # Z1 Recovery
    "#4467A3",  # Z2 Endurance
    "#009E73",  # Z3 Aerobic (Imprint brand green)
    "#BD8233",  # Z4 Threshold
    "#AE3030",  # Z5 Maximum
)

# Data: 90-minute polarized endurance cycling session
zone_names = ["Z1 Recovery", "Z2 Endurance", "Z3 Aerobic", "Z4 Threshold", "Z5 Maximum"]
hr_ranges = ["< 120 bpm", "120–141 bpm", "141–157 bpm", "157–170 bpm", "> 170 bpm"]
minutes = [12, 45, 20, 10, 3]
total_min = sum(minutes)

# X-axis labels combining zone name and HR range
x_labels = [f"{zone_names[i]}  {hr_ranges[i]}" for i in range(5)]

# Title with length-aware font size
title = "Heart Rate Zones · bar-heart-rate-zones · python · pygal · anyplot.ai"
n = len(title)
title_font_size = round(66 * (67 / n)) if n > 67 else 66

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ZONE_COLORS,
    title_font_size=title_font_size,
    label_font_size=40,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    stroke_width=2.5,
)

# Chart — total session duration embedded in y_title for storytelling context
chart = pygal.Bar(
    width=3200,
    height=1800,
    title=title,
    y_title=f"Time (minutes)  ·  {total_min} min total",
    style=custom_style,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    x_label_rotation=45,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{int(x)} min",
    rounded_bars=10,
    margin_bottom=100,
)

chart.x_labels = x_labels

# Single series with per-bar color dicts — each zone gets its Imprint-mapped color
chart.add("Time (min)", [{"value": minutes[i], "color": ZONE_COLORS[i]} for i in range(5)])

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
