"""pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, FixedTicker, HoverTool, LinearColorMapper, Range1d
from bokeh.plotting import figure
from bokeh.resources import Resources


# Data
np.random.seed(42)

note_names_map = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}

black_key_indices = {1, 3, 6, 8, 10}


note_names = [f"{note_names_map[p % 12]}{p // 12 - 1}" for p in range(128)]
black_keys = {p for p in range(128) if (p % 12) in black_key_indices}

# A short melody/chord progression (C major scale run + chords, ~8 measures)
notes = []

# Measure 1-2: ascending C major scale (C4 to C5)
scale_pitches = [60, 62, 64, 65, 67, 69, 71, 72]
for i, pitch in enumerate(scale_pitches):
    notes.append({"start": i * 0.5, "duration": 0.45, "pitch": pitch, "velocity": 60 + i * 8})

# Measure 3-4: descending with longer notes
desc_pitches = [72, 71, 69, 67, 65, 64, 62, 60]
for i, pitch in enumerate(desc_pitches):
    notes.append({"start": 4.0 + i * 0.5, "duration": 0.45, "pitch": pitch, "velocity": 110 - i * 8})

# Measure 5-6: C major chord arpeggiation and block chords
chord_notes = [
    (8.0, 1.0, 60, 90),
    (8.0, 1.0, 64, 85),
    (8.0, 1.0, 67, 80),
    (9.0, 1.0, 65, 95),
    (9.0, 1.0, 69, 90),
    (9.0, 1.0, 72, 85),
    (10.0, 1.0, 67, 100),
    (10.0, 1.0, 71, 95),
    (10.0, 1.0, 74, 90),
    (11.0, 1.0, 60, 105),
    (11.0, 1.0, 64, 100),
    (11.0, 1.0, 67, 95),
    (11.0, 1.0, 72, 90),
]
for start, dur, pitch, vel in chord_notes:
    notes.append({"start": start, "duration": dur, "pitch": pitch, "velocity": vel})

# Measure 7-8: melodic phrase with varied dynamics
melody = [
    (12.0, 0.5, 72, 110),
    (12.5, 0.25, 74, 90),
    (12.75, 0.25, 72, 85),
    (13.0, 0.5, 71, 100),
    (13.5, 0.5, 69, 95),
    (14.0, 1.0, 67, 80),
    (15.0, 0.5, 65, 70),
    (15.5, 0.5, 64, 65),
    (14.0, 1.0, 60, 75),
    (15.0, 1.0, 62, 70),
]
for start, dur, pitch, vel in melody:
    notes.append({"start": start, "duration": dur, "pitch": pitch, "velocity": vel})

starts = np.array([n["start"] for n in notes])
durations = np.array([n["duration"] for n in notes])
pitches = np.array([n["pitch"] for n in notes])
velocities = np.array([n["velocity"] for n in notes])

# Compute rectangle geometry (center-based)
rect_x = starts + durations / 2
rect_y = pitches.astype(float)
rect_w = durations
rect_h = np.full_like(durations, 0.8)

# Pitch range with margin
pitch_min = int(pitches.min()) - 1
pitch_max = int(pitches.max()) + 2

# Background rows for black/white key distinction
bg_pitches = list(range(pitch_min, pitch_max))
bg_x = [8.0] * len(bg_pitches)
bg_w = [18.0] * len(bg_pitches)
bg_h = [1.0] * len(bg_pitches)
bg_colors = ["#E8E8E8" if p in black_keys else "#F8F8F8" for p in bg_pitches]

bg_source = ColumnDataSource(
    data={"x": bg_x, "y": [float(p) for p in bg_pitches], "w": bg_w, "h": bg_h, "color": bg_colors}
)

# Note source
color_mapper = LinearColorMapper(
    palette=[
        "#2C3E7B",
        "#306998",
        "#3A8EC2",
        "#5DADE2",
        "#85C1E9",
        "#F5B041",
        "#EB984E",
        "#E74C3C",
        "#C0392B",
        "#922B21",
    ],
    low=40,
    high=127,
)

note_source = ColumnDataSource(
    data={
        "x": rect_x,
        "y": rect_y,
        "w": rect_w,
        "h": rect_h,
        "velocity": velocities,
        "pitch": pitches,
        "note_name": [note_names[p] for p in pitches],
        "start": starts,
        "duration": durations,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="piano-roll-midi \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time (beats)",
    y_axis_label="Pitch",
    x_range=Range1d(-0.5, 16.5),
    y_range=Range1d(pitch_min - 0.5, pitch_max + 0.5),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Background key shading
p.rect(x="x", y="y", width="w", height="h", source=bg_source, fill_color="color", line_color=None, level="underlay")

# Beat grid lines (light for beats, strong for measures)
for beat in range(17):
    alpha = 0.4 if beat % 4 == 0 else 0.15
    width = 3 if beat % 4 == 0 else 1
    p.line([beat, beat], [pitch_min - 0.5, pitch_max + 0.5], line_color="#999999", line_alpha=alpha, line_width=width)

# Note rectangles
p.rect(
    x="x",
    y="y",
    width="w",
    height="h",
    source=note_source,
    fill_color={"field": "velocity", "transform": color_mapper},
    line_color="white",
    line_width=2,
    line_alpha=0.9,
)

# Hover tool
hover = HoverTool(
    tooltips=[
        ("Note", "@note_name"),
        ("Start", "@start{0.00} beats"),
        ("Duration", "@duration{0.00} beats"),
        ("Velocity", "@velocity"),
    ]
)
p.add_tools(hover)

# Style
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Y-axis: show note names
y_ticks = list(range(pitch_min, pitch_max + 1))
p.yaxis.ticker = FixedTicker(ticks=y_ticks)
p.yaxis.major_label_overrides = {p_val: note_names[p_val] for p_val in y_ticks}

# X-axis: show beat numbers
p.xaxis.ticker = FixedTicker(ticks=list(range(17)))

# Remove top/right spines
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"

p.min_border_left = 120
p.min_border_bottom = 80

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="piano-roll-midi", resources=Resources(mode="cdn"))
