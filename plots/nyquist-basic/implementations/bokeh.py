"""pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import Resources


# Data - Transfer function: G(s) = 50 / (s+1)(s+2)(s+5)
# Third-order system near stability boundary for an interesting Nyquist shape
poles = np.array([-1.0, -2.0, -5.0])
gain_k = 50.0

# Frequency sweep: logarithmically spaced from very low to very high
freq = np.concatenate(
    [np.logspace(-3, -1, 100), np.logspace(-1, 0.5, 300), np.logspace(0.5, 1.5, 200), np.logspace(1.5, 3, 100)]
)

# Compute G(jw) = K / ((jw + p1)(jw + p2)(jw + p3))
jw = 1j * freq
G = gain_k / np.prod(np.array([jw - p for p in poles]), axis=0)

real_part = G.real
imag_part = G.imag

# Mirror for negative frequencies (Nyquist contour)
real_mirror = real_part[::-1]
imag_mirror = -imag_part[::-1]

# Find gain crossover (|G(jw)| = 1) and phase crossover (Im(G) = 0, Re(G) < 0)
magnitude = np.abs(G)
phase_deg = np.degrees(np.arctan2(imag_part, real_part))

# Gain crossover: magnitude crosses 1
gain_cross_idx = None
for i in range(len(magnitude) - 1):
    if (magnitude[i] - 1) * (magnitude[i + 1] - 1) < 0:
        gain_cross_idx = i
        break

# Phase crossover: imaginary part crosses zero while real < 0
phase_cross_idx = None
for i in range(1, len(imag_part) - 1):
    if imag_part[i] * imag_part[i + 1] < 0 and real_part[i] < 0:
        phase_cross_idx = i
        break

# Compute gain margin and phase margin for storytelling
gain_margin_db = None
phase_margin_deg = None
if phase_cross_idx is not None:
    gain_margin_val = -1.0 / real_part[phase_cross_idx]
    gain_margin_db = 20 * np.log10(gain_margin_val)
if gain_cross_idx is not None:
    phase_margin_deg = 180 + phase_deg[gain_cross_idx]

# Source for positive frequencies
source_pos = ColumnDataSource(
    data={"real": real_part, "imag": imag_part, "freq": freq, "mag": magnitude, "phase": phase_deg}
)

# Source for negative frequencies (mirror)
source_neg = ColumnDataSource(
    data={
        "real": real_mirror,
        "imag": imag_mirror,
        "freq": -freq[::-1],
        "mag": magnitude[::-1],
        "phase": -phase_deg[::-1],
    }
)

# Unit circle
theta_circle = np.linspace(0, 2 * np.pi, 200)
unit_x = np.cos(theta_circle)
unit_y = np.sin(theta_circle)

# Color palette - refined, cohesive scheme
COLOR_POS = "#1B6CA8"
COLOR_NEG = "#C4722A"
COLOR_CRITICAL = "#C0392B"
COLOR_UNIT_CIRCLE = "#7F8C8D"
COLOR_ANNOTATION = "#2C3E50"
COLOR_GAIN_MARGIN = "#27AE60"
COLOR_PHASE_MARGIN = "#8E44AD"

# Plot
x_min = min(real_part.min(), -1.5) * 1.2
x_max = max(real_part.max(), 1.0) * 1.15
y_ext = max(abs(imag_part).max(), 1.2) * 1.2

p = figure(
    width=3600,
    height=3600,
    title="nyquist-basic · bokeh · pyplots.ai",
    x_axis_label="Real",
    y_axis_label="Imaginary",
    x_range=Range1d(x_min, x_max),
    y_range=Range1d(-y_ext, y_ext),
    tools="pan,wheel_zoom,box_zoom,reset,save",
    active_scroll="wheel_zoom",
    match_aspect=True,
)

# Unit circle (reference) - more prominent
p.line(
    x=unit_x.tolist(),
    y=unit_y.tolist(),
    line_color=COLOR_UNIT_CIRCLE,
    line_width=3,
    line_dash="dashed",
    line_alpha=0.6,
    legend_label="Unit circle",
)

# Axes through origin
origin_h = Span(location=0, dimension="width", line_color="#AAAAAA", line_width=1.5, line_alpha=0.35)
origin_v = Span(location=0, dimension="height", line_color="#AAAAAA", line_width=1.5, line_alpha=0.35)
p.add_layout(origin_h)
p.add_layout(origin_v)

# Gain margin visualization: line from phase crossover to critical point
if phase_cross_idx is not None:
    gm_source = ColumnDataSource(data={"x": [real_part[phase_cross_idx], -1.0], "y": [0.0, 0.0]})
    p.line(
        x="x", y="y", source=gm_source, line_color=COLOR_GAIN_MARGIN, line_width=4, line_dash="dotted", line_alpha=0.8
    )

# Nyquist curve - positive frequencies
line_pos = p.line(
    x="real", y="imag", source=source_pos, line_color=COLOR_POS, line_width=4.5, line_alpha=0.95, legend_label="ω > 0"
)

# Nyquist curve - negative frequencies (mirror)
line_neg = p.line(
    x="real",
    y="imag",
    source=source_neg,
    line_color=COLOR_NEG,
    line_width=3,
    line_dash="dashed",
    line_alpha=0.6,
    legend_label="ω < 0",
)

# Critical point (-1, 0)
p.scatter(x=[-1], y=[0], size=44, marker="x", color=COLOR_CRITICAL, line_width=7, legend_label="Critical point (-1, 0)")

# Direction arrows on the positive frequency curve
arrow_indices = [len(freq) // 6, len(freq) // 3, len(freq) * 2 // 3]
for idx in arrow_indices:
    if idx < len(freq) - 5:
        dx = real_part[idx + 5] - real_part[idx]
        dy = imag_part[idx + 5] - imag_part[idx]
        angle = np.arctan2(dy, dx) - np.pi / 2
        p.scatter(
            x=[real_part[idx]],
            y=[imag_part[idx]],
            size=26,
            marker="triangle",
            color=COLOR_POS,
            angle=[angle],
            alpha=0.9,
        )

# Direction arrows on the negative frequency curve (mirrored)
mirror_indices = [len(freq) // 6, len(freq) // 3, len(freq) * 2 // 3]
for idx in mirror_indices:
    ridx = len(freq) - 1 - idx
    if ridx > 5:
        dx = (
            real_mirror[len(freq) - 1 - idx + 5] - real_mirror[len(freq) - 1 - idx]
            if len(freq) - 1 - idx + 5 < len(real_mirror)
            else 0
        )
        dy = (
            imag_mirror[len(freq) - 1 - idx + 5] - imag_mirror[len(freq) - 1 - idx]
            if len(freq) - 1 - idx + 5 < len(imag_mirror)
            else 0
        )
        if abs(dx) + abs(dy) > 1e-8:
            angle = np.arctan2(dy, dx) - np.pi / 2
            p.scatter(
                x=[real_mirror[len(freq) - 1 - idx]],
                y=[imag_mirror[len(freq) - 1 - idx]],
                size=22,
                marker="triangle",
                color=COLOR_NEG,
                angle=[angle],
                alpha=0.65,
            )

# Annotate gain crossover frequency - positioned away from origin
if gain_cross_idx is not None:
    gc_freq = freq[gain_cross_idx]
    p.scatter(
        x=[real_part[gain_cross_idx]],
        y=[imag_part[gain_cross_idx]],
        size=32,
        marker="circle",
        color=COLOR_POS,
        line_color="white",
        line_width=3,
    )
    pm_text = f"  PM = {phase_margin_deg:.1f}°" if phase_margin_deg is not None else ""
    p.add_layout(
        Label(
            x=real_part[gain_cross_idx] + 0.15,
            y=imag_part[gain_cross_idx] - 0.35,
            text=f"Gain crossover ω={gc_freq:.2f} rad/s{pm_text}",
            text_font_size="26pt",
            text_color=COLOR_POS,
            text_font="Helvetica",
            text_font_style="bold",
        )
    )

# Annotate phase crossover frequency - positioned clearly above with offset
if phase_cross_idx is not None:
    pc_freq = freq[phase_cross_idx]
    p.scatter(
        x=[real_part[phase_cross_idx]],
        y=[imag_part[phase_cross_idx]],
        size=32,
        marker="diamond",
        color=COLOR_CRITICAL,
        line_color="white",
        line_width=3,
    )
    gm_text = f"  GM = {gain_margin_db:.1f} dB" if gain_margin_db is not None else ""
    p.add_layout(
        Label(
            x=real_part[phase_cross_idx] - 0.15,
            y=imag_part[phase_cross_idx] + 0.25,
            text=f"Phase crossover ω={pc_freq:.2f}{gm_text}",
            text_font_size="26pt",
            text_color=COLOR_CRITICAL,
            text_font="Helvetica",
            text_font_style="bold",
        )
    )

# Label at low frequency start
p.add_layout(
    Label(
        x=real_part[0] + 0.05,
        y=imag_part[0] - 0.15,
        text="ω → 0",
        text_font_size="28pt",
        text_color=COLOR_ANNOTATION,
        text_font="Helvetica",
        text_font_style="italic",
    )
)

# Label at high frequency end - offset to avoid overlap with phase crossover
p.add_layout(
    Label(
        x=real_part[-1] + 0.08,
        y=imag_part[-1] - 0.20,
        text="ω → ∞",
        text_font_size="28pt",
        text_color=COLOR_ANNOTATION,
        text_font="Helvetica",
        text_font_style="italic",
    )
)

# HoverTool for positive frequency curve
hover = HoverTool(
    renderers=[line_pos],
    tooltips=[
        ("ω", "@freq{0.000} rad/s"),
        ("G(jω)", "@real{0.000} + @imag{0.000}j"),
        ("|G(jω)|", "@mag{0.000}"),
        ("Phase", "@phase{0.0}°"),
    ],
    point_policy="snap_to_data",
    mode="mouse",
)
p.add_tools(hover)

# Style
p.title.text_font_size = "60pt"
p.title.text_color = "#1A1A2E"
p.title.text_font = "Helvetica"
p.title.offset = 10

p.xaxis.axis_label_text_font_size = "44pt"
p.yaxis.axis_label_text_font_size = "44pt"
p.xaxis.axis_label_text_font = "Helvetica"
p.yaxis.axis_label_text_font = "Helvetica"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "32pt"
p.yaxis.major_label_text_font_size = "32pt"
p.xaxis.axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_color = "#2C3E50"
p.xaxis.major_label_text_color = "#566573"
p.yaxis.major_label_text_color = "#566573"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.grid_line_alpha = 0.10
p.grid.grid_line_width = 1
p.grid.grid_line_color = "#95A5A6"

p.background_fill_color = "#F8F9FA"
p.border_fill_color = "white"
p.outline_line_color = None

# Legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "28pt"
p.legend.label_text_font = "Helvetica"
p.legend.label_text_color = "#2C3E50"
p.legend.background_fill_alpha = 0.9
p.legend.background_fill_color = "#FFFFFF"
p.legend.border_line_color = "#D5D8DC"
p.legend.border_line_width = 1.5
p.legend.glyph_width = 44
p.legend.glyph_height = 44
p.legend.spacing = 10
p.legend.padding = 18
p.legend.margin = 25

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Nyquist Plot")
