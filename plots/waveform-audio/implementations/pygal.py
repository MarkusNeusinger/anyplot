"""pyplots.ai
waveform-audio: Audio Waveform Plot
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data
np.random.seed(42)
sample_rate = 22050
duration = 0.15
t = np.linspace(0, duration, int(sample_rate * duration))

fundamental = 220
envelope = np.exp(-2.0 * t / duration) * (1.0 - np.exp(-80 * t))
signal = (
    np.sin(2 * np.pi * fundamental * t)
    + 0.5 * np.sin(2 * np.pi * 2 * fundamental * t)
    + 0.25 * np.sin(2 * np.pi * 3 * fundamental * t)
    + 0.12 * np.sin(2 * np.pi * 5 * fundamental * t)
)
signal = signal / np.max(np.abs(signal))
amplitude = signal * envelope
amplitude = amplitude / np.max(np.abs(amplitude)) * 0.92

# Downsample for pygal (SVG can't handle 3000+ points well)
n_points = 800
indices = np.linspace(0, len(t) - 1, n_points, dtype=int)
t_down = t[indices]
amp_down = amplitude[indices]

# Build XY data as list of (time_ms, amplitude) tuples
waveform_data = [(round(float(t_down[i]) * 1000, 3), round(float(amp_down[i]), 4)) for i in range(n_points)]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998",),
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=1.5,
    opacity=0.85,
    opacity_hover=1.0,
)

# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="waveform-audio · pygal · pyplots.ai",
    x_title="Time (ms)",
    y_title="Amplitude",
    show_dots=False,
    fill=True,
    stroke_style={"width": 1.5},
    show_legend=False,
    range=(-1.0, 1.0),
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_label=-1,
)

chart.add("Waveform", waveform_data)

# Zero reference line
zero_line = [(round(float(t_down[0]) * 1000, 3), 0), (round(float(t_down[-1]) * 1000, 3), 0)]
chart.add("Zero", zero_line, stroke_style={"width": 1.0, "dasharray": "6,4"}, show_dots=False, fill=False)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
