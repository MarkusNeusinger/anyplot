""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - synthesized A3 note (220 Hz) with harmonics and decay envelope
np.random.seed(42)
sample_rate = 44100
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

# Downsample for pygal SVG rendering - enough points for smooth waveform
n_points = 1200
indices = np.linspace(0, len(t) - 1, n_points, dtype=int)
t_down = t[indices]
amp_down = amplitude[indices]
env_down = envelope[indices] / np.max(np.abs(envelope)) * 0.92

# Build XY data with per-point dict format for rich tooltips (pygal distinctive feature)
waveform_data = [
    {
        "value": (round(float(t_down[i]), 5), round(float(amp_down[i]), 4)),
        "label": f"t={float(t_down[i]):.4f}s  amp={float(amp_down[i]):.3f}",
    }
    for i in range(n_points)
]

# Envelope curves with per-point labels for interactive exploration
envelope_upper = [
    {
        "value": (round(float(t_down[i]), 5), round(float(env_down[i]), 4)),
        "label": f"envelope: ±{float(env_down[i]):.3f}",
    }
    for i in range(n_points)
]
envelope_lower = [
    {
        "value": (round(float(t_down[i]), 5), round(float(-env_down[i]), 4)),
        "label": f"envelope: {float(-env_down[i]):.3f}",
    }
    for i in range(n_points)
]

# Peak amplitude marker - highlight the attack transient peak for data storytelling
peak_idx = int(np.argmax(np.abs(amp_down)))
peak_marker = [
    {
        "value": (round(float(t_down[peak_idx]), 5), round(float(amp_down[peak_idx]), 4)),
        "label": f"Peak: {float(amp_down[peak_idx]):.3f} at {float(t_down[peak_idx]):.4f}s",
    }
]

# Style - publication quality with colorblind-safe palette
# Using blue (#306998) + orange (#E69F00) - universally distinguishable
custom_style = Style(
    background="white",
    plot_background="#f5f6f8",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d0d0d0",
    colors=("#306998", "#E69F00", "#E69F00", "#306998", "#999999"),
    title_font_size=62,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    value_font_size=28,
    tooltip_font_size=28,
    stroke_width=1.8,
    opacity=0.65,
    opacity_hover=0.95,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
    transition="200ms ease-in",
)

# X-axis labels - fewer ticks to avoid crowding
x_labels = [round(i * 0.02, 2) for i in range(8)]

# Chart with comprehensive pygal configuration
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="waveform-audio \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time (s)",
    y_title="Amplitude",
    show_dots=False,
    fill=True,
    stroke_style={"width": 1.8},
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=30,
    range=(-1.0, 1.0),
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_label=-1,
    x_labels=x_labels,
    x_labels_major_every=1,
    x_value_formatter=lambda x: f"{x:.2f}",
    value_formatter=lambda x: f"{x:.3f}",
    print_values=False,
    margin_top=50,
    margin_bottom=70,
    margin_left=80,
    margin_right=40,
    spacing=25,
    show_minor_x_labels=False,
    dots_size=0,
    explicit_size=True,
    js=[],
    secondary_range=(-1.0, 1.0),
    interpolate="cubic",
)

chart.add("Waveform", waveform_data)

# Envelope lines showing decay boundary - thick dashed for strong visibility
chart.add(
    "Decay envelope",
    envelope_upper,
    stroke_style={"width": 4.5, "dasharray": "12,6", "linecap": "round"},
    show_dots=False,
    fill=False,
)
chart.add(
    None,
    envelope_lower,
    stroke_style={"width": 4.5, "dasharray": "12,6", "linecap": "round"},
    show_dots=False,
    fill=False,
)

# Peak transient marker - distinctive pygal per-point styling with custom node
chart.add("Peak transient", peak_marker, stroke_style={"width": 0}, dots_size=12, show_dots=True, fill=False)

# Zero reference line
zero_line = [
    {"value": (0.0, 0), "label": "zero baseline"},
    {"value": (round(float(t_down[-1]), 5), 0), "label": "zero baseline"},
]
chart.add(None, zero_line, stroke_style={"width": 1.5, "dasharray": "4,6"}, show_dots=False, fill=False)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
