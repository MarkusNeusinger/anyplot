"""pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: pygal | Python 3.13
Quality: pending | Created: 2026-04-12
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

# Color points by time index for temporal structure
time_idx = np.arange(len(y_t))
quartile_bounds = np.percentile(time_idx, [25, 50, 75])
early = [(float(y_t[i]), float(y_t_lag[i])) for i in range(len(y_t)) if time_idx[i] < quartile_bounds[0]]
mid_early = [
    (float(y_t[i]), float(y_t_lag[i]))
    for i in range(len(y_t))
    if quartile_bounds[0] <= time_idx[i] < quartile_bounds[1]
]
mid_late = [
    (float(y_t[i]), float(y_t_lag[i]))
    for i in range(len(y_t))
    if quartile_bounds[1] <= time_idx[i] < quartile_bounds[2]
]
late = [(float(y_t[i]), float(y_t_lag[i])) for i in range(len(y_t)) if time_idx[i] >= quartile_bounds[2]]

# Correlation coefficient
r = np.corrcoef(y_t, y_t_lag)[0, 1]

# Diagonal reference line (y = x)
data_min = float(min(y_t.min(), y_t_lag.min()))
data_max = float(max(y_t.max(), y_t_lag.max()))
margin = (data_max - data_min) * 0.05
ref_start = data_min - margin
ref_end = data_max + margin
ref_line = [(ref_start, ref_start), (ref_end, ref_end)]

# Shared font
font = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Style
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#e0e0e0",
    guide_stroke_color="#e0e0e0",
    colors=("#1a3a5c", "#306998", "#5a9bd5", "#a3ceed", "#888888"),
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
    opacity=0.55,
    opacity_hover=0.90,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Chart
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
    margin_left=60,
    margin_right=40,
    margin_top=50,
    range=(ref_start, ref_end),
    xrange=(ref_start, ref_end),
    x_labels_major_count=8,
    y_labels_major_count=8,
    print_values=False,
    print_zeroes=False,
    js=[],
)

# Add temporal quartile series
chart.add("Days 1\u2013100", early, stroke=False)
chart.add("Days 101\u2013200", mid_early, stroke=False)
chart.add("Days 201\u2013300", mid_late, stroke=False)
chart.add("Days 301\u2013399", late, stroke=False)

# Diagonal reference line
chart.add(
    "y = x",
    ref_line,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "dasharray": "24, 12", "linecap": "round"},
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
