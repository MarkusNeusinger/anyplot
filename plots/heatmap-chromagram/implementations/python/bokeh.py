""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, FixedTicker, HoverTool, LinearColorMapper, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Simulated chromagram: 12 pitch classes over 80 time frames
np.random.seed(42)
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_pitch = len(pitch_classes)
n_frames = 80
time_seconds = np.linspace(0, 8, n_frames)

# Build energy matrix simulating chord progressions:
# C major (C-E-G) -> G major (G-B-D) -> Am (A-C-E) -> F major (F-A-C)
energy = np.random.uniform(0.02, 0.12, size=(12, n_frames))

chord_patterns = {
    "C_major": {"notes": [0, 4, 7], "boost": [0.9, 0.7, 0.8]},
    "G_major": {"notes": [7, 11, 2], "boost": [0.9, 0.7, 0.75]},
    "A_minor": {"notes": [9, 0, 4], "boost": [0.85, 0.7, 0.7]},
    "F_major": {"notes": [5, 9, 0], "boost": [0.9, 0.7, 0.75]},
}

chord_sequence = ["C_major", "G_major", "A_minor", "F_major"]
frames_per_chord = n_frames // len(chord_sequence)

for idx, chord_name in enumerate(chord_sequence):
    start = idx * frames_per_chord
    end = start + frames_per_chord
    pattern = chord_patterns[chord_name]
    for note_idx, boost in zip(pattern["notes"], pattern["boost"], strict=True):
        energy[note_idx, start:end] += boost + np.random.uniform(-0.08, 0.08, end - start)
    for note_idx in pattern["notes"]:
        neighbor = (note_idx + 7) % 12
        energy[neighbor, start:end] += 0.15 + np.random.uniform(-0.03, 0.03, end - start)

# Smooth transitions between chords
for i in range(1, len(chord_sequence)):
    boundary = i * frames_per_chord
    if boundary - 2 >= 0 and boundary + 2 < n_frames:
        for row in range(12):
            window = energy[row, boundary - 2 : boundary + 3]
            energy[row, boundary - 2 : boundary + 3] = np.convolve(window, [0.15, 0.25, 0.3, 0.2, 0.1], mode="same")

energy = np.clip(energy, 0, 1)

# Prepare data for rendering
dt = time_seconds[1] - time_seconds[0]

# Reverse energy rows so C is at top (row 0 in image = bottom of plot = B)
# image glyph renders row 0 at the bottom, so reversed energy puts C at top
energy_image = energy[::-1, :]

# Flatten to DataFrame for HoverTool interactivity
records = []
for i, pitch in enumerate(pitch_classes):
    y_pos = n_pitch - 1 - i  # C=11 (top), B=0 (bottom)
    for j in range(n_frames):
        records.append(
            {"time": float(time_seconds[j]), "pitch": pitch, "y": y_pos, "energy": round(float(energy[i, j]), 3)}
        )

source = ColumnDataSource(pd.DataFrame(records))

# Sequential colormap (magma-inspired)
magma_palette = [
    "#000004",
    "#0d0829",
    "#1b0c41",
    "#280b53",
    "#3d0965",
    "#510a6c",
    "#63106e",
    "#76176e",
    "#89226a",
    "#9c2e64",
    "#ae395c",
    "#bf4a52",
    "#cd5e48",
    "#d9743e",
    "#e48c35",
    "#eda72e",
    "#f3c321",
    "#f8df17",
    "#fcffa4",
]

# Color mapper
mapper = LinearColorMapper(palette=magma_palette, low=0, high=1)

# Create figure with numeric axes
p = figure(
    width=4800,
    height=2700,
    y_range=Range1d(-0.5, n_pitch - 0.5),
    x_range=(-dt / 2, 8 + dt / 2),
    title="heatmap-chromagram · bokeh · pyplots.ai",
    x_axis_label="Time (seconds)",
    y_axis_label="Pitch Class",
    toolbar_location=None,
    tools="",
)

# Custom y-axis tick labels for pitch classes
p.yaxis.ticker = FixedTicker(ticks=list(range(n_pitch)))
p.yaxis.major_label_overrides = {i: pitch_classes[n_pitch - 1 - i] for i in range(n_pitch)}

# Seamless heatmap using image glyph (no gaps between cells)
p.image(image=[energy_image], x=-dt / 2, y=-0.5, dw=8 + dt, dh=n_pitch, color_mapper=mapper)

# Invisible rect layer for HoverTool interactivity (HTML only)
r = p.rect(x="time", y="y", width=dt, height=1, source=source, fill_alpha=0, line_alpha=0)

# Color bar — wider with larger labels for 4800px canvas
color_bar = ColorBar(
    color_mapper=mapper,
    width=100,
    ticker=BasicTicker(desired_num_ticks=8),
    label_standoff=25,
    major_label_text_font_size="24pt",
    border_line_color=None,
    padding=20,
    title="Energy",
    title_text_font_size="26pt",
    title_standoff=30,
)
p.add_layout(color_bar, "right")

# HoverTool for interactive HTML
hover = HoverTool(
    tooltips=[("Pitch", "@pitch"), ("Time", "@time{0.00} s"), ("Energy", "@energy{0.000}")], renderers=[r]
)
p.add_tools(hover)

# Styling for 4800x2700 px
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid and axes
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.outline_line_color = None

# Dark background to complement magma colormap
p.min_border_right = 200
p.min_border_left = 40
p.min_border_top = 30
p.min_border_bottom = 40
p.background_fill_color = "#0a0a0a"
p.border_fill_color = "#1a1a1a"
p.title.text_color = "#e0e0e0"
p.xaxis.axis_label_text_color = "#cccccc"
p.yaxis.axis_label_text_color = "#cccccc"
p.xaxis.major_label_text_color = "#aaaaaa"
p.yaxis.major_label_text_color = "#cccccc"
color_bar.major_label_text_color = "#cccccc"
color_bar.title_text_color = "#cccccc"
color_bar.background_fill_color = "#1a1a1a"
color_bar.bar_line_color = None
color_bar.major_tick_line_color = "#666666"
color_bar.minor_tick_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="heatmap-chromagram · bokeh · pyplots.ai")
