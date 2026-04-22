""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.layouts import column
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Third-order open-loop transfer function:
# H(s) = K / (s * (s/w1 + 1) * (s/w2 + 1))
# Classic control system with integrator + two real poles
K = 100
w1 = 2 * np.pi * 5  # Pole at 5 Hz
w2 = 2 * np.pi * 50  # Pole at 50 Hz

frequency_hz = np.logspace(-1, 3, 500)
omega = 2 * np.pi * frequency_hz
s = 1j * omega

H = K / (s * (s / w1 + 1) * (s / w2 + 1))
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.degrees(np.unwrap(np.angle(H)))

# Gain crossover: where magnitude crosses 0 dB
sign_changes = np.diff(np.sign(magnitude_db))
gc_indices = np.where(sign_changes != 0)[0]
gain_cross_idx = gc_indices[0] if len(gc_indices) > 0 else np.argmin(np.abs(magnitude_db))
gain_cross_freq = frequency_hz[gain_cross_idx]
phase_at_gain_cross = phase_deg[gain_cross_idx]
phase_margin = 180 + phase_at_gain_cross

# Phase crossover: where phase crosses -180 degrees
phase_shifted = phase_deg + 180
sign_changes_phase = np.diff(np.sign(phase_shifted))
pc_indices = np.where(sign_changes_phase != 0)[0]
phase_cross_idx = pc_indices[0] if len(pc_indices) > 0 else np.argmin(np.abs(phase_deg + 180))
phase_cross_freq = frequency_hz[phase_cross_idx]
mag_at_phase_cross = magnitude_db[phase_cross_idx]
gain_margin = -mag_at_phase_cross

# Colors - colorblind-safe: Python Blue, Vermillion, Blue-Purple (Wong palette)
CURVE_COLOR = "#306998"
GM_COLOR = "#D55E00"  # Vermillion
PM_COLOR = "#7570B3"  # Blue-purple
REF_COLOR = "#555555"
BG_COLOR = "#FAFAFA"
AXIS_COLOR = "#444444"

source = ColumnDataSource(data={"frequency": frequency_hz, "magnitude": magnitude_db, "phase": phase_deg})

# Magnitude plot
p_mag = figure(
    width=4800,
    height=1350,
    x_axis_type="log",
    x_axis_label="",
    y_axis_label="Magnitude (dB)",
    title="bode-basic · bokeh · pyplots.ai",
    toolbar_location=None,
)

# Stability region shading (above 0 dB = high gain region)
p_mag.add_layout(BoxAnnotation(bottom=0, fill_color=CURVE_COLOR, fill_alpha=0.025))

p_mag.line("frequency", "magnitude", source=source, line_width=4, color=CURVE_COLOR)

# 0 dB reference line
p_mag.add_layout(
    Span(location=0, dimension="width", line_color=REF_COLOR, line_width=2, line_dash="dashed", line_alpha=0.7)
)
p_mag.add_layout(
    Label(
        x=0.12,
        y=1.5,
        text="0 dB",
        text_font_size="16pt",
        text_color=REF_COLOR,
        text_alpha=0.7,
        text_font_style="italic",
    )
)

# Gain margin annotation
p_mag.scatter([phase_cross_freq], [mag_at_phase_cross], size=16, color=GM_COLOR, marker="circle")
p_mag.scatter([phase_cross_freq], [0], size=16, color=GM_COLOR, marker="circle")
p_mag.segment(
    x0=[phase_cross_freq],
    y0=[mag_at_phase_cross],
    x1=[phase_cross_freq],
    y1=[0],
    line_width=3,
    color=GM_COLOR,
    line_dash="dotted",
)
p_mag.add_layout(
    Label(
        x=phase_cross_freq,
        y=mag_at_phase_cross / 2,
        text=f"GM = {gain_margin:.1f} dB",
        text_font_size="22pt",
        text_font_style="bold",
        text_color=GM_COLOR,
        x_offset=18,
    )
)

# Gain crossover marker on magnitude plot
p_mag.scatter([gain_cross_freq], [0], size=16, color=PM_COLOR, marker="circle")

# Phase plot
p_phase = figure(
    width=4800,
    height=1350,
    x_axis_type="log",
    x_axis_label="Frequency (Hz)",
    y_axis_label="Phase (°)",
    x_range=p_mag.x_range,
    toolbar_location=None,
)

# Instability region shading (below -180°)
p_phase.add_layout(BoxAnnotation(top=-180, fill_color=GM_COLOR, fill_alpha=0.025))

p_phase.line("frequency", "phase", source=source, line_width=4, color=CURVE_COLOR)

# -180° reference line
p_phase.add_layout(
    Span(location=-180, dimension="width", line_color=REF_COLOR, line_width=2, line_dash="dashed", line_alpha=0.7)
)
p_phase.add_layout(
    Label(
        x=0.12,
        y=-177,
        text="-180°",
        text_font_size="16pt",
        text_color=REF_COLOR,
        text_alpha=0.7,
        text_font_style="italic",
    )
)

# Phase margin annotation
p_phase.scatter([gain_cross_freq], [phase_at_gain_cross], size=16, color=PM_COLOR, marker="circle")
p_phase.scatter([gain_cross_freq], [-180], size=16, color=PM_COLOR, marker="circle")
p_phase.segment(
    x0=[gain_cross_freq],
    y0=[phase_at_gain_cross],
    x1=[gain_cross_freq],
    y1=[-180],
    line_width=3,
    color=PM_COLOR,
    line_dash="dotted",
)
p_phase.add_layout(
    Label(
        x=gain_cross_freq,
        y=(phase_at_gain_cross - 180) / 2,
        text=f"PM = {phase_margin:.1f}°",
        text_font_size="22pt",
        text_font_style="bold",
        text_color=PM_COLOR,
        x_offset=18,
    )
)

# Phase crossover marker on phase plot
p_phase.scatter([phase_cross_freq], [-180], size=16, color=GM_COLOR, marker="circle")

# HoverTool for interactive HTML output (distinctive Bokeh feature)
p_mag.add_tools(
    HoverTool(
        tooltips=[("Frequency", "@frequency{0.00} Hz"), ("Magnitude", "@magnitude{0.0} dB")],
        mode="vline",
        line_policy="nearest",
    )
)
p_phase.add_tools(
    HoverTool(
        tooltips=[("Frequency", "@frequency{0.00} Hz"), ("Phase", "@phase{0.0}°")], mode="vline", line_policy="nearest"
    )
)


# Style helper
def style_plot(p, is_top=False):
    p.yaxis.axis_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_font_size = "22pt"
    p.xaxis.major_label_text_font_size = "18pt"
    p.yaxis.major_label_text_font_size = "18pt"
    p.xaxis.axis_line_color = AXIS_COLOR
    p.yaxis.axis_line_color = AXIS_COLOR
    p.xaxis.axis_line_width = 1.5
    p.yaxis.axis_line_width = 1.5
    p.xaxis.major_tick_line_color = None
    p.yaxis.major_tick_line_color = None
    p.xaxis.minor_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.outline_line_color = None
    p.background_fill_color = BG_COLOR
    p.border_fill_color = "#FFFFFF"
    p.ygrid.grid_line_alpha = 0.25
    p.ygrid.grid_line_width = 1
    p.ygrid.grid_line_dash = [4, 4]
    p.xgrid.grid_line_alpha = 0.15
    p.xgrid.grid_line_width = 1
    p.xgrid.grid_line_dash = [4, 4]
    p.min_border_left = 120
    p.min_border_right = 80
    if is_top:
        p.min_border_bottom = 20
    else:
        p.min_border_top = 20


style_plot(p_mag, is_top=True)
style_plot(p_phase, is_top=False)

# Title styling
p_mag.title.text_font_size = "28pt"
p_mag.title.text_font_style = "normal"
p_mag.title.text_color = "#333333"

# Layout with tight spacing
layout = column(p_mag, p_phase, spacing=0)

# Save
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", resources=CDN, title="bode-basic · bokeh · pyplots.ai")
