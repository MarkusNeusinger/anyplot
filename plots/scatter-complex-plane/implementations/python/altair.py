""" anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-28
"""

import importlib
import os
import sys
from fractions import Fraction

import numpy as np
import pandas as pd
from PIL import Image


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — canonical order, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ROTATION_ROWS = 2  # a rotation is drawn when the last category holds a point and its image
ARC_STEPS = 40  # segments of the rotation arc
VIEW_PX = 600  # logical width and height of the plot view
BACK_PX = 17  # arrowhead centre to point centre: marker radius (9.4) + head half-size (7)
LABEL_HALF_HEIGHT = 0.06  # half the height of a 10 px label, in data units

# Columns: set these to your table's column names
REAL = "Real axis"  # role: real
IMAGINARY = "Imaginary axis"  # role: imaginary
LABEL = "Point"  # role: label
CATEGORY = "Category"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
# 3rd roots of unity e^(2πik/3), arbitrary points in all four quadrants, and a rotation z -> z·e^(iπ/4)
z_original = 1.5 + 0.8j
groups = {
    "Roots of Unity": ([np.exp(2j * np.pi * k / 3) for k in range(3)], ["ω0", "ω1", "ω2"]),
    "Arbitrary": ([2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -0.5 - 1.5j, 2.0 + 0.5j], ["z₁", "z₂", "z₃", "z₄", "z₅"]),
    "Transformation": ([z_original, z_original * np.exp(1j * np.pi / 4)], ["z", "z·e^(iπ/4)"]),
}
df = pd.DataFrame(
    [
        {REAL: z.real, IMAGINARY: z.imag, LABEL: name, CATEGORY: category}
        for category, (points, names) in groups.items()
        for z, name in zip(points, names, strict=True)
    ]
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
categories = list(df[CATEGORY].unique())
color_scale = alt.Scale(domain=categories, range=IMPRINT_PALETTE)

# Axis range: symmetric, a quarter unit beyond the farthest coordinate
axis_limit = float(np.ceil(df[[REAL, IMAGINARY]].abs().max().max() * 4) / 4 + 0.25)

# Annotation text: label and rectangular form a+bi
rect = [f"{round(x, 2)}{'+' if y >= 0 else ''}{round(y, 2)}i" for x, y in zip(df[REAL], df[IMAGINARY], strict=True)]
notes = pd.DataFrame({"text": df[LABEL] + " = " + pd.Series(rect), "category": df[CATEGORY]})

half_width = 0.026 * notes["text"].str.len()

# Unit circle (reference geometry)
theta = np.linspace(0, 2 * np.pi, 200)
circle_df = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta), "order": range(len(theta))})

# Vector segments from the origin to each point
arrow_df = pd.concat(
    [
        pd.DataFrame({"x": 0.0, "y": 0.0, "group": df[LABEL], "order": 0, "category": df[CATEGORY]}),
        pd.DataFrame({"x": df[REAL], "y": df[IMAGINARY], "group": df[LABEL], "order": 1, "category": df[CATEGORY]}),
    ]
)

# Arrowheads: pulled back by the marker radius plus the head's own half-size (in screen pixels, converted
# to data units), so the whole triangle shows and its tip touches the edge of the point marker
magnitude = np.hypot(df[REAL], df[IMAGINARY])
back = BACK_PX * 2 * axis_limit / VIEW_PX / magnitude
arrowhead_df = pd.DataFrame(
    {
        "x": df[REAL] * (1 - back),
        "y": df[IMAGINARY] * (1 - back),
        "angle": 90 - np.degrees(np.arctan2(df[IMAGINARY], df[REAL])),
        "category": df[CATEGORY],
    }
)

# Rotation arc: from the next-to-last point to the last one when they share a category, at 55% of its length
last_group = df[df[CATEGORY] == df[CATEGORY].iloc[-1]]
layers_extra = []
arc_xy = np.empty((0, 2))
arc_label_xy = np.empty((0, 2))
if len(last_group) == ROTATION_ROWS:
    z_from = complex(last_group[REAL].iloc[0], last_group[IMAGINARY].iloc[0])
    z_to = complex(last_group[REAL].iloc[1], last_group[IMAGINARY].iloc[1])
    arc_start = np.angle(z_from)
    arc_turn = np.angle(z_to / z_from)
    arc_r = abs(z_from) * 0.55
    arc_theta = np.linspace(arc_start, arc_start + arc_turn, ARC_STEPS)
    arc_df = pd.DataFrame({"x": arc_r * np.cos(arc_theta), "y": arc_r * np.sin(arc_theta), "order": range(ARC_STEPS)})
    turn = Fraction(arc_turn / np.pi).limit_denominator(12)
    turn_text = f"{'' if turn.numerator == 1 else turn.numerator}π/{turn.denominator}"
    mid = arc_start + arc_turn / 2
    arc_xy = arc_df[["x", "y"]].to_numpy()
    # Label just outside the arc, along the bisector between the two vectors
    arc_label_xy = np.array([[(arc_r + 0.3) * np.cos(mid), (arc_r + 0.3) * np.sin(mid)]])
    arc_label_df = pd.DataFrame({"x": arc_label_xy[:, 0], "y": arc_label_xy[:, 1], "text": [turn_text]})
    layers_extra = [
        alt.Chart(arc_df)
        .mark_line(color=IMPRINT_PALETTE[2], strokeWidth=2.5, strokeDash=[5, 3], opacity=0.75)
        .encode(x="x:Q", y="y:Q", order="order:O"),
        alt.Chart(arc_label_df)
        .mark_text(fontSize=12, fontStyle="italic", fontWeight="bold", color=INK_SOFT, opacity=0.9)
        .encode(x="x:Q", y="y:Q", text="text:N"),
    ]

# Axis lines through the origin
axis_line_data = pd.DataFrame(
    {
        "x": [-axis_limit, axis_limit, 0, 0],
        "y": [0, 0, -axis_limit, axis_limit],
        "axis": ["real", "real", "imag", "imag"],
        "order": [0, 1, 0, 1],
    }
)

# Tick marks (every 0.5) and whole-number labels on the axes through the origin
tick_step = 10 ** np.floor(np.log10(axis_limit)) / 2
tick_count = int(axis_limit // tick_step)
tick_values = np.arange(-tick_count, tick_count + 1) * tick_step
tick_values = tick_values[np.abs(tick_values) > 1e-9]
TICK_HALF = 0.05
real_ticks = pd.DataFrame({"x": tick_values, "y0": -TICK_HALF, "y1": TICK_HALF})
imag_ticks = pd.DataFrame({"y": tick_values, "x0": -TICK_HALF, "x1": TICK_HALF})
whole = tick_values[np.abs(tick_values / tick_step % 2) < 1e-9]
tick_labels = pd.DataFrame(
    {
        "x": np.concatenate([whole, np.full(len(whole), -0.17)]),
        "y": np.concatenate([np.full(len(whole), -0.17), whole]),
        "text": [f"{v:g}" for v in np.concatenate([whole, whole])],
    }
)

# Label placement: each label goes to the free spot around its point (8 directions, 2 distances) that
# crosses the fewest vectors, circle, arc, axis ticks and other labels, preferring the side away from the origin
sample_t = np.linspace(0, 1, 150)[:, None]
axis_run = np.linspace(-axis_limit, axis_limit, 200)
points_xy = df[[REAL, IMAGINARY]].to_numpy()
lines_xy = np.vstack(
    [(sample_t * p).reshape(-1, 2) for p in points_xy]
    + [circle_df[["x", "y"]].to_numpy(), arc_xy]
    + [np.column_stack([axis_run, axis_run * 0]), np.column_stack([axis_run * 0, axis_run])]
    + [
        np.column_stack([tick_labels["x"], tick_labels["y"]]) + [dx, dy]
        for dx in (-0.04, 0, 0.04)
        for dy in (-0.06, 0, 0.06)
    ]
)
placed = []
note_x, note_y = [], []
for point, hw in zip(points_xy, half_width, strict=True):
    hh = LABEL_HALF_HEIGHT
    radial = np.arctan2(point[1], point[0])
    best_cost, best_xy = np.inf, point
    for ring in (0.13, 0.26):
        for angle in np.radians(np.arange(0, 360, 45)):
            cx = point[0] + np.cos(angle) * (hw + ring)
            cy = point[1] + np.sin(angle) * (hh + ring)
            near = (np.abs(lines_xy[:, 0] - cx) < hw + 0.05) & (np.abs(lines_xy[:, 1] - cy) < hh + 0.05)
            on_mark = (np.abs(points_xy[:, 0] - cx) < hw + 0.1) & (np.abs(points_xy[:, 1] - cy) < hh + 0.1)
            on_arc_label = (np.abs(arc_label_xy[:, 0] - cx) < hw + 0.12) & (np.abs(arc_label_xy[:, 1] - cy) < hh + 0.1)
            on_label = sum(abs(cx - qx) < hw + qw + 0.02 and abs(cy - qy) < 2 * hh + 0.02 for qx, qy, qw in placed)
            outside = abs(cx) + hw > axis_limit - 0.05 or abs(cy) + hh > axis_limit - 0.05
            away = abs(np.angle(np.exp(1j * (angle - radial)))) / np.pi
            cost = near.sum() + 60 * (on_mark.sum() + on_arc_label.sum() + on_label) + 1000 * outside + away + ring
            if cost < best_cost:
                best_cost, best_xy = cost, np.array([cx, cy])
    placed.append((best_xy[0], best_xy[1], hw))
    note_x.append(best_xy[0])
    note_y.append(best_xy[1])
notes["x"] = note_x
notes["y"] = note_y

# Interactive legend selection — click to highlight by category
highlight = alt.selection_point(fields=["category"], bind="legend")
opacity_cond = alt.condition(highlight, alt.value(1.0), alt.value(0.25))
color_enc = alt.Color("category:N", scale=color_scale, legend=None)

axis_cfg = {
    "tickCount": 11,
    "labelFontSize": 10,
    "titleFontSize": 12,
    "gridDash": [3, 3],
    "gridOpacity": 0.12,
    "titleColor": INK,
    "labelColor": INK_SOFT,
    "domainColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

axes = (
    alt.Chart(axis_line_data)
    .mark_line(color=INK_MUTED, strokeWidth=1.5, opacity=0.6)
    .encode(
        x=alt.X("x:Q", title=REAL, scale=alt.Scale(domain=[-axis_limit, axis_limit]), axis=alt.Axis(**axis_cfg)),
        y=alt.Y("y:Q", title=IMAGINARY, scale=alt.Scale(domain=[-axis_limit, axis_limit]), axis=alt.Axis(**axis_cfg)),
        detail="axis:N",
        order="order:O",
    )
)

axis_ticks = [
    alt.Chart(real_ticks).mark_rule(color=INK_MUTED, strokeWidth=1.5).encode(x="x:Q", y="y0:Q", y2="y1:Q"),
    alt.Chart(imag_ticks).mark_rule(color=INK_MUTED, strokeWidth=1.5).encode(y="y:Q", x="x0:Q", x2="x1:Q"),
    alt.Chart(tick_labels).mark_text(fontSize=10, color=INK_MUTED).encode(x="x:Q", y="y:Q", text="text:N"),
]

unit_circle = (
    alt.Chart(circle_df)
    .mark_line(color=INK_SOFT, strokeWidth=2.0, strokeDash=[8, 6], opacity=0.5)
    .encode(x="x:Q", y="y:Q", order="order:O")
)

vectors = (
    alt.Chart(arrow_df)
    .mark_line(strokeWidth=2.5)
    .encode(x="x:Q", y="y:Q", detail="group:N", order="order:O", color=color_enc, opacity=opacity_cond)
    .add_params(highlight)
)

arrowheads = (
    alt.Chart(arrowhead_df)
    .mark_point(shape="triangle-up", filled=True, size=200)
    .encode(x="x:Q", y="y:Q", angle=alt.Angle("angle:Q"), color=color_enc, opacity=opacity_cond)
    .add_params(highlight)
)

# Scatter points with a page-colored outline for definition on both themes; the legend lives inside the
# view (bottom-left corner) so the view keeps equal x and y scales
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=220, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        x=alt.X(
            REAL.translate(ESCAPE),
            type="quantitative",
            title=REAL,
            scale=alt.Scale(domain=[-axis_limit, axis_limit]),
            axis=alt.Axis(**axis_cfg),
        ),
        y=alt.Y(
            IMAGINARY.translate(ESCAPE),
            type="quantitative",
            title=IMAGINARY,
            scale=alt.Scale(domain=[-axis_limit, axis_limit]),
            axis=alt.Axis(**axis_cfg),
        ),
        color=alt.Color(
            CATEGORY.translate(ESCAPE),
            type="nominal",
            title=CATEGORY,
            scale=color_scale,
            legend=alt.Legend(
                titleFontSize=10,
                labelFontSize=10,
                symbolType="circle",
                symbolSize=150,
                symbolStrokeWidth=0,
                orient="none",
                legendX=8,
                legendY=420,
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                padding=6,
            ),
        ),
        opacity=opacity_cond,
        tooltip=[
            alt.Tooltip(LABEL.translate(ESCAPE), type="nominal", title=LABEL),
            alt.Tooltip(REAL.translate(ESCAPE), type="quantitative", title=REAL, format=".2f"),
            alt.Tooltip(IMAGINARY.translate(ESCAPE), type="quantitative", title=IMAGINARY, format=".2f"),
            alt.Tooltip(CATEGORY.translate(ESCAPE), type="nominal", title=CATEGORY),
        ],
    )
    .transform_calculate(category=f"datum['{CATEGORY}']")
    .add_params(highlight)
)

# Point labels: label + rectangular form
annotations = (
    alt.Chart(notes)
    .mark_text(fontSize=10, fontWeight="bold", color=INK)
    .encode(x="x:Q", y="y:Q", text="text:N", opacity=opacity_cond)
    .add_params(highlight)
)

# "Re" and "Im" italic labels at the axis ends
axis_labels_df = pd.DataFrame({"x": [axis_limit - 0.15, 0.22], "y": [-0.22, axis_limit - 0.10], "text": ["Re", "Im"]})
axis_labels = (
    alt.Chart(axis_labels_df)
    .mark_text(fontSize=12, fontStyle="italic", fontWeight="bold", color=INK_MUTED)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

title_text = "scatter-complex-plane · python · altair · anyplot.ai"
chart = (
    alt.layer(axes, *axis_ticks, unit_circle, *layers_extra, vectors, arrowheads, points, annotations, axis_labels)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding={"left": 23, "right": 23, "top": 10, "bottom": 10},
        background=PAGE_BG,
        title=alt.Title(
            title_text,
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle="Points, vectors from the origin and the unit circle in the complex plane",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .resolve_scale(color="independent")
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(titlePadding=14)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .interactive()
)

# Save PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Fit-to-canvas safety: only a size mismatch lands here; scale down as a whole, never crop
TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
