""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-02-27
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure


# Data — typical combined loading stress state
sigma_x = 80  # MPa (tensile)
sigma_y = -30  # MPa (compressive)
tau_xy = 40  # MPa

# Mohr's circle parameters
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius  # major principal stress
sigma_2 = center - radius  # minor principal stress
tau_max = radius
theta_p = 0.5 * np.arctan2(2 * tau_xy, sigma_x - sigma_y)  # principal angle
theta_p_deg = np.degrees(theta_p)

# Circle points
theta = np.linspace(0, 2 * np.pi, 300)
circle_x = center + radius * np.cos(theta)
circle_y = radius * np.sin(theta)

# Stress points on the circle
ax_pt = (sigma_x, tau_xy)  # Point A
bx_pt = (sigma_y, -tau_xy)  # Point B

# Data sources for interactive features
principal_source = ColumnDataSource(
    data={
        "x": [sigma_1, sigma_2],
        "y": [0, 0],
        "label": ["σ₁ (Major Principal)", "σ₂ (Minor Principal)"],
        "sigma": [f"{sigma_1:.1f}", f"{sigma_2:.1f}"],
        "tau": ["0.0", "0.0"],
    }
)

shear_source = ColumnDataSource(
    data={
        "x": [center, center],
        "y": [tau_max, -tau_max],
        "label": ["τ_max (Top)", "τ_max (Bottom)"],
        "sigma": [f"{center:.1f}", f"{center:.1f}"],
        "tau": [f"{tau_max:.1f}", f"{-tau_max:.1f}"],
    }
)

stress_source = ColumnDataSource(
    data={
        "x": [ax_pt[0], bx_pt[0]],
        "y": [ax_pt[1], bx_pt[1]],
        "label": ["Point A (σx, τxy)", "Point B (σy, -τxy)"],
        "sigma": [f"{ax_pt[0]:.1f}", f"{bx_pt[0]:.1f}"],
        "tau": [f"{ax_pt[1]:.1f}", f"{bx_pt[1]:.1f}"],
    }
)

# Plot
padding = radius * 0.55
p = figure(
    width=3600,
    height=3600,
    title="Mohr's Circle for Stress Analysis · mohr-circle · bokeh · pyplots.ai",
    x_axis_label="Normal Stress σ (MPa)",
    y_axis_label="Shear Stress τ (MPa)",
    x_range=(sigma_2 - padding, sigma_1 + padding),
    y_range=(-tau_max - padding, tau_max + padding),
    match_aspect=True,
    toolbar_location="right",
    tools="",
)

# Reference lines through the center
center_h = Span(location=0, dimension="width", line_color="#AAAAAA", line_width=2, line_alpha=0.6)
center_v = Span(
    location=center, dimension="height", line_color="#AAAAAA", line_width=2, line_alpha=0.6, line_dash="dashed"
)
p.add_layout(center_h)
p.add_layout(center_v)

# Mohr's circle
p.line(circle_x, circle_y, line_color="#306998", line_width=4, line_alpha=0.9)

# Line connecting A and B through center (diameter)
p.line(
    [ax_pt[0], bx_pt[0]], [ax_pt[1], bx_pt[1]], line_color="#555555", line_width=2, line_dash="dashed", line_alpha=0.6
)

# Principal stresses on horizontal axis
principal_r = p.scatter(
    "x", "y", source=principal_source, size=22, color="#E74C3C", marker="diamond", line_color="white", line_width=2
)

# Maximum shear stress at top and bottom (colorblind-safe orange)
shear_r = p.scatter(
    "x", "y", source=shear_source, size=22, color="#E67E22", marker="triangle", line_color="white", line_width=2
)

# Stress points A and B
stress_r = p.scatter("x", "y", source=stress_source, size=24, color="#306998", line_color="white", line_width=2)

# HoverTool for interactive stress readouts
hover = HoverTool(
    renderers=[principal_r, shear_r, stress_r],
    tooltips=[("Point", "@label"), ("σ (MPa)", "@sigma"), ("τ (MPa)", "@tau")],
    mode="mouse",
)
p.add_tools(hover)

# Angle arc for 2θp from point A to σ1 axis
angle_2tp = np.arctan2(tau_xy, sigma_x - center)  # angle from center to point A
arc_radius = radius * 0.35
arc_angles = np.linspace(0, angle_2tp, 60)
arc_x = center + arc_radius * np.cos(arc_angles)
arc_y = arc_radius * np.sin(arc_angles)
p.line(arc_x, arc_y, line_color="#E74C3C", line_width=3, line_alpha=0.8)

# Annotations
offset_lg = radius * 0.08

p.add_layout(
    Label(
        x=sigma_1,
        y=offset_lg * 1.5,
        text=f"σ₁ = {sigma_1:.1f} MPa",
        text_font_size="22pt",
        text_color="#E74C3C",
        text_align="center",
    )
)
p.add_layout(
    Label(
        x=sigma_2,
        y=offset_lg * 1.5,
        text=f"σ₂ = {sigma_2:.1f} MPa",
        text_font_size="22pt",
        text_color="#E74C3C",
        text_align="center",
    )
)

p.add_layout(
    Label(
        x=center + offset_lg,
        y=tau_max + offset_lg * 0.5,
        text=f"τ_max = {tau_max:.1f} MPa",
        text_font_size="20pt",
        text_color="#E67E22",
    )
)
p.add_layout(
    Label(
        x=center + offset_lg,
        y=-tau_max - offset_lg * 0.5,
        text=f"τ_max = {tau_max:.1f} MPa",
        text_font_size="20pt",
        text_color="#E67E22",
        text_baseline="top",
    )
)

p.add_layout(
    Label(
        x=ax_pt[0] + offset_lg,
        y=ax_pt[1] + offset_lg * 0.5,
        text=f"A ({sigma_x}, {tau_xy})",
        text_font_size="20pt",
        text_color="#306998",
    )
)
p.add_layout(
    Label(
        x=bx_pt[0] - offset_lg,
        y=bx_pt[1] - offset_lg * 0.5,
        text=f"B ({sigma_y}, {-tau_xy})",
        text_font_size="20pt",
        text_color="#306998",
        text_align="right",
        text_baseline="top",
    )
)

p.add_layout(
    Label(
        x=center,
        y=-padding * 0.85,
        text=f"Center = ({center:.1f}, 0)  |  R = {radius:.1f} MPa",
        text_font_size="20pt",
        text_color="#555555",
        text_align="center",
    )
)

# 2θp angle label
arc_mid_angle = angle_2tp / 2
label_r = arc_radius * 1.3
p.add_layout(
    Label(
        x=center + label_r * np.cos(arc_mid_angle),
        y=label_r * np.sin(arc_mid_angle),
        text=f"2θp = {2 * theta_p_deg:.1f}°",
        text_font_size="20pt",
        text_color="#E74C3C",
    )
)

# Style
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.background_fill_color = "#FFFFFF"

p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Save HTML with interactive features (toolbar visible for hover)
output_file("plot.html")
save(p)

# Save PNG without toolbar
p.toolbar_location = None
export_png(p, filename="plot.png")
