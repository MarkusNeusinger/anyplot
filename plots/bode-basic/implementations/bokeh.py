""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Label, Span
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

# Gain crossover: where magnitude crosses 0 dB (find sign change)
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

p_mag.line("frequency", "magnitude", source=source, line_width=3.5, color="#306998")

# 0 dB reference line
p_mag.add_layout(
    Span(location=0, dimension="width", line_color="#888888", line_width=1.5, line_dash="dashed", line_alpha=0.5)
)

# Gain margin annotation
p_mag.scatter([phase_cross_freq], [mag_at_phase_cross], size=14, color="#E85D3A", marker="circle")
p_mag.scatter([phase_cross_freq], [0], size=14, color="#E85D3A", marker="circle")
p_mag.segment(
    x0=[phase_cross_freq],
    y0=[mag_at_phase_cross],
    x1=[phase_cross_freq],
    y1=[0],
    line_width=2.5,
    color="#E85D3A",
    line_dash="dotted",
)
p_mag.add_layout(
    Label(
        x=phase_cross_freq,
        y=mag_at_phase_cross / 2,
        text=f"GM = {gain_margin:.1f} dB",
        text_font_size="18pt",
        text_color="#E85D3A",
        x_offset=15,
        y_offset=0,
    )
)

# Gain crossover marker
p_mag.scatter([gain_cross_freq], [0], size=14, color="#2CA02C", marker="circle")

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

p_phase.line("frequency", "phase", source=source, line_width=3.5, color="#306998")

# -180 degree reference line
p_phase.add_layout(
    Span(location=-180, dimension="width", line_color="#888888", line_width=1.5, line_dash="dashed", line_alpha=0.5)
)

# Phase margin annotation
p_phase.scatter([gain_cross_freq], [phase_at_gain_cross], size=14, color="#2CA02C", marker="circle")
p_phase.scatter([gain_cross_freq], [-180], size=14, color="#2CA02C", marker="circle")
p_phase.segment(
    x0=[gain_cross_freq],
    y0=[phase_at_gain_cross],
    x1=[gain_cross_freq],
    y1=[-180],
    line_width=2.5,
    color="#2CA02C",
    line_dash="dotted",
)
p_phase.add_layout(
    Label(
        x=gain_cross_freq,
        y=(phase_at_gain_cross - 180) / 2,
        text=f"PM = {phase_margin:.1f}°",
        text_font_size="18pt",
        text_color="#2CA02C",
        x_offset=15,
        y_offset=0,
    )
)

# Phase crossover marker
p_phase.scatter([phase_cross_freq], [-180], size=14, color="#E85D3A", marker="circle")

# Style - magnitude plot
p_mag.title.text_font_size = "28pt"
p_mag.title.text_font_style = "normal"
p_mag.yaxis.axis_label_text_font_size = "22pt"
p_mag.xaxis.major_label_text_font_size = "18pt"
p_mag.yaxis.major_label_text_font_size = "18pt"
p_mag.xaxis.axis_line_color = "#333333"
p_mag.yaxis.axis_line_color = "#333333"
p_mag.xaxis.major_tick_line_color = None
p_mag.yaxis.major_tick_line_color = None
p_mag.xaxis.minor_tick_line_color = None
p_mag.yaxis.minor_tick_line_color = None
p_mag.outline_line_color = None
p_mag.background_fill_color = "#FFFFFF"
p_mag.border_fill_color = "#FFFFFF"
p_mag.ygrid.grid_line_alpha = 0.2
p_mag.ygrid.grid_line_width = 1
p_mag.xgrid.grid_line_alpha = 0.2
p_mag.xgrid.grid_line_width = 1

# Style - phase plot
p_phase.yaxis.axis_label_text_font_size = "22pt"
p_phase.xaxis.axis_label_text_font_size = "22pt"
p_phase.xaxis.major_label_text_font_size = "18pt"
p_phase.yaxis.major_label_text_font_size = "18pt"
p_phase.xaxis.axis_line_color = "#333333"
p_phase.yaxis.axis_line_color = "#333333"
p_phase.xaxis.major_tick_line_color = None
p_phase.yaxis.major_tick_line_color = None
p_phase.xaxis.minor_tick_line_color = None
p_phase.yaxis.minor_tick_line_color = None
p_phase.outline_line_color = None
p_phase.background_fill_color = "#FFFFFF"
p_phase.border_fill_color = "#FFFFFF"
p_phase.ygrid.grid_line_alpha = 0.2
p_phase.ygrid.grid_line_width = 1
p_phase.xgrid.grid_line_alpha = 0.2
p_phase.xgrid.grid_line_width = 1

# Layout
layout = column(p_mag, p_phase)

# Save
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", resources=CDN, title="bode-basic · bokeh · pyplots.ai")
