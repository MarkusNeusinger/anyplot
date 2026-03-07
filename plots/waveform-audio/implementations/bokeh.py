""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)
sample_rate = 22050
duration = 1.5
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

# Synthesize audio: fundamental + harmonics with amplitude envelope
fundamental = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * time)
    + 0.25 * np.sin(2 * np.pi * fundamental * 2 * time)
    + 0.1 * np.sin(2 * np.pi * fundamental * 3 * time)
    + 0.05 * np.sin(2 * np.pi * fundamental * 5 * time)
)

# Amplitude envelope: attack-sustain-release shape
envelope = np.ones(num_samples)
attack = int(0.05 * sample_rate)
release = int(0.3 * sample_rate)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[-release:] = np.linspace(1, 0, release)

# Add tremolo modulation
tremolo = 1.0 - 0.15 * np.sin(2 * np.pi * 5.5 * time)
amplitude = signal * envelope * tremolo

# Normalize to [-1, 1]
amplitude = amplitude / np.max(np.abs(amplitude))

# Downsample for envelope rendering (min/max per chunk)
chunk_size = 8
num_chunks = num_samples // chunk_size
time_chunked = time[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)
amp_chunked = amplitude[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)

env_time = time_chunked.mean(axis=1)
env_max = amp_chunked.max(axis=1)
env_min = amp_chunked.min(axis=1)

# Build filled area coordinates (upper then lower reversed)
fill_x = np.concatenate([env_time, env_time[::-1]])
fill_y = np.concatenate([env_max, env_min[::-1]])

source_fill = ColumnDataSource(data={"x": fill_x, "y": fill_y})
source_upper = ColumnDataSource(data={"time": env_time, "amplitude": env_max})
source_lower = ColumnDataSource(data={"time": env_time, "amplitude": env_min})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="waveform-audio \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Amplitude",
    y_range=Range1d(-1.15, 1.15),
)

# Filled waveform area
p.patch("x", "y", source=source_fill, fill_color="#306998", fill_alpha=0.35, line_color=None)

# Waveform outline (upper and lower edges)
p.line("time", "amplitude", source=source_upper, line_color="#306998", line_width=2, line_alpha=0.8)
p.line("time", "amplitude", source=source_lower, line_color="#306998", line_width=2, line_alpha=0.8)

# Zero baseline
zero_line = Span(location=0, dimension="width", line_color="#333333", line_width=2, line_alpha=0.5, line_dash="solid")
p.add_layout(zero_line)

# Style
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_alpha = 0.2

p.yaxis.ticker = [-1.0, -0.5, 0.0, 0.5, 1.0]

p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Audio Waveform Plot")
