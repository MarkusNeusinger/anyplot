"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-02
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
axis_limit = float(np.ceil(df[[REAL, IMAGINARY]].abs().to_numpy().max() * 4) / 4 + 0.25)

# Annotation text: label and rectangular form a+bi
rect = [f"{round(x, 2)}{'+' if y >= 0 else ''}{round(y, 2)}i" for x, y in zip(df[REAL], df[IMAGINARY], strict=True)]
notes = pd.DataFrame({"text": df[LABEL] + " = " + pd.Series(rect), "category": df[CATEGORY]})

# Label positions: pushed away from the origin by quadrant; points hugging the real axis go
# below it. Text is centred on its anchor, so a label beside its point is shifted by half its width.
half_width = 0.026 * notes["text"].str.len()
near_axis = (df[IMAGINARY].abs() < 0.6).to_numpy()
side_y = np.where(df[IMAGINARY] >= 0, 1.0, -1.0)
side_y[near_axis] = -1.0
side_x = np.where(df[REAL] >= 0, 1.0, -1.0)
unit_x = df[REAL] / np.hypot(df[REAL], df[IMAGINARY])
unit_y = df[IMAGINARY] / np.hypot(df[REAL], df[IMAGINARY])
# Away from the origin along each vector, so a label never sits on its own arrow
radial_x = df[REAL] + unit_x * (0.12 + half_width * unit_x.abs())
radial_y = df[IMAGINARY] + unit_y * 0.3
notes["x"] = np.clip(np.where(near_axis, df[REAL], radial_x), -axis_limit + half_width, axis_limit - half_width)
notes["y"] = np.where(near_axis, df[IMAGINARY] + side_y * 0.38, radial_y)

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

# Arrowheads: pulled slightly back toward the origin so each tip ends at its point
magnitude = np.hypot(df[REAL], df[IMAGINARY])
back = 0.08 / magnitude
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
    arc_label_df = pd.DataFrame(
        {"x": [arc_r * np.cos(mid) - 0.15], "y": [arc_r * np.sin(mid) + 0.16], "text": [turn_text]}
    )
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
    .mark_point(shape="triangle-up", filled=True, size=300)
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
    alt.layer(axes, unit_circle, *layers_extra, vectors, arrowheads, points, annotations, axis_labels)
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
