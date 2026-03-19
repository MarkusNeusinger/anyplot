"""pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Label, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Synthetic ECG waveform generation using Gaussian pulse model
np.random.seed(42)

sampling_rate = 1000
duration = 2.5
n_samples = int(sampling_rate * duration)
t = np.linspace(0, duration, n_samples)

heart_rate_bpm = 72
beat_interval = 60.0 / heart_rate_bpm
beat_centers = np.arange(beat_interval / 2, duration, beat_interval)

# Gaussian pulse parameters: (center_offset, sigma, amplitude)
p_wave_params = [(-0.18, 0.012, 0.15), (-0.15, 0.012, 0.10)]
qrs_params = [(-0.04, 0.004, -0.10), (0.0, 0.004, 1.20), (0.03, 0.004, -0.25)]
t_wave_params = [(0.20, 0.025, 0.30)]

# Lead transformation factors (approximate Einthoven/Goldberger/Wilson relations)
lead_transforms = {
    "I": {"scale": 0.65, "invert": False, "p_scale": 0.8, "t_scale": 0.7},
    "II": {"scale": 1.0, "invert": False, "p_scale": 1.0, "t_scale": 1.0},
    "III": {"scale": 0.55, "invert": False, "p_scale": 0.5, "t_scale": 0.6},
    "aVR": {"scale": 0.75, "invert": True, "p_scale": 0.9, "t_scale": 0.8},
    "aVL": {"scale": 0.45, "invert": False, "p_scale": 0.6, "t_scale": 0.5},
    "aVF": {"scale": 0.70, "invert": False, "p_scale": 0.7, "t_scale": 0.8},
    "V1": {"scale": 0.80, "invert": True, "p_scale": 0.3, "t_scale": 0.4},
    "V2": {"scale": 1.10, "invert": False, "p_scale": 0.4, "t_scale": 0.5},
    "V3": {"scale": 1.30, "invert": False, "p_scale": 0.5, "t_scale": 0.6},
    "V4": {"scale": 1.20, "invert": False, "p_scale": 0.7, "t_scale": 0.8},
    "V5": {"scale": 0.90, "invert": False, "p_scale": 0.8, "t_scale": 0.9},
    "V6": {"scale": 0.70, "invert": False, "p_scale": 0.9, "t_scale": 0.8},
}

leads = {}
for lead_name, params in lead_transforms.items():
    signal = np.zeros(n_samples)
    for center in beat_centers:
        t_shifted = t - center
        beat = np.zeros(n_samples)
        for offset, sigma, amp in p_wave_params:
            beat += amp * params["p_scale"] * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
        for offset, sigma, amp in qrs_params:
            beat += amp * params["scale"] * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
        for offset, sigma, amp in t_wave_params:
            beat += amp * params["t_scale"] * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
        signal += beat
    if params["invert"]:
        signal = -signal
    signal += np.random.normal(0, 0.015, n_samples)
    leads[lead_name] = signal

# Standard clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Colors
ecg_trace_color = "#1B5E20"
grid_minor_color = "#F8D0C0"
grid_major_color = "#E8978A"
paper_bg_color = "#FFF5F0"
label_color = "#333333"

# Plot - Create individual lead figures in a grid
fig_width = 1200
fig_height = 620
y_range_mv = 2.0

figures = []
for _row_idx, lead_row in enumerate(grid_layout):
    fig_row = []
    for col_idx, lead_name in enumerate(lead_row):
        signal = leads[lead_name]

        p = figure(
            width=fig_width,
            height=fig_height,
            x_range=Range1d(0, duration),
            y_range=Range1d(-y_range_mv, y_range_mv),
            tools="",
            toolbar_location=None,
        )

        # ECG paper grid - major lines every 0.2s and 0.5mV
        for x_major in np.arange(0, duration + 0.01, 0.2):
            p.add_layout(
                Span(location=x_major, dimension="height", line_color=grid_major_color, line_width=2, line_alpha=0.7)
            )
        for y_major in np.arange(-y_range_mv, y_range_mv + 0.01, 0.5):
            p.add_layout(
                Span(location=y_major, dimension="width", line_color=grid_major_color, line_width=2, line_alpha=0.7)
            )

        # Minor grid lines every 0.04s and 0.1mV
        for x_minor in np.arange(0, duration + 0.01, 0.04):
            p.add_layout(
                Span(location=x_minor, dimension="height", line_color=grid_minor_color, line_width=1, line_alpha=0.5)
            )
        for y_minor in np.arange(-y_range_mv, y_range_mv + 0.01, 0.1):
            p.add_layout(
                Span(location=y_minor, dimension="width", line_color=grid_minor_color, line_width=1, line_alpha=0.5)
            )

        # ECG trace
        source = ColumnDataSource(data={"time": t, "voltage": signal})
        p.line(x="time", y="voltage", source=source, line_color=ecg_trace_color, line_width=2.5, line_alpha=0.95)

        # Lead label
        p.add_layout(
            Label(
                x=0.06,
                y=y_range_mv * 0.72,
                text=lead_name,
                text_font_size="22pt",
                text_font_style="bold",
                text_color=label_color,
            )
        )

        # Calibration pulse on leftmost column (1mV square pulse indicator)
        if col_idx == 0:
            p.line(
                x=[0.02, 0.02, 0.08, 0.08],
                y=[0.0, 1.0, 1.0, 0.0],
                line_color=ecg_trace_color,
                line_width=2,
                line_alpha=0.6,
            )

        # Style
        p.xaxis.visible = False
        p.yaxis.visible = False
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        p.background_fill_color = paper_bg_color
        p.border_fill_color = "white"
        p.outline_line_color = "#D0D0D0"
        p.outline_line_width = 1
        p.min_border = 5

        fig_row.append(p)
    figures.append(fig_row)

# Rhythm strip (Lead II, 10 seconds)
rhythm_duration = 10.0
rhythm_t = np.linspace(0, rhythm_duration, int(sampling_rate * rhythm_duration))
rhythm_signal = np.zeros(len(rhythm_t))
rhythm_beat_centers = np.arange(beat_interval / 2, rhythm_duration, beat_interval)
for center in rhythm_beat_centers:
    t_shifted = rhythm_t - center
    for offset, sigma, amp in p_wave_params:
        rhythm_signal += amp * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
    for offset, sigma, amp in qrs_params:
        rhythm_signal += amp * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
    for offset, sigma, amp in t_wave_params:
        rhythm_signal += amp * np.exp(-((t_shifted - offset) ** 2) / (2 * sigma**2))
rhythm_signal += np.random.normal(0, 0.015, len(rhythm_t))

p_rhythm = figure(
    width=fig_width * 4,
    height=500,
    x_range=Range1d(0, rhythm_duration),
    y_range=Range1d(-y_range_mv, y_range_mv),
    tools="",
    toolbar_location=None,
)

# Rhythm strip grid
for x_major in np.arange(0, rhythm_duration + 0.01, 0.2):
    p_rhythm.add_layout(
        Span(location=x_major, dimension="height", line_color=grid_major_color, line_width=2, line_alpha=0.7)
    )
for y_major in np.arange(-y_range_mv, y_range_mv + 0.01, 0.5):
    p_rhythm.add_layout(
        Span(location=y_major, dimension="width", line_color=grid_major_color, line_width=2, line_alpha=0.7)
    )
for x_minor in np.arange(0, rhythm_duration + 0.01, 0.04):
    p_rhythm.add_layout(
        Span(location=x_minor, dimension="height", line_color=grid_minor_color, line_width=1, line_alpha=0.5)
    )
for y_minor in np.arange(-y_range_mv, y_range_mv + 0.01, 0.1):
    p_rhythm.add_layout(
        Span(location=y_minor, dimension="width", line_color=grid_minor_color, line_width=1, line_alpha=0.5)
    )

rhythm_source = ColumnDataSource(data={"time": rhythm_t, "voltage": rhythm_signal})
p_rhythm.line(x="time", y="voltage", source=rhythm_source, line_color=ecg_trace_color, line_width=2.5, line_alpha=0.95)

p_rhythm.add_layout(
    Label(
        x=0.06,
        y=y_range_mv * 0.72,
        text="II (Rhythm)",
        text_font_size="22pt",
        text_font_style="bold",
        text_color=label_color,
    )
)

p_rhythm.xaxis.visible = False
p_rhythm.yaxis.visible = False
p_rhythm.xgrid.grid_line_color = None
p_rhythm.ygrid.grid_line_color = None
p_rhythm.background_fill_color = paper_bg_color
p_rhythm.border_fill_color = "white"
p_rhythm.outline_line_color = "#D0D0D0"
p_rhythm.outline_line_width = 1
p_rhythm.min_border = 5

# Title
p_title = figure(
    width=fig_width * 4, height=160, tools="", toolbar_location=None, x_range=Range1d(0, 1), y_range=Range1d(0, 1)
)
p_title.add_layout(
    Label(
        x=0.5,
        y=0.55,
        text="ecg-twelve-lead · bokeh · pyplots.ai",
        text_font_size="36pt",
        text_font_style="normal",
        text_color="#333333",
        text_align="center",
    )
)
p_title.add_layout(
    Label(
        x=0.5,
        y=0.1,
        text="25 mm/s  ·  10 mm/mV  ·  Normal Sinus Rhythm  ·  72 BPM",
        text_font_size="20pt",
        text_font_style="normal",
        text_color="#777777",
        text_align="center",
    )
)
p_title.xaxis.visible = False
p_title.yaxis.visible = False
p_title.xgrid.grid_line_color = None
p_title.ygrid.grid_line_color = None
p_title.background_fill_color = "white"
p_title.border_fill_color = "white"
p_title.outline_line_color = None
p_title.min_border = 0

# Assemble layout
grid = gridplot(figures, toolbar_location=None, merge_tools=False)
layout = column(p_title, grid, p_rhythm)

# Save
export_png(layout, filename="plot.png")
save(layout, filename="plot.html", resources=CDN, title="ecg-twelve-lead · bokeh · pyplots.ai")
