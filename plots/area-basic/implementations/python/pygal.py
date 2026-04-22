""" pyplots.ai
area-basic: Basic Area Chart
Library: pygal 3.1.0 | Python 3.14.2
Quality: 87/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Daily website visitors over a month (three distinct phases)
# Phase 1 (Days 1-10): Stable baseline with weekend dips
# Phase 2 (Days 11-20): Growth period with increasing trend
# Phase 3 (Days 21-30): Peak plateau with high variability
days = list(range(1, 31))
visitors = [
    1250,
    1380,
    1420,
    1180,
    980,
    890,
    920,  # Week 1: baseline, weekend dip
    1340,
    1520,
    1680,  # Early week 2: recovery
    1590,
    1450,
    1120,
    1080,  # Mid-month dip (weekend)
    1560,
    1720,
    1890,
    2010,
    1850,
    1420,
    1380,  # Growth phase with weekend dip
    1680,
    1920,
    2150,
    2080,
    1950,
    1620,
    1540,  # Peak phase
    1780,
    1920,  # Final uptick
]

# Key data points
peak_idx = visitors.index(max(visitors))
low_idx = visitors.index(min(visitors))

# Trend line (simple linear fit using endpoint averages)
n = len(visitors)
first_half_avg = sum(visitors[: n // 2]) / (n // 2)
second_half_avg = sum(visitors[n // 2 :]) / (n // 2)
slope = (second_half_avg - first_half_avg) / (n // 2)
trend_start = first_half_avg - slope * (n // 4)
trend = [trend_start + slope * i for i in range(n)]

# Custom style for 4800x2700 canvas — refined typography and subtle chrome
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#c45a00", "#7b2d8e", "#0e7c6b"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    value_font_size=32,
    legend_font_size=34,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.40,
    opacity_hover=0.55,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,3",
    major_guide_stroke_color="#cccccc",
    major_guide_stroke_dasharray="6,3",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=28,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Create area chart — cubic interpolation for smooth curves (distinctive pygal feature)
chart = pygal.Line(
    width=4800,
    height=2700,
    title="Daily Website Visitors \u00b7 area-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Day of Month",
    y_title="Number of Visitors (count)",
    style=custom_style,
    fill=True,
    show_dots=True,
    dots_size=10,
    stroke_style={"width": 5},
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    value_formatter=lambda x: f"{x:,.0f}",
    x_value_formatter=lambda x: f"Day {x}",
    interpolate="cubic",
    interpolation_precision=250,
    min_scale=4,
    max_scale=8,
    margin_bottom=120,
    margin_left=80,
    margin_right=40,
    margin_top=60,
    spacing=12,
    show_minor_x_labels=True,
    show_minor_y_labels=True,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    show_only_major_dots=False,
)

# Main area series with smooth cubic interpolation
chart.add("Daily Visitors", visitors, fill=True, stroke_style={"width": 5})

# Trend line (dashed, no fill) with contrasting dark orange color
chart.add(
    f"Trend (+{slope:.0f} visitors/day)",
    [round(t) for t in trend],
    fill=False,
    show_dots=False,
    stroke_style={"width": 4, "dasharray": "20, 12"},
)

# Peak marker (dark purple - colorblind-safe)
peak_series = [None] * n
peak_series[peak_idx] = {
    "value": visitors[peak_idx],
    "label": f"Peak: {visitors[peak_idx]:,} visitors (Day {peak_idx + 1})",
}
chart.add(f"Peak: {visitors[peak_idx]:,}", peak_series, fill=False, show_dots=True, dots_size=22, stroke=False)

# Low marker (teal - colorblind-safe)
low_series = [None] * n
low_series[low_idx] = {"value": visitors[low_idx], "label": f"Low: {visitors[low_idx]:,} visitors (Day {low_idx + 1})"}
chart.add(f"Low: {visitors[low_idx]:,}", low_series, fill=False, show_dots=True, dots_size=22, stroke=False)

# X-axis labels — major every 5th day for clean spacing
chart.x_labels = [str(d) if d % 5 == 0 or d == 1 else "" for d in days]

# Save outputs (SVG-native format + PNG via cairosvg)
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
