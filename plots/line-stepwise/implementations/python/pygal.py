""" anyplot.ai
line-stepwise: Step Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data - Server response time stepping over 24 hours
hours = list(range(0, 25))
response_times = [50]
for i in range(1, 25):
    if i == 8:
        response_times.append(120)
    elif i == 12:
        response_times.append(180)
    elif i == 14:
        response_times.append(100)
    elif i == 18:
        response_times.append(200)
    elif i == 21:
        response_times.append(80)
    elif i == 23:
        response_times.append(40)
    else:
        response_times.append(response_times[-1])

# Create step data by duplicating points for horizontal-then-vertical transitions
step_x_labels = []
step_values = []
for i, (h, v) in enumerate(zip(hours, response_times, strict=True)):
    if i == 0:
        step_x_labels.append(str(h))
        step_values.append(v)
    else:
        step_x_labels.append(str(h))
        step_values.append(response_times[i - 1])
        step_x_labels.append("")
        step_values.append(v)

# Theme-adaptive style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-stepwise · pygal · anyplot.ai",
    x_title="Hour of Day",
    y_title="Response Time (ms)",
    show_dots=False,
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=False,
    truncate_label=-1,
    show_minor_x_labels=True,
    x_label_rotation=0,
)

# X-axis labels
chart.x_labels = step_x_labels

# Add step data
chart.add("Server Response", step_values)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
