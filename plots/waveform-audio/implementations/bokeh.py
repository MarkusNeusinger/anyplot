""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, Range1d, Span
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
attack_samples = int(0.05 * sample_rate)
release_samples = int(0.3 * sample_rate)
envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
envelope[-release_samples:] = np.linspace(1, 0, release_samples)

# Phase boundaries (in seconds)
attack_end = 0.05
sustain_end = duration - 0.3

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

# Split into attack / sustain / release segments for color-coded rendering
attack_mask = env_time <= attack_end
sustain_mask = (env_time > attack_end) & (env_time <= sustain_end)
release_mask = env_time > sustain_end

source_attack = ColumnDataSource(
    data={"x": env_time[attack_mask], "y1": env_min[attack_mask], "y2": env_max[attack_mask]}
)
source_sustain = ColumnDataSource(
    data={"x": env_time[sustain_mask], "y1": env_min[sustain_mask], "y2": env_max[sustain_mask]}
)
source_release = ColumnDataSource(
    data={"x": env_time[release_mask], "y1": env_min[release_mask], "y2": env_max[release_mask]}
)

# Colors for each phase - cohesive palette around Python Blue
color_attack = "#4A90D9"  # lighter blue for attack
color_sustain = "#306998"  # Python Blue for sustain (main body)
color_release = "#1D4F72"  # darker blue for release/decay

# Plot
p = figure(
    width=4800,
    height=2700,
    title="waveform-audio · bokeh · pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Amplitude",
    y_range=Range1d(-1.12, 1.12),
    background_fill_color="#F7F9FC",
)

# Phase region shading with BoxAnnotation
phase_alpha = 0.04
p.add_layout(BoxAnnotation(left=0, right=attack_end, fill_color=color_attack, fill_alpha=phase_alpha))
p.add_layout(BoxAnnotation(left=attack_end, right=sustain_end, fill_color=color_sustain, fill_alpha=phase_alpha))
p.add_layout(BoxAnnotation(left=sustain_end, right=duration, fill_color=color_release, fill_alpha=phase_alpha))

# Filled waveform using varea (idiomatic Bokeh)
p.varea(x="x", y1="y1", y2="y2", source=source_attack, fill_color=color_attack, fill_alpha=0.45)
p.varea(x="x", y1="y1", y2="y2", source=source_sustain, fill_color=color_sustain, fill_alpha=0.40)
p.varea(x="x", y1="y1", y2="y2", source=source_release, fill_color=color_release, fill_alpha=0.45)

# Waveform outline edges
for src in [source_attack, source_sustain, source_release]:
    p.line("x", "y2", source=src, line_color="#306998", line_width=2, line_alpha=0.7)
    p.line("x", "y1", source=src, line_color="#306998", line_width=2, line_alpha=0.7)

# Zero baseline
zero_line = Span(location=0, dimension="width", line_color="#555555", line_width=2, line_alpha=0.4)
p.add_layout(zero_line)

# Phase labels using Label model
label_props = {"text_font_size": "16pt", "text_color": "#666666", "text_font_style": "italic", "text_alpha": 0.7}
p.add_layout(Label(x=attack_end / 2, y=1.03, text="Attack", text_align="center", **label_props))
p.add_layout(Label(x=(attack_end + sustain_end) / 2, y=1.03, text="Sustain", text_align="center", **label_props))
p.add_layout(Label(x=(sustain_end + duration) / 2, y=1.03, text="Release", text_align="center", **label_props))

# Phase boundary lines
for boundary in [attack_end, sustain_end]:
    p.add_layout(
        Span(
            location=boundary,
            dimension="height",
            line_color="#999999",
            line_width=1.5,
            line_dash="dashed",
            line_alpha=0.4,
        )
    )

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.title.text_color = "#2C3E50"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"

p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.axis_line_color = "#AAAAAA"
p.yaxis.axis_line_color = "#AAAAAA"

p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [4, 4]

p.yaxis.ticker = [-1.0, -0.5, 0.0, 0.5, 1.0]
p.border_fill_color = "#F7F9FC"

p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Audio Waveform Plot")
