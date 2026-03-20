""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-20
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

# Corner arcs (quarter circles, radius 1m)
corner_angles_bl = np.linspace(0, math.pi / 2, 10)
corner_bl = [(math.cos(a), math.sin(a)) for a in corner_angles_bl]
corner_angles_br = np.linspace(math.pi / 2, math.pi, 10)
corner_br = [(105 + math.cos(a), math.sin(a)) for a in corner_angles_br]
corner_angles_tr = np.linspace(math.pi, 3 * math.pi / 2, 10)
corner_tr = [(105 + math.cos(a), 68 + math.sin(a)) for a in corner_angles_tr]
corner_angles_tl = np.linspace(3 * math.pi / 2, 2 * math.pi, 10)
corner_tl = [(math.cos(a), 68 + math.sin(a)) for a in corner_angles_tl]

# Style — high-contrast colorblind-safe palette
# Passes: blue lines, Shots: red/crimson lines, Tackles: orange dots, Interceptions: teal dots
# Successful: bright/saturated, Unsuccessful: desaturated/muted with distinct hue shift
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="#1b5e20",
    plot_background="#2e7d32",
    foreground="#ffffff",
    foreground_strong="#ffffff",
    foreground_subtle="#2e7d32",
    guide_stroke_color="#2e7d32",
    colors=(
        "#ffffff",  # pitch outline
        "#ffffff",  # halfway
        "#ffffff",  # left penalty
        "#ffffff",  # right penalty
        "#ffffff",  # left goal area
        "#ffffff",  # right goal area
        "#ffffff",  # center circle
        "#ffffff",  # center spot
        "#ffffff",  # left penalty arc
        "#ffffff",  # right penalty arc
        "#ffffff",  # corner bl
        "#ffffff",  # corner br
        "#ffffff",  # corner tr
        "#ffffff",  # corner tl
        "#64b5f6",  # Pass (successful) — medium blue, subtle
        "#fdd835",  # Pass (unsuccessful) — yellow, visible on green
        "#d50000",  # Shot (successful/goal) — bright red, focal point
        "#ff8a80",  # Shot (unsuccessful) — salmon pink, visible
        "#ff6d00",  # Tackle (successful) — vivid orange
        "#ffab40",  # Tackle (unsuccessful) — amber
        "#00bfa5",  # Interception (successful) — bright teal
        "#80cbc4",  # Interception (unsuccessful) — light teal
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    legend_font_family=font,
    value_font_size=24,
    tooltip_font_size=24,
    tooltip_font_family=font,
    opacity=0.85,
    opacity_hover=1.0,
    stroke_opacity=0.9,
    stroke_opacity_hover=1,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-pitch-events · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    stroke=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-5, 110),
    range=(-5, 73),
    margin_bottom=100,
    margin_left=20,
    margin_right=20,
    margin_top=50,
    print_values=False,
    print_zeroes=False,
    js=[],
)

# Pitch markings as line series
marking_style = {"width": 5, "linecap": "round", "linejoin": "round"}
thin_style = {"width": 4, "linecap": "round", "linejoin": "round"}

chart.add(
    None,
    pitch_outline,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)
chart.add(None, halfway_line, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, left_penalty, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, right_penalty, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, left_goal_area, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, right_goal_area, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, center_circle, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, [(52.5, 34)], stroke=False, dots_size=6)
chart.add(None, left_penalty_arc, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, right_penalty_arc, stroke=True, show_dots=False, stroke_style=thin_style)
chart.add(None, corner_bl, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})
chart.add(None, corner_br, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})
chart.add(None, corner_tr, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})
chart.add(None, corner_tl, stroke=True, show_dots=False, stroke_style={"width": 3, "linecap": "round"})

# Event data — passes and shots as directional line segments (pygal None-break technique)
# Tackles and interceptions as scatter dots with distinct sizes

# Passes as directional arrows (line segments with dots at endpoints)
# Using None to break between individual pass segments — idiomatic pygal pattern
pass_succ_mask = pass_outcome == "successful"
pass_succ_lines = []
for sx, sy, ex, ey in zip(
    pass_x[pass_succ_mask], pass_y[pass_succ_mask], pass_end_x[pass_succ_mask], pass_end_y[pass_succ_mask], strict=True
):
    pass_succ_lines.append({"value": (float(sx), float(sy)), "label": f"Pass → ({float(ex):.0f}, {float(ey):.0f})"})
    pass_succ_lines.append((float(ex), float(ey)))
    pass_succ_lines.append(None)
chart.add(
    "Pass ✓", pass_succ_lines, stroke=True, show_dots=True, dots_size=5, stroke_style={"width": 2, "linecap": "round"}
)

pass_fail_mask = ~pass_succ_mask
pass_fail_lines = []
for sx, sy, ex, ey in zip(
    pass_x[pass_fail_mask], pass_y[pass_fail_mask], pass_end_x[pass_fail_mask], pass_end_y[pass_fail_mask], strict=True
):
    pass_fail_lines.append({"value": (float(sx), float(sy)), "label": f"Pass ✗ → ({float(ex):.0f}, {float(ey):.0f})"})
    pass_fail_lines.append((float(ex), float(ey)))
    pass_fail_lines.append(None)
chart.add(
    "Pass ✗",
    pass_fail_lines,
    stroke=True,
    show_dots=True,
    dots_size=5,
    stroke_style={"width": 2, "linecap": "round", "dasharray": "8,6"},
)

# Shots as directional lines (prominent — key events for storytelling)
shot_succ_mask = shot_outcome == "successful"
shot_succ_lines = []
for sx, sy, ex, ey in zip(
    shot_x[shot_succ_mask], shot_y[shot_succ_mask], shot_end_x[shot_succ_mask], shot_end_y[shot_succ_mask], strict=True
):
    shot_succ_lines.append({"value": (float(sx), float(sy)), "label": "Goal!"})
    shot_succ_lines.append((float(ex), float(ey)))
    shot_succ_lines.append(None)
chart.add(
    "Shot ✓ (goal)",
    shot_succ_lines,
    stroke=True,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 6, "linecap": "round"},
)

shot_fail_mask = ~shot_succ_mask
shot_fail_lines = []
for sx, sy, ex, ey in zip(
    shot_x[shot_fail_mask], shot_y[shot_fail_mask], shot_end_x[shot_fail_mask], shot_end_y[shot_fail_mask], strict=True
):
    shot_fail_lines.append({"value": (float(sx), float(sy)), "label": "Shot missed"})
    shot_fail_lines.append((float(ex), float(ey)))
    shot_fail_lines.append(None)
chart.add(
    "Shot ✗",
    shot_fail_lines,
    stroke=True,
    show_dots=True,
    dots_size=9,
    stroke_style={"width": 4, "linecap": "round", "dasharray": "6,4"},
)

# Tackles as scatter dots (large markers)
tackle_succ_mask = tackle_outcome == "successful"
tackle_succ_pts = [
    {"value": (float(x), float(y)), "label": "Tackle won"}
    for x, y in zip(tackle_x[tackle_succ_mask], tackle_y[tackle_succ_mask], strict=True)
]
chart.add("Tackle ✓", tackle_succ_pts, stroke=False, dots_size=16)

tackle_fail_mask = ~tackle_succ_mask
tackle_fail_pts = [
    {"value": (float(x), float(y)), "label": "Tackle lost"}
    for x, y in zip(tackle_x[tackle_fail_mask], tackle_y[tackle_fail_mask], strict=True)
]
chart.add("Tackle ✗", tackle_fail_pts, stroke=False, dots_size=10)

# Interceptions as scatter dots
int_succ_mask = interception_outcome == "successful"
int_succ_pts = [
    {"value": (float(x), float(y)), "label": "Interception"}
    for x, y in zip(interception_x[int_succ_mask], interception_y[int_succ_mask], strict=True)
]
chart.add("Intercept ✓", int_succ_pts, stroke=False, dots_size=14)

int_fail_mask = ~int_succ_mask
int_fail_pts = [
    {"value": (float(x), float(y)), "label": "Intercept missed"}
    for x, y in zip(interception_x[int_fail_mask], interception_y[int_fail_mask], strict=True)
]
chart.add("Intercept ✗", int_fail_pts, stroke=False, dots_size=9)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
