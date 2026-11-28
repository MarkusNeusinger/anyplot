"""anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: altair 6.3.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-28
"""

import os
import sys


# altair.py shadows the altair package — remove this directory from sys.path first
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) != os.path.realpath(_here)]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (Imprint style guide)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette positions used
BRAND = "#009E73"  # pos 1 — stress state points + circle line
LAVENDER = "#C475FD"  # pos 2 — max shear points
BLUE = "#4467A3"  # pos 3 — principal stresses + 2θp arc

# Columns: set these to your table's column names
SIGMA_X = "sigma_x (MPa)"  # role: sigma_x
SIGMA_Y = "sigma_y (MPa)"  # role: sigma_y
TAU_XY = "tau_xy (MPa)"  # role: tau_xy

# Data: replace this one-row table with your own stress state, for example df = pd.read_csv("stress.csv")
df = pd.DataFrame({SIGMA_X: [80], SIGMA_Y: [-40], TAU_XY: [30]})

# Plot: everything below derives from the stress state in df
sigma_x, sigma_y, tau_xy = (df[c].iloc[0] for c in (SIGMA_X, SIGMA_Y, TAU_XY))
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
theta_p2 = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Circle outline (parametric)
angles = np.linspace(0, 2 * np.pi, 361)
circle_df = pd.DataFrame(
    {"sigma": center + radius * np.cos(angles), "tau": radius * np.sin(angles), "order": range(len(angles))}
)

# Key stress points; dx/dy are label offsets in screen pixels
stress_points = pd.DataFrame(
    [
        {
            "sigma": sigma_x,
            "tau": tau_xy,
            "label": f"A ({sigma_x}, {tau_xy})",
            "type": "Stress State",
            "dx": 14,
            "dy": -14,
        },
        {
            "sigma": sigma_y,
            "tau": -tau_xy,
            "label": f"B ({sigma_y}, {-tau_xy})",
            "type": "Stress State",
            "dx": -18,
            "dy": 14,
        },
        {"sigma": sigma_1, "tau": 0, "label": f"σ₁ = {sigma_1:.1f} MPa", "type": "Principal", "dx": -16, "dy": 20},
        {"sigma": sigma_2, "tau": 0, "label": f"σ₂ = {sigma_2:.1f} MPa", "type": "Principal", "dx": 16, "dy": 20},
        {
            "sigma": center,
            "tau": tau_max,
            "label": f"τmax = {tau_max:.1f} MPa",
            "type": "Max Shear",
            "dx": 12,
            "dy": -14,
        },
        {
            "sigma": center,
            "tau": -tau_max,
            "label": f"−τmax = −{tau_max:.1f} MPa",
            "type": "Max Shear",
            "dx": 12,
            "dy": 18,
        },
    ]
)

# Diameter line A → B
diameter_df = pd.DataFrame({"sigma": [sigma_x, sigma_y], "tau": [tau_xy, -tau_xy]})

# 2θp angle arc
arc_r = radius * 0.25
arc_angles = np.linspace(0, np.radians(theta_p2), 50)
arc_df = pd.DataFrame(
    {"sigma": center + arc_r * np.cos(arc_angles), "tau": arc_r * np.sin(arc_angles), "order": range(len(arc_angles))}
)

# Equal-aspect domains: same data span on both axes in a square view, so the circle stays round
span = max(sigma_1 - sigma_2, 2 * tau_max) * 1.25
x_scale = alt.Scale(domain=[center - span / 2, center + span / 2], nice=False)
# The fit layout leaves the view about 5 % wider than tall (axis titles and ticks take height), so the shear span shrinks by that ratio
VIEW_ASPECT = 0.947
y_scale = alt.Scale(domain=[-span / 2 * VIEW_ASPECT, span / 2 * VIEW_ASPECT], nice=False)

# Reference lines through center
h_rule = (
    alt.Chart(pd.DataFrame({"tau": [0]}))
    .mark_rule(color=INK_SOFT, strokeWidth=1, opacity=0.5)
    .encode(y=alt.Y("tau:Q", scale=y_scale))
)
v_rule = (
    alt.Chart(pd.DataFrame({"sigma": [center]}))
    .mark_rule(color=INK_SOFT, strokeWidth=1, opacity=0.4, strokeDash=[6, 4])
    .encode(x=alt.X("sigma:Q", scale=x_scale))
)

# Circle
circle = (
    alt.Chart(circle_df)
    .mark_line(color=BRAND, strokeWidth=2.5)
    .encode(
        x=alt.X("sigma:Q", title="Normal Stress σ (MPa)", scale=x_scale),
        y=alt.Y("tau:Q", title="Shear Stress τ (MPa)", scale=y_scale),
        order="order:Q",
    )
)

# Diameter line
diameter = (
    alt.Chart(diameter_df)
    .mark_line(color=BRAND, strokeWidth=1.5, strokeDash=[8, 5], opacity=0.5)
    .encode(x="sigma:Q", y="tau:Q")
)

# 2θp arc — linked to principal plane rotation
arc = alt.Chart(arc_df).mark_line(color=BLUE, strokeWidth=2.5).encode(x="sigma:Q", y="tau:Q", order="order:Q")

# Angle label
angle_lbl_df = pd.DataFrame(
    {
        "sigma": [center + arc_r * 2.2 * np.cos(np.radians(theta_p2 / 2))],
        "tau": [arc_r * 2.2 * np.sin(np.radians(theta_p2 / 2))],
    }
)
angle_lbl = (
    alt.Chart(angle_lbl_df)
    .mark_text(text=f"2θp = {theta_p2:.1f}°", fontSize=11, fontWeight="bold", color=INK)
    .encode(x="sigma:Q", y="tau:Q")
)

# Interactive hover selection (enhances HTML output)
highlight = alt.selection_point(fields=["type"], on="pointerover")

# Stress points with Imprint palette colors and hover interaction
points = (
    alt.Chart(stress_points)
    .mark_point(filled=True, strokeWidth=2, stroke=PAGE_BG)
    .encode(
        x="sigma:Q",
        y="tau:Q",
        color=alt.Color(
            "type:N",
            scale=alt.Scale(domain=["Stress State", "Principal", "Max Shear"], range=[BRAND, BLUE, LAVENDER]),
            legend=alt.Legend(
                title=None,
                orient="bottom-right",
                direction="vertical",
                symbolSize=180,
                symbolStrokeWidth=0,
                labelFontSize=10,
                padding=8,
                offset=8,
                cornerRadius=4,
            ),
        ),
        size=alt.condition(highlight, alt.value(420), alt.value(300)),
        opacity=alt.condition(highlight, alt.value(1.0), alt.value(0.85)),
        tooltip=[
            alt.Tooltip("label:N", title="Point"),
            alt.Tooltip("sigma:Q", title="σ (MPa)", format=".1f"),
            alt.Tooltip("tau:Q", title="τ (MPa)", format=".1f"),
            alt.Tooltip("type:N", title="Category"),
        ],
    )
    .add_params(highlight)
)

# Center point
center_pt_df = pd.DataFrame({"sigma": [center], "tau": [0]})
center_pt = (
    alt.Chart(center_pt_df)
    .mark_point(size=180, filled=True, color=INK_MUTED, strokeWidth=2, stroke=PAGE_BG)
    .encode(x="sigma:Q", y="tau:Q")
)
center_lbl = (
    alt.Chart(center_pt_df)
    .mark_text(text=f"C ({center:.0f}, 0)", fontSize=10, color=INK_SOFT, align="left", dx=8, dy=18)
    .encode(x="sigma:Q", y="tau:Q")
)

# Annotation labels, one text layer per point so each gets its own pixel offset
labels = [
    alt.Chart(pd.DataFrame([row]))
    .mark_text(
        fontSize=11,
        fontWeight="bold",
        color=INK,
        dx=row["dx"],
        dy=row["dy"],
        align="left" if row["dx"] > 0 else "right",
    )
    .encode(x="sigma:Q", y="tau:Q", text="label:N")
    for row in stress_points.to_dict("records")
]

# Title and subtitle
title_text = "mohr-circle · python · altair · anyplot.ai"
subtitle_text = f"2D Stress Transformation — σx={sigma_x}, σy={sigma_y}, τxy={tau_xy} MPa"

# Compose chart; the fit autosize makes the view square, so the circle stays round
chart = (
    alt.layer(h_rule, v_rule, circle, diameter, arc, points, center_pt, *labels, center_lbl, angle_lbl)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            title_text,
            fontSize=16,
            fontWeight="bold",
            color=INK,
            subtitle=subtitle_text,
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleColor=INK,
        labelColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=True,
        gridOpacity=0.12,
        tickMinStep=20,
        gridColor=INK,
        domain=False,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
    .configure_title(color=INK)
)

# Save: 600×600 fit chart × scale 4 = 2400×2400; pad with PAGE_BG if short, never crop
TW, TH = 2400, 2400
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
