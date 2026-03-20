""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
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
        x[i] = r * math.cos(angle) - r * math.cos(angle) * 0.0 + np.random.normal(0, 1)
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
        x[i] = np.random.normal(0, 0.3)
        y[i] = 15 + np.random.normal(0, 0.3)
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
        "#888888",  # baseline
        "#888888",  # three-pt arc
        "#888888",  # corner left
        "#888888",  # corner right
        "#888888",  # paint
        "#888888",  # ft circle top
        "#888888",  # ft circle bottom (dashed)
        "#888888",  # restricted arc
        "#555555",  # backboard
        "#dd6600",  # rim
        "#2eac66",  # made shots — green
        "#d94444",  # missed shots — red
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=48,
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
    xrange=(-28, 28),
    range=(-4, 33),
    margin_bottom=100,
    margin_left=30,
    margin_right=30,
    margin_top=60,
    print_values=False,
    print_zeroes=False,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    js=[],
)

# Court markings
line_style = {"width": 4, "linecap": "round", "linejoin": "round"}
thin_style = {"width": 3, "linecap": "round", "linejoin": "round"}

chart.add(None, baseline, stroke=True, show_dots=False, stroke_style={"width": 5, "linecap": "round"})
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
    stroke_style={"width": 3, "linecap": "round", "dasharray": "8,6"},
)
chart.add(None, restricted_arc, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, backboard, stroke=True, show_dots=False, stroke_style={"width": 6, "linecap": "round"})
chart.add(None, rim, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})

# Shot data
made_mask = made
made_pts = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} — Made"} for i in range(n_shots) if made_mask[i]
]
chart.add(f"Made ({sum(made_mask)}/{n_shots})", made_pts, stroke=False, dots_size=10)

missed_mask = ~made
missed_pts = [
    {"value": (float(x[i]), float(y[i])), "label": f"{shot_type[i]} — Missed"} for i in range(n_shots) if missed_mask[i]
]
chart.add(f"Missed ({sum(missed_mask)}/{n_shots})", missed_pts, stroke=False, dots_size=10)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
