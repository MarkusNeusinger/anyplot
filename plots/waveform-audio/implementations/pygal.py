"""pyplots.ai
waveform-audio: Audio Waveform Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - synthesized A3 note (220 Hz) with harmonics and decay envelope
np.random.seed(42)
sample_rate = 22050
duration = 0.15
t = np.linspace(0, duration, int(sample_rate * duration))

fundamental = 220
attack_time = 0.005
envelope = np.exp(-2.0 * t / duration) * (1.0 - np.exp(-t / attack_time))
signal = (
    np.sin(2 * np.pi * fundamental * t)
    + 0.5 * np.sin(2 * np.pi * 2 * fundamental * t)
    + 0.25 * np.sin(2 * np.pi * 3 * fundamental * t)
    + 0.12 * np.sin(2 * np.pi * 5 * fundamental * t)
)
signal = signal / np.max(np.abs(signal))
amplitude = signal * envelope
amplitude = amplitude / np.max(np.abs(amplitude)) * 0.92

# Downsample for pygal SVG rendering
n_points = 800
indices = np.linspace(0, len(t) - 1, n_points, dtype=int)
t_down = t[indices]
amp_down = amplitude[indices]
env_down = envelope[indices] / np.max(np.abs(envelope)) * 0.92

# Build XY data as (time_seconds, amplitude) tuples
waveform_data = [
    {
        "value": (round(float(t_down[i]), 5), round(float(amp_down[i]), 4)),
        "label": f"t={float(t_down[i]):.4f}s  amp={float(amp_down[i]):.3f}",
    }
    for i in range(n_points)
]

# Envelope curves to emphasize the decay story
envelope_upper = [(round(float(t_down[i]), 5), round(float(env_down[i]), 4)) for i in range(n_points)]
envelope_lower = [(round(float(t_down[i]), 5), round(float(-env_down[i]), 4)) for i in range(n_points)]

# Style - publication quality with larger fonts for 4800x2700
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#c44e52", "#c44e52"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    value_font_size=28,
    tooltip_font_size=28,
    stroke_width=1.5,
    opacity=0.75,
    opacity_hover=0.95,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Chart with pygal-specific formatting features
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="waveform-audio · pygal · pyplots.ai",
    x_title="Time (s)",
    y_title="Amplitude",
    show_dots=False,
    fill=True,
    stroke_style={"width": 1.5},
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    range=(-1.0, 1.0),
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_label=-1,
    x_value_formatter=lambda x: f"{x:.3f}",
    value_formatter=lambda x: f"{x:.3f}",
    print_values=False,
    margin_top=40,
    margin_bottom=60,
    spacing=30,
)

chart.add("Waveform", waveform_data)

# Envelope lines showing decay boundary
chart.add(
    "Decay envelope", envelope_upper, stroke_style={"width": 2.5, "dasharray": "8,4"}, show_dots=False, fill=False
)
chart.add(None, envelope_lower, stroke_style={"width": 2.5, "dasharray": "8,4"}, show_dots=False, fill=False)

# Zero reference line
zero_line = [(round(float(t_down[0]), 5), 0), (round(float(t_down[-1]), 5), 0)]
chart.add(None, zero_line, stroke_style={"width": 1.5, "dasharray": "4,6"}, show_dots=False, fill=False)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
