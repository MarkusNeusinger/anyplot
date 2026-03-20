"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic match events on a 105m x 68m pitch
np.random.seed(42)

n_passes = 80
n_shots = 15
n_tackles = 25
n_interceptions = 20

pass_x = np.random.uniform(10, 95, n_passes)
pass_y = np.random.uniform(5, 63, n_passes)
pass_end_x = pass_x + np.random.uniform(-15, 25, n_passes)
pass_end_y = pass_y + np.random.normal(0, 10, n_passes)
pass_end_x = np.clip(pass_end_x, 0, 105)
pass_end_y = np.clip(pass_end_y, 0, 68)
pass_outcome = np.random.choice(["successful", "unsuccessful"], n_passes, p=[0.75, 0.25])

shot_x = np.random.uniform(70, 104, n_shots)
shot_y = np.random.uniform(18, 50, n_shots)
shot_end_x = np.full(n_shots, 105.0)
shot_end_y = np.random.uniform(28, 40, n_shots)
shot_outcome = np.random.choice(["successful", "unsuccessful"], n_shots, p=[0.35, 0.65])

tackle_x = np.random.uniform(15, 85, n_tackles)
tackle_y = np.random.uniform(5, 63, n_tackles)
tackle_outcome = np.random.choice(["successful", "unsuccessful"], n_tackles, p=[0.6, 0.4])

interception_x = np.random.uniform(20, 80, n_interceptions)
interception_y = np.random.uniform(8, 60, n_interceptions)
interception_outcome = np.random.choice(["successful", "unsuccessful"], n_interceptions, p=[0.7, 0.3])

# Pitch marking coordinates (FIFA standard 105m x 68m)
pitch_outline = [(0, 0), (105, 0), (105, 68), (0, 68), (0, 0)]
halfway_line = [(52.5, 0), (52.5, 68)]
left_penalty = [(0, 13.84), (16.5, 13.84), (16.5, 54.16), (0, 54.16)]
right_penalty = [(105, 13.84), (88.5, 13.84), (88.5, 54.16), (105, 54.16)]
left_goal_area = [(0, 24.84), (5.5, 24.84), (5.5, 43.16), (0, 43.16)]
right_goal_area = [(105, 24.84), (99.5, 24.84), (99.5, 43.16), (105, 43.16)]

center_circle_angles = np.linspace(0, 2 * math.pi, 60)
center_circle = [(52.5 + 9.15 * math.cos(a), 34 + 9.15 * math.sin(a)) for a in center_circle_angles]

left_arc_angles = np.linspace(-0.65, 0.65, 20)
left_penalty_arc = [(11 + 9.15 * math.cos(a), 34 + 9.15 * math.sin(a)) for a in left_arc_angles]

right_arc_angles = np.linspace(math.pi - 0.65, math.pi + 0.65, 20)
right_penalty_arc = [(94 + 9.15 * math.cos(a), 34 + 9.15 * math.sin(a)) for a in right_arc_angles]

# Style
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="#2e7d32",
    plot_background="#388e3c",
    foreground="#ffffff",
    foreground_strong="#ffffff",
    foreground_subtle="#388e3c",
    guide_stroke_color="#388e3c",
    colors=(
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#ffffff",
        "#42a5f5",
        "#90caf9",
        "#ef5350",
        "#ef9a9a",
        "#ff9800",
        "#ffcc80",
        "#ab47bc",
        "#ce93d8",
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    legend_font_family=font,
    value_font_size=24,
    tooltip_font_size=24,
    tooltip_font_family=font,
    opacity=0.9,
    opacity_hover=1.0,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-pitch-events \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=20,
    stroke=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-5, 110),
    range=(-5, 73),
    margin_bottom=90,
    margin_left=20,
    margin_right=20,
    margin_top=50,
    print_values=False,
    print_zeroes=False,
    js=[],
)

# Pitch markings as line series
chart.add(
    None,
    pitch_outline,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)
chart.add(None, halfway_line, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})
chart.add(
    None, left_penalty, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round", "linejoin": "round"}
)
chart.add(
    None,
    right_penalty,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round", "linejoin": "round"},
)
chart.add(
    None,
    left_goal_area,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round", "linejoin": "round"},
)
chart.add(
    None,
    right_goal_area,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "linecap": "round", "linejoin": "round"},
)
chart.add(None, center_circle, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})
chart.add(None, [(52.5, 34)], stroke=False, dots_size=6)
chart.add(None, left_penalty_arc, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})
chart.add(None, right_penalty_arc, stroke=True, show_dots=False, stroke_style={"width": 4, "linecap": "round"})

# Event data — successful events as filled dots, unsuccessful as smaller/lower opacity
# Passes (successful)
pass_succ_mask = pass_outcome == "successful"
pass_succ_pts = [
    {"value": (float(x), float(y)), "label": f"Pass \u2192 ({float(ex):.0f}, {float(ey):.0f})"}
    for x, y, ex, ey in zip(
        pass_x[pass_succ_mask],
        pass_y[pass_succ_mask],
        pass_end_x[pass_succ_mask],
        pass_end_y[pass_succ_mask],
        strict=True,
    )
]
chart.add("Pass (successful)", pass_succ_pts, stroke=False, dots_size=8)

# Passes (unsuccessful)
pass_fail_mask = ~pass_succ_mask
pass_fail_pts = [
    {"value": (float(x), float(y)), "label": f"Pass \u2192 ({float(ex):.0f}, {float(ey):.0f})"}
    for x, y, ex, ey in zip(
        pass_x[pass_fail_mask],
        pass_y[pass_fail_mask],
        pass_end_x[pass_fail_mask],
        pass_end_y[pass_fail_mask],
        strict=True,
    )
]
chart.add("Pass (unsuccessful)", pass_fail_pts, stroke=False, dots_size=6)

# Shots (successful)
shot_succ_mask = shot_outcome == "successful"
shot_succ_pts = [
    {"value": (float(x), float(y)), "label": "Shot on target"}
    for x, y in zip(shot_x[shot_succ_mask], shot_y[shot_succ_mask], strict=True)
]
chart.add("Shot (successful)", shot_succ_pts, stroke=False, dots_size=12)

# Shots (unsuccessful)
shot_fail_mask = ~shot_succ_mask
shot_fail_pts = [
    {"value": (float(x), float(y)), "label": "Shot off target"}
    for x, y in zip(shot_x[shot_fail_mask], shot_y[shot_fail_mask], strict=True)
]
chart.add("Shot (unsuccessful)", shot_fail_pts, stroke=False, dots_size=8)

# Tackles (successful)
tackle_succ_mask = tackle_outcome == "successful"
tackle_succ_pts = [
    (float(x), float(y)) for x, y in zip(tackle_x[tackle_succ_mask], tackle_y[tackle_succ_mask], strict=True)
]
chart.add("Tackle (successful)", tackle_succ_pts, stroke=False, dots_size=8)

# Tackles (unsuccessful)
tackle_fail_mask = ~tackle_succ_mask
tackle_fail_pts = [
    (float(x), float(y)) for x, y in zip(tackle_x[tackle_fail_mask], tackle_y[tackle_fail_mask], strict=True)
]
chart.add("Tackle (unsuccessful)", tackle_fail_pts, stroke=False, dots_size=6)

# Interceptions (successful)
int_succ_mask = interception_outcome == "successful"
int_succ_pts = [
    (float(x), float(y)) for x, y in zip(interception_x[int_succ_mask], interception_y[int_succ_mask], strict=True)
]
chart.add("Interception (successful)", int_succ_pts, stroke=False, dots_size=8)

# Interceptions (unsuccessful)
int_fail_mask = ~int_succ_mask
int_fail_pts = [
    (float(x), float(y)) for x, y in zip(interception_x[int_fail_mask], interception_y[int_fail_mask], strict=True)
]
chart.add("Interception (unsuccessful)", int_fail_pts, stroke=False, dots_size=6)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
