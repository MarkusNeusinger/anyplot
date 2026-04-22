""" pyplots.ai
campbell-basic: Campbell Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — natural frequencies of a rotor system vs rotational speed
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
speed_hz = speed_rpm / 60

# Natural frequency modes (Hz) with gyroscopic effects
mode1 = 25 + 0.003 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
mode2 = 48 + 0.005 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
mode3 = 62 - 0.001 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
mode4 = 78 - 0.002 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))
mode5 = 92 + 0.004 * speed_rpm + np.random.normal(0, 0.15, len(speed_rpm))

orders = [1, 2, 3]
modes_data = [mode1, mode2, mode3, mode4, mode5]
mode_names = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "2nd Torsional"]

# Find critical speed intersections
critical_speeds = []
critical_info = []
for order in orders:
    eo_freq = order * speed_hz
    for mi, mode in enumerate(modes_data):
        diff = eo_freq - mode
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            frac = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            rpm_interp = speed_rpm[idx] + frac * (speed_rpm[idx + 1] - speed_rpm[idx])
            freq_interp = order * rpm_interp / 60
            if 0 < rpm_interp < 6000:
                critical_speeds.append((float(rpm_interp), float(freq_interp)))
                critical_info.append((order, mode_names[mi]))

# Style — stroke_width controls .reactive CSS base width for all line elements
# Setting it high ensures EO dashed lines are fully visible in CairoSVG PNG rendering
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#d0d0d0",
    guide_stroke_color="#e4e4e4",
    guide_stroke_dasharray="4, 6",
    major_guide_stroke_dasharray="2, 4",
    colors=(
        "#306998",  # 1st Bending — Python Blue
        "#1a9988",  # 2nd Bending — teal
        "#7b5ea7",  # 1st Torsional — purple
        "#d4812e",  # Axial — orange
        "#5a8c3c",  # 2nd Torsional — green
        "#b71c1c",  # 1x EO — dark red
        "#0d47a1",  # 2x EO — bold blue
        "#4a148c",  # 3x EO — bold purple
        "#d50000",  # Critical Speeds — vivid red
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
    opacity=1.0,
    opacity_hover=1.0,
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    stroke_width=6,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="campbell-basic · pygal · pyplots.ai",
    x_title="Rotational Speed (RPM)",
    y_title="Frequency (Hz)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=30,
    stroke=True,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:,.0f}",
    value_formatter=lambda y: f"{y:.1f}",
    margin_bottom=80,
    margin_left=100,
    margin_right=60,
    margin_top=50,
    x_label_rotation=0,
    truncate_legend=-1,
    range=(0, 130),
    xrange=(0, 6000),
    print_values=False,
    print_zeroes=False,
    tooltip_fancy_mode=True,
    js=[],
)

# Natural frequency mode curves — solid, thick lines with cubic interpolation
# Add label point near right end of each curve for direct labeling
for mode, label in zip(modes_data, mode_names, strict=True):
    points = []
    label_idx = int(len(speed_rpm) * 0.82)
    for j, (r, f) in enumerate(zip(speed_rpm, mode, strict=True)):
        if j == label_idx:
            points.append({"value": (float(r), float(f)), "label": label})
        else:
            points.append((float(r), float(f)))
    chart.add(label, points, stroke_style={"width": 10, "linecap": "round"}, show_dots=False, interpolate="cubic")

# Engine order lines — dashed, bold, many sample points for proper rendering
# Using multiple points along each line ensures CairoSVG renders the full stroke
eo_labels = ["1× EO", "2× EO", "3× EO"]
eo_dash_patterns = ["28, 14", "20, 10, 8, 10", "14, 8"]
for order, eo_label, dash in zip(orders, eo_labels, eo_dash_patterns, strict=True):
    eo_end_rpm = min(6000.0, 130.0 * 60.0 / order)
    eo_end_hz = order * eo_end_rpm / 60.0
    # Generate 40 evenly spaced points so pygal renders a proper visible path
    eo_rpms = np.linspace(0, eo_end_rpm, 40)
    eo_freqs = order * eo_rpms / 60.0
    # Place label near 70% of line length
    label_idx = int(len(eo_rpms) * 0.70)
    eo_points = []
    for j, (r, f) in enumerate(zip(eo_rpms, eo_freqs, strict=True)):
        if j == label_idx:
            eo_points.append({"value": (float(r), float(f)), "label": eo_label})
        else:
            eo_points.append((float(r), float(f)))
    chart.add(eo_label, eo_points, stroke_style={"width": 8, "dasharray": dash, "linecap": "round"}, show_dots=False)

# Critical speed markers — vivid red with tooltip showing intersection details
critical_points = []
for pt, info in zip(critical_speeds, critical_info, strict=True):
    order, mname = info
    critical_points.append({"value": pt, "label": f"{mname} × {order}× EO\n{pt[0]:.0f} RPM / {pt[1]:.1f} Hz"})
chart.add("Critical Speeds", critical_points, stroke=False, dots_size=22)

# Render both SVG/HTML (leveraging pygal's native SVG interactivity) and PNG
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
