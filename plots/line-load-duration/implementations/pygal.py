"""pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours = 8760

# Build realistic load profile: base ~400 MW, peak ~1200 MW
base_load = 400
peak_load = 1200
mid_load = (base_load + peak_load) / 2

hour_of_year = np.arange(hours)
day_of_year = hour_of_year / 24.0
hour_of_day = hour_of_year % 24

# Seasonal component (summer peak, winter secondary peak)
seasonal = 150 * np.sin(2 * np.pi * (day_of_year - 45) / 365)
seasonal += 80 * np.sin(4 * np.pi * day_of_year / 365)

# Daily component (daytime peak)
daily = 120 * np.sin(np.pi * (hour_of_day - 6) / 16)
daily[hour_of_day < 6] = -80
daily[hour_of_day > 22] = -60

# Random noise
noise = np.random.normal(0, 40, hours)

# Combine and sort descending for load duration curve
raw_load = mid_load + seasonal + daily + noise
raw_load = np.clip(raw_load, base_load * 0.9, peak_load * 1.05)
load_mw = np.sort(raw_load)[::-1]

# Capacity tiers (base at 550 MW so base region is visually wider)
base_capacity = 550
intermediate_capacity = 900

# Region boundaries
peak_end = int(np.searchsorted(-load_mw, -intermediate_capacity))
base_start = int(np.searchsorted(-load_mw, -base_capacity))

# Total energy consumption
total_energy_twh = np.trapezoid(load_mw) / 1e6

# Downsample for SVG performance (8760 points too heavy)
step = 15
indices = list(range(0, hours, step))
if indices[-1] != hours - 1:
    indices.append(hours - 1)
n_pts = len(indices)

load_sampled = [float(load_mw[i]) for i in indices]

# Build three filled region series
peak_series = [None] * n_pts
inter_series = [None] * n_pts
base_series = [None] * n_pts

for i, idx in enumerate(indices):
    val = load_sampled[i]
    if idx <= peak_end:
        peak_series[i] = val
    elif idx <= base_start:
        inter_series[i] = val
    else:
        base_series[i] = val

# Ensure continuity at boundaries by overlapping one point
for i, idx in enumerate(indices):
    if idx >= peak_end and inter_series[i] is None and peak_series[i] is not None:
        inter_series[i] = load_sampled[i]
        break
for i, idx in enumerate(indices):
    if idx >= base_start and base_series[i] is None and inter_series[i] is not None:
        base_series[i] = load_sampled[i]
        break

# Custom style - 3 region colors + 3 capacity line colors
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e8e8e8",
    colors=("#e74c3c", "#27ae60", "#306998", "#444444", "#7b4173", "#1a1a2e"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=50,
    label_font_size=36,
    major_label_font_size=32,
    value_font_size=28,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=0.55,
    opacity_hover=0.70,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,3",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=26,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
)

# Chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title=(
        f"Load Duration Curve (Total Energy: {total_energy_twh:.1f} TWh)"
        " \u00b7 line-load-duration \u00b7 pygal \u00b7 pyplots.ai"
    ),
    x_title="Hours of Year (ranked by demand)",
    y_title="Power Demand (MW)",
    style=custom_style,
    fill=True,
    show_dots=False,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    value_formatter=lambda x: f"{x:,.0f} MW" if x else "",
    min_scale=4,
    max_scale=8,
    margin_bottom=140,
    margin_left=160,
    margin_right=140,
    margin_top=60,
    range=(0, 1350),
    truncate_label=10,
)

# Add filled region series
chart.add(f"Peak Load (0\u2013{peak_end} hrs)", peak_series, fill=True, stroke_style={"width": 4})
chart.add(f"Intermediate ({peak_end}\u2013{base_start} hrs)", inter_series, fill=True, stroke_style={"width": 4})
chart.add(f"Base Load ({base_start}\u2013{hours} hrs)", base_series, fill=True, stroke_style={"width": 4})

# Capacity tier reference lines (horizontal dashed)
base_line = [base_capacity] * n_pts
inter_line = [intermediate_capacity] * n_pts
peak_line = [1200] * n_pts

chart.add(
    f"Base Capacity ({base_capacity} MW)",
    base_line,
    fill=False,
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "16, 10"},
)
chart.add(
    f"Intermediate Capacity ({intermediate_capacity} MW)",
    inter_line,
    fill=False,
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "16, 10"},
)
chart.add(
    "Peak Capacity (1200 MW)", peak_line, fill=False, show_dots=False, stroke_style={"width": 2, "dasharray": "16, 10"}
)

# X-axis labels at key points
x_labels = []
for idx in indices:
    if idx == 0:
        x_labels.append("0")
    elif idx % 1000 < step:
        x_labels.append(str((idx // 1000) * 1000))
    elif idx == indices[-1]:
        x_labels.append("8760")
    else:
        x_labels.append("")
chart.x_labels = x_labels

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
