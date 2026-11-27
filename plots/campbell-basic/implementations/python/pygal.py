"""anyplot.ai
campbell-basic: Campbell Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
WARNING = "#DDCC77"  # amber, semantic anchor outside the categorical pool

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation orders drawn as diagonals from the origin

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODES = ["1st Lateral", "Rocking", "2nd Lateral", "Axial", "1st Torsional"]  # role: frequency_mode_
FREQUENCY = "Frequency (Hz)"  # role: extra
ENGINE_ORDER = "Engine order"  # role: engine_order
CRITICAL_SPEED = "Critical speed (RPM)"  # role: critical_speeds

# Data: replace this block with your own table, for example df = pd.read_csv("modes.csv")
# Steam-turbine shaft: bearing stiffening raises two modes with speed, softening lowers the others.
speed = np.linspace(0, 6000, 80)
base_hz = [32.0, 54.0, 71.0, 96.0, 118.0]
stiffness = [0.35, 0.18, -0.12, -0.22, 0.10]  # relative change at 6000 RPM, nonlinear in speed
df = pd.DataFrame(
    {SPEED: speed}
    | {name: f0 * np.sqrt(1 + k * (speed / 6000) ** 2) for name, f0, k in zip(MODES, base_hz, stiffness, strict=True)}
)

# Plot
speed_rpm = df[SPEED].to_numpy()
speed_hz = speed_rpm / 60
top_hz = float(np.ceil(np.nanmax(df[MODES].to_numpy()) * 1.1 / 10) * 10)
max_rpm = float(np.nanmax(speed_rpm))

# Find critical speed intersections
critical_speeds = []
critical_info = []
for order in ENGINE_ORDERS:
    eo_freq = order * speed_hz
    for name in MODES:
        diff = eo_freq - df[name].to_numpy()
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            frac = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            rpm_interp = speed_rpm[idx] + frac * (speed_rpm[idx + 1] - speed_rpm[idx])
            freq_interp = order * rpm_interp / 60
            if 0 < rpm_interp < max_rpm:
                critical_speeds.append((float(rpm_interp), float(freq_interp)))
                critical_info.append((order, name))

font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="4, 6",
    major_guide_stroke_dasharray="2, 4",
    # modes first, then the engine order lines, then the amber critical speeds
    colors=(*IMPRINT_PALETTE, WARNING),
    font_family=font,
    title_font_family=font,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    legend_font_family=font,
    value_font_size=36,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=1.0,
    opacity_hover=1.0,
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    stroke_width=7,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="campbell-basic · python · pygal · anyplot.ai",
    x_title=SPEED,
    y_title=FREQUENCY,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=20,
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
    range=(0, top_hz),
    xrange=(0, max_rpm),
    print_values=False,
    print_zeroes=False,
    tooltip_fancy_mode=True,
    js=[],
)

# Natural frequency mode curves — solid, thick lines with cubic interpolation
for label in MODES:
    points = []
    label_idx = int(len(speed_rpm) * 0.82)
    for j, (r, f) in enumerate(zip(speed_rpm, df[label], strict=True)):
        if np.isnan(r) or np.isnan(f):
            continue  # a missing value draws nothing
        if j == label_idx:
            points.append({"value": (float(r), float(f)), "label": label})
        else:
            points.append((float(r), float(f)))
    chart.add(label, points, stroke_style={"width": 7, "linecap": "round"}, show_dots=False, interpolate="cubic")

# Engine order lines — dashed with prominent width and clear patterns
eo_dash_patterns = ["30, 12", "20, 8, 6, 8", "12, 6"]
for i, order in enumerate(ENGINE_ORDERS):
    eo_label = f"{order}× EO"
    dash = eo_dash_patterns[i % len(eo_dash_patterns)]
    eo_end_rpm = min(max_rpm, top_hz * 60.0 / order)
    eo_rpms = np.linspace(0, eo_end_rpm, 40)
    eo_freqs = order * eo_rpms / 60.0
    label_idx = int(len(eo_rpms) * 0.70)
    eo_points = []
    for j, (r, f) in enumerate(zip(eo_rpms, eo_freqs, strict=True)):
        if j == label_idx:
            eo_points.append({"value": (float(r), float(f)), "label": eo_label})
        else:
            eo_points.append((float(r), float(f)))
    chart.add(eo_label, eo_points, stroke_style={"width": 6, "dasharray": dash, "linecap": "round"}, show_dots=False)

# Critical speed markers — amber warning dots with intersection details
critical_points = []
for pt, info in zip(critical_speeds, critical_info, strict=True):
    order, mname = info
    critical_points.append({"value": pt, "label": f"{mname} × {order}× EO\n{pt[0]:.0f} RPM / {pt[1]:.1f} Hz"})
chart.add("Critical Speeds", critical_points, stroke=False, dots_size=15)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
