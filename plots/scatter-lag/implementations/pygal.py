""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-04-12
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic AR(1) process with moderate positive autocorrelation
np.random.seed(42)
n = 400
phi = 0.78
noise = np.random.normal(0, 1.0, n)
temperature = np.zeros(n)
temperature[0] = 20.0
for i in range(1, n):
    temperature[i] = 20.0 + phi * (temperature[i - 1] - 20.0) + noise[i]

lag = 1
y_t = temperature[:-lag]
y_t_lag = temperature[lag:]

# Temporal quartile masks
time_idx = np.arange(len(y_t))
q_bounds = np.percentile(time_idx, [25, 50, 75])

# Build scatter series with interactive tooltips (pygal dict format)
early = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Day {i + 1}"}
    for i in range(len(y_t))
    if time_idx[i] < q_bounds[0]
]
mid_early = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Day {i + 1}"}
    for i in range(len(y_t))
    if q_bounds[0] <= time_idx[i] < q_bounds[1]
]
mid_late = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Day {i + 1}"}
    for i in range(len(y_t))
    if q_bounds[1] <= time_idx[i] < q_bounds[2]
]
late = [
    {"value": (float(y_t[i]), float(y_t_lag[i])), "label": f"Day {i + 1}"}
    for i in range(len(y_t))
    if time_idx[i] >= q_bounds[2]
]

# Correlation coefficient
r = np.corrcoef(y_t, y_t_lag)[0, 1]

# Reference geometry
data_min = float(min(y_t.min(), y_t_lag.min()))
data_max = float(max(y_t.max(), y_t_lag.max()))
pad = (data_max - data_min) * 0.05
ref_start = data_min - pad
ref_end = data_max + pad
ref_line = [(ref_start, ref_start), (ref_end, ref_end)]

# ±1σ envelope around y=x to visualise autocorrelation spread
sigma = float(np.std(y_t_lag - y_t))
upper_env = [(ref_start, ref_start + sigma), (ref_end, ref_end + sigma)]
lower_env = [(ref_start, ref_start - sigma), (ref_end, ref_end - sigma)]

# Warm-to-cool temporal palette: terracotta → amber → teal → navy
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#f8f7f5",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d5d5d3",
    guide_stroke_color="#e0dfdd",
    colors=(
        "#c25a3c",  # Q1 — terracotta
        "#d4a028",  # Q2 — warm amber
        "#2a9d8f",  # Q3 — teal
        "#264653",  # Q4 — deep navy
        "#c0bebb",  # +1σ envelope
        "#c0bebb",  # −1σ envelope
        "#888886",  # y = x reference
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=32,
    legend_font_family=font,
    value_font_size=28,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.60,
    opacity_hover=0.95,
    stroke_opacity=0.7,
    stroke_opacity_hover=1,
)

# Chart — interactivity enabled for SVG hover tooltips
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title=f"Lag Plot (k={lag}, r={r:.2f}) \u00b7 scatter-lag \u00b7 pygal \u00b7 pyplots.ai",
    x_title="y(t)",
    y_title=f"y(t+{lag})",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    stroke=False,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.1f}",
    value_formatter=lambda y: f"{y:.1f}",
    margin_bottom=100,
    margin_left=80,
    margin_right=30,
    margin_top=40,
    range=(ref_start, ref_end),
    xrange=(ref_start, ref_end),
    x_labels_major_count=8,
    y_labels_major_count=8,
    print_values=False,
    print_zeroes=False,
    truncate_legend=40,
)

# Temporal quartile scatter series
chart.add("Days 1\u2013100", early, stroke=False, dots_size=9)
chart.add("Days 101\u2013200", mid_early, stroke=False)
chart.add("Days 201\u2013300", mid_late, stroke=False)
chart.add("Days 301\u2013399", late, stroke=False, dots_size=9)

# ±1σ envelope (no legend entry)
env_style = {"width": 3, "dasharray": "6, 8", "linecap": "round"}
chart.add(None, upper_env, stroke=True, show_dots=False, stroke_style=env_style)
chart.add(None, lower_env, stroke=True, show_dots=False, stroke_style=env_style)

# Diagonal reference line y = x
chart.add(
    "y = x (\u00b11\u03c3)",
    ref_line,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "dasharray": "24, 12", "linecap": "round"},
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
