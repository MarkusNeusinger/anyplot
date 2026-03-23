""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic NBA shot chart (200 attempts)
np.random.seed(42)

n_shots = 200

# Generate shot locations across the half-court (50 ft wide x 47 ft deep)
# Cluster shots around common zones: paint, mid-range, three-point line
zones = np.random.choice(["paint", "midrange", "three", "free_throw"], n_shots, p=[0.30, 0.25, 0.35, 0.10])

x = np.zeros(n_shots)
y = np.zeros(n_shots)
made = np.zeros(n_shots, dtype=bool)
shot_type = []

for i in range(n_shots):
    if zones[i] == "paint":
        x[i] = np.random.uniform(-8, 8)
        y[i] = np.random.uniform(0, 12)
        made[i] = np.random.random() < 0.55
        shot_type.append("2-pointer")
    elif zones[i] == "midrange":
        angle = np.random.uniform(0, math.pi)
        r = np.random.uniform(10, 22)
        x[i] = r * math.cos(angle)
        y[i] = r * math.sin(angle)
        made[i] = np.random.random() < 0.40
        shot_type.append("2-pointer")
    elif zones[i] == "three":
        angle = np.random.uniform(0.15, math.pi - 0.15)
        r = np.random.uniform(23, 27)
        x[i] = r * math.cos(angle)
        y[i] = r * math.sin(angle)
        # Corner threes
        if np.random.random() < 0.25:
            x[i] = np.random.choice([-22, 22]) + np.random.normal(0, 0.5)
            y[i] = np.random.uniform(0, 8)
        made[i] = np.random.random() < 0.36
        shot_type.append("3-pointer")
    else:
        x[i] = np.random.normal(0, 0.8)
        y[i] = 15 + np.random.normal(0, 0.8)
        made[i] = np.random.random() < 0.80
        shot_type.append("free-throw")

# Court geometry — NBA half-court (origin at basket center)
# Three-point arc: 23.75 ft radius, 22 ft in corners (straight to ~14 ft out)
three_pt_angles = np.linspace(math.acos(22.0 / 23.75), math.pi - math.acos(22.0 / 23.75), 80)
three_pt_arc = [(23.75 * math.cos(a), 23.75 * math.sin(a)) for a in three_pt_angles]
# Corner lines
three_pt_left_corner = [(-22, 0), (-22, 14)]
three_pt_right_corner = [(22, 0), (22, 14)]

# Paint / key area: 16 ft wide, 19 ft deep (to free-throw line)
paint = [(-8, 0), (-8, 19), (8, 19), (8, 0)]

# Free-throw circle (top half visible, 6 ft radius centered at free-throw line)
ft_circle_angles = np.linspace(0, math.pi, 40)
ft_circle_top = [(6 * math.cos(a), 19 + 6 * math.sin(a)) for a in ft_circle_angles]
ft_circle_bottom_angles = np.linspace(math.pi, 2 * math.pi, 40)
ft_circle_bottom = [(6 * math.cos(a), 19 + 6 * math.sin(a)) for a in ft_circle_bottom_angles]

# Restricted area arc: 4 ft radius
restricted_angles = np.linspace(0, math.pi, 30)
restricted_arc = [(4 * math.cos(a), 4 * math.sin(a)) for a in restricted_angles]

# Backboard and basket
backboard = [(-3, -0.5), (3, -0.5)]
rim_angles = np.linspace(0, 2 * math.pi, 30)
rim = [(0.75 * math.cos(a), 1.5 + 0.75 * math.sin(a)) for a in rim_angles]

# Baseline
baseline = [(-25, 0), (25, 0)]

# Style
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#f5f0e8",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#f5f0e8",
    guide_stroke_color="#f5f0e8",
    colors=(
        "#b8a990",  # baseline — slightly more visible court lines
        "#b8a990",  # three-pt arc
        "#b8a990",  # corner left
        "#b8a990",  # corner right
        "#b8a990",  # paint
        "#b8a990",  # ft circle top
        "#b8a990",  # ft circle bottom (dashed)
        "#b8a990",  # restricted arc
        "#8c7e6e",  # backboard — darker for emphasis
        "#c87830",  # rim — orange
        "#2166ac",  # made inside — blue (colorblind-safe)
        "#5aa3d9",  # made perimeter — light blue
        "#d6604d",  # missed inside — orange-red (colorblind-safe)
        "#e8a088",  # missed perimeter — light salmon
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=28,
    major_label_font_size=24,
    legend_font_size=36,
    legend_font_family=font,
    value_font_size=20,
    tooltip_font_size=22,
    tooltip_font_family=font,
    opacity=0.75,
    opacity_hover=1.0,
)

# Chart — square aspect for court (use 3600x3600 for 1:1)
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="scatter-shot-chart · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=28,
    stroke=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-27, 27),
    range=(-3, 28),
    margin_bottom=100,
    margin_left=20,
    margin_right=20,
    margin_top=60,
    print_values=False,
    print_zeroes=False,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    truncate_legend=-1,
    value_formatter=lambda val: f"{val:.1f} ft",
    js=[],
)

# Court markings
line_style = {"width": 3, "linecap": "round", "linejoin": "round"}
thin_style = {"width": 2.5, "linecap": "round", "linejoin": "round"}

chart.add(None, baseline, stroke=True, show_dots=False, stroke_style={"width": 3.5, "linecap": "round"})
chart.add(None, three_pt_arc, stroke=True, show_dots=False, stroke_style=line_style)
chart.add(None, three_pt_left_corner, stroke=True, show_dots=False, stroke_style=line_style)
chart.add(None, three_pt_right_corner, stroke=True, show_dots=False, stroke_style=line_style)
chart.add(None, paint, stroke=True, show_dots=False, stroke_style=line_style)
chart.add(None, ft_circle_top, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(
    None,
    ft_circle_bottom,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 2.5, "linecap": "round", "dasharray": "8,6"},
)
chart.add(None, restricted_arc, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, backboard, stroke=True, show_dots=False, stroke_style={"width": 5, "linecap": "round"})
chart.add(None, rim, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})

# Shot data — separate by zone for visual hierarchy
# Paint/FT shots (high efficiency) get larger dots; perimeter shots get smaller dots
# Compute zone FG% for legend labels and storytelling
paint_ft_mask = np.array([z in ("paint", "free_throw") for z in zones])
perim_mask = ~paint_ft_mask
n_inside = int(np.sum(paint_ft_mask))
n_perim = int(np.sum(perim_mask))
inside_fg = np.sum(made[paint_ft_mask]) / n_inside * 100
perim_fg = np.sum(made[perim_mask]) / n_perim * 100

# Made shots — paint/FT with bigger markers (high-value zone)
made_inside = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} ({zones[i]}) — Made", "node": {"r": 12}}
    for i in range(n_shots)
    if made[i] and zones[i] in ("paint", "free_throw")
]
made_outside = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} ({zones[i]}) — Made", "node": {"r": 7}}
    for i in range(n_shots)
    if made[i] and zones[i] in ("midrange", "three")
]

chart.add(
    f"\u2b24 Made Inside — {inside_fg:.0f}% FG ({len(made_inside)}/{n_inside})",
    made_inside,
    stroke=False,
    dots_size=13,
    formatter=lambda val: f"({val[0]:.1f}, {val[1]:.1f}) ft" if isinstance(val, (list, tuple)) else str(val),
)
chart.add(
    f"\u2022 Made Perimeter — {perim_fg:.0f}% FG ({len(made_outside)}/{n_perim})",
    made_outside,
    stroke=False,
    dots_size=8,
    formatter=lambda val: f"({val[0]:.1f}, {val[1]:.1f}) ft" if isinstance(val, (list, tuple)) else str(val),
)

# Missed shots — same size hierarchy
missed_inside = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} ({zones[i]}) — Missed", "node": {"r": 12}}
    for i in range(n_shots)
    if not made[i] and zones[i] in ("paint", "free_throw")
]
missed_outside = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} ({zones[i]}) — Missed", "node": {"r": 7}}
    for i in range(n_shots)
    if not made[i] and zones[i] in ("midrange", "three")
]
chart.add(
    f"\u2b24 Missed Inside ({len(missed_inside)})",
    missed_inside,
    stroke=False,
    dots_size=13,
    formatter=lambda val: f"({val[0]:.1f}, {val[1]:.1f}) ft" if isinstance(val, (list, tuple)) else str(val),
)
chart.add(
    f"\u2022 Missed Perimeter ({len(missed_outside)})",
    missed_outside,
    stroke=False,
    dots_size=8,
    formatter=lambda val: f"({val[0]:.1f}, {val[1]:.1f}) ft" if isinstance(val, (list, tuple)) else str(val),
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
