""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import Resources


# Data - Transfer function: G(s) = 1 / (s(s+1)(s+3))
# Open-loop poles at s = 0, -1, -3; no zeros
open_loop_poles = np.array([0.0, -1.0, -3.0])

# Characteristic equation: s^3 + 4s^2 + 3s + K = 0
# Compute root locus by solving for poles at each gain K
gains = np.concatenate(
    [np.linspace(0, 0.5, 200), np.linspace(0.5, 5, 600), np.linspace(5, 20, 600), np.linspace(20, 80, 600)]
)

# Coefficients: s^3 + 4s^2 + 3s + K
all_roots = np.zeros((len(gains), 3), dtype=complex)
for i, k in enumerate(gains):
    coeffs = [1, 4, 3, k]
    all_roots[i] = np.sort_complex(np.roots(coeffs))

# Organize into branches by tracking continuity
n_branches = 3
branch_real = []
branch_imag = []
branch_gain = []
branch_id = []

for b in range(n_branches):
    reals = all_roots[:, b].real
    imags = all_roots[:, b].imag
    branch_real.extend(reals)
    branch_imag.extend(imags)
    branch_gain.extend(gains)
    branch_id.extend([f"Branch {b + 1}"] * len(gains))

branch_real = np.array(branch_real)
branch_imag = np.array(branch_imag)
branch_gain = np.array(branch_gain)

# Colors
branch_colors = ["#306998", "#E07B39", "#E07B39"]
colors = []
for b in range(n_branches):
    colors.extend([branch_colors[b]] * len(gains))

source = ColumnDataSource(
    data={"real": branch_real, "imag": branch_imag, "gain": branch_gain, "branch": branch_id, "color": colors}
)

# Open-loop poles source
pole_source = ColumnDataSource(data={"real": open_loop_poles, "imag": np.zeros_like(open_loop_poles)})

# Imaginary axis crossings (stability boundary)
# For s^3 + 4s^2 + 3s + K = 0 via Routh criterion: K_critical = 12, w = sqrt(3)
w_crit = np.sqrt(3)
crossing_source = ColumnDataSource(data={"real": [0.0, 0.0], "imag": [w_crit, -w_crit]})

# Breakaway point: derivative of K = -(s^3 + 4s^2 + 3s) → 3s^2 + 8s + 3 = 0
# s = (-8 ± sqrt(64-36)) / 6 → s ≈ -0.451 (on real axis between -1 and 0)
breakaway_s = (-8 + np.sqrt(28)) / 6
breakaway_K = -(breakaway_s**3 + 4 * breakaway_s**2 + 3 * breakaway_s)

# Plot
y_max = max(abs(branch_imag)) * 1.15
p = figure(
    width=4800,
    height=2700,
    title="root-locus-basic · bokeh · pyplots.ai",
    x_axis_label="Real Axis (σ)",
    y_axis_label="Imaginary Axis (jω)",
    x_range=Range1d(-5.5, 1.5),
    y_range=Range1d(-y_max, y_max),
    tools="pan,wheel_zoom,box_zoom,reset,save",
    active_scroll="wheel_zoom",
    match_aspect=True,
)

# Constant damping ratio lines (radial lines from origin into left half-plane)
for zeta in [0.2, 0.4, 0.6, 0.8]:
    r_max = 5.0
    x_end = -r_max * zeta
    y_end = r_max * np.sqrt(1 - zeta**2)
    p.line(x=[0, x_end], y=[0, y_end], line_color="#B0B0B0", line_width=1.5, line_alpha=0.3, line_dash="dotted")
    p.line(x=[0, x_end], y=[0, -y_end], line_color="#B0B0B0", line_width=1.5, line_alpha=0.3, line_dash="dotted")
    label_r = 4.5
    lx = -label_r * zeta
    ly = label_r * np.sqrt(1 - zeta**2)
    p.add_layout(
        Label(
            x=lx,
            y=ly + 0.15,
            text=f"ζ={zeta}",
            text_font_size="24pt",
            text_color="#999999",
            text_alpha=0.6,
            text_font="Helvetica",
        )
    )

# Constant natural frequency arcs (semicircles)
for wn in [1, 2, 3, 4]:
    theta = np.linspace(np.pi / 2, np.pi, 60)
    arc_x = wn * np.cos(theta)
    arc_y = wn * np.sin(theta)
    p.line(
        x=arc_x.tolist(), y=arc_y.tolist(), line_color="#B0B0B0", line_width=1.5, line_alpha=0.25, line_dash="dotted"
    )
    p.line(
        x=arc_x.tolist(), y=(-arc_y).tolist(), line_color="#B0B0B0", line_width=1.5, line_alpha=0.25, line_dash="dotted"
    )
    p.add_layout(
        Label(
            x=-0.15,
            y=wn + 0.15,
            text=f"ωn={wn}",
            text_font_size="22pt",
            text_color="#999999",
            text_alpha=0.6,
            text_font="Helvetica",
        )
    )

# Real axis segments of root locus
# Poles at 0, -1, -3 → segments: [-1, 0] and [-∞, -3]
p.segment(
    x0=[-1], y0=[0], x1=[0], y1=[0], line_color="#306998", line_width=6, line_alpha=0.35, legend_label="Real-axis locus"
)
p.segment(x0=[-5.5], y0=[0], x1=[-3], y1=[0], line_color="#306998", line_width=6, line_alpha=0.35)

# Locus branches
scatter = p.scatter(
    x="real",
    y="imag",
    source=source,
    size=6,
    color="color",
    alpha=0.7,
    line_color=None,
    legend_label="Complex branches",
)

# Open-loop poles (× markers)
p.scatter(
    x="real",
    y="imag",
    source=pole_source,
    size=45,
    marker="x",
    color="#2B2B2B",
    line_width=5,
    legend_label="Open-loop poles",
)

# Imaginary axis crossings (stability boundary markers)
p.scatter(
    x="real",
    y="imag",
    source=crossing_source,
    size=35,
    marker="diamond",
    color="#E74C3C",
    line_color="white",
    line_width=3,
    legend_label="Stability crossing (K=12)",
)

# Breakaway point marker
p.scatter(
    x=[breakaway_s],
    y=[0],
    size=30,
    marker="square",
    color="#306998",
    line_color="white",
    line_width=3,
    legend_label=f"Breakaway (K={breakaway_K:.2f})",
)

# Stability boundary - imaginary axis
stability_line = Span(
    location=0, dimension="height", line_color="#E74C3C", line_width=2.5, line_alpha=0.2, line_dash="dashed"
)
p.add_layout(stability_line)

# Direction arrows on branches indicating increasing gain
for b in range(n_branches):
    arrow_idx = len(gains) * 2 // 3
    r = all_roots[arrow_idx, b]
    r_next = all_roots[min(arrow_idx + 20, len(gains) - 1), b]
    dx = r_next.real - r.real
    dy = r_next.imag - r.imag
    length = np.sqrt(dx**2 + dy**2)
    if length > 0.01:
        p.scatter(
            x=[r.real],
            y=[r.imag],
            size=28,
            marker="triangle",
            color=branch_colors[b],
            angle=[np.arctan2(dy, dx) - np.pi / 2],
            alpha=0.9,
        )

# Annotations at key engineering points
p.add_layout(
    Label(
        x=0.2,
        y=w_crit + 0.25,
        text=f"jω-crossing: K={12}, ω=√3≈{w_crit:.2f}",
        text_font_size="28pt",
        text_color="#E74C3C",
        text_font="Helvetica",
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=breakaway_s + 0.05,
        y=-0.45,
        text=f"Breakaway: σ={breakaway_s:.3f}, K={breakaway_K:.2f}",
        text_font_size="26pt",
        text_color="#306998",
        text_font="Helvetica",
        text_font_style="bold",
    )
)

# Asymptote annotation
# Asymptote angles: (2k+1)*180/n for n=3 poles, 0 zeros → 60°, 180°, 300°
# Centroid: (-0 -1 -3) / 3 = -4/3
centroid = sum(open_loop_poles) / len(open_loop_poles)
p.add_layout(
    Label(
        x=centroid - 0.05,
        y=0.35,
        text=f"Centroid σ={centroid:.2f}",
        text_font_size="24pt",
        text_color="#555555",
        text_font="Helvetica",
        text_font_style="italic",
    )
)
p.scatter(x=[centroid], y=[0], size=18, marker="circle", color="#555555", line_color="white", line_width=2, alpha=0.7)

# HoverTool
hover = HoverTool(
    renderers=[scatter],
    tooltips=[("Pole", "@real{0.00} + @imag{0.00}j"), ("Gain K", "@gain{0.00}"), ("Branch", "@branch")],
    point_policy="snap_to_data",
    mode="mouse",
)
p.add_tools(hover)

# Style
p.title.text_font_size = "72pt"
p.title.text_color = "#2B2B2B"
p.title.text_font = "Helvetica"

p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.axis_label_text_font = "Helvetica"
p.yaxis.axis_label_text_font = "Helvetica"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = "#3A3A3A"
p.yaxis.axis_label_text_color = "#3A3A3A"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.grid_line_alpha = 0.12
p.grid.grid_line_width = 1.5
p.grid.grid_line_color = "#AAAAAA"

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = None

p.xaxis.ticker.desired_num_ticks = 10
p.yaxis.ticker.desired_num_ticks = 10

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "28pt"
p.legend.label_text_font = "Helvetica"
p.legend.label_text_color = "#3A3A3A"
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "white"
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_width = 2
p.legend.glyph_width = 40
p.legend.glyph_height = 40
p.legend.spacing = 8
p.legend.padding = 15
p.legend.margin = 20

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Root Locus Plot")
