"""pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - A chord progression with melody (Cmaj - Am - F - G pattern, 8 measures)
np.random.seed(42)

# Black key semitone positions within an octave (1=C#, 3=D#, 6=F#, 8=G#, 10=A#)
black_semitones = {1, 3, 6, 8, 10}
black_key_pitches = {p for p in range(0, 128) if (p % 12) in black_semitones}

# Chord progression: C major - A minor - F major - G major (repeated twice)
# Wider velocity range for better color differentiation
chords = [
    # Measure 1: C major - building
    (0, 4, [48, 52, 55, 60], [55, 50, 45, 60]),
    # Measure 2: A minor - softer
    (4, 4, [48, 52, 57, 60], [40, 38, 35, 45]),
    # Measure 3: F major - growing
    (8, 4, [48, 53, 57, 60], [65, 60, 55, 70]),
    # Measure 4: G major - strong
    (12, 4, [47, 50, 55, 59], [80, 75, 70, 85]),
    # Measure 5: C major - restart softer
    (16, 4, [48, 52, 55, 60], [45, 40, 35, 50]),
    # Measure 6: A minor - quiet
    (20, 4, [48, 52, 57, 60], [35, 32, 30, 40]),
    # Measure 7: F major - building to climax
    (24, 4, [48, 53, 57, 60], [75, 70, 65, 80]),
    # Measure 8: G major -> resolve fortissimo
    (28, 4, [47, 50, 55, 59], [95, 90, 85, 100]),
]

# Melody over the chords - wider dynamic range
melody_notes = [
    # Measure 1-2: ascending phrase (mf)
    (0, 1, 72, 85),
    (1, 0.5, 74, 75),
    (1.5, 0.5, 76, 70),
    (2, 1, 79, 100),
    (3, 1, 76, 80),
    (4, 1.5, 72, 90),
    (5.5, 0.5, 71, 65),
    (6, 1, 69, 75),
    (7, 0.5, 67, 55),
    (7.5, 0.5, 69, 60),
    # Measure 3-4: responding phrase (f)
    (8, 1, 72, 85),
    (9, 1, 77, 105),
    (10, 0.5, 76, 80),
    (10.5, 0.5, 74, 70),
    (11, 1, 72, 85),
    (12, 1, 71, 90),
    (13, 0.5, 72, 75),
    (13.5, 0.5, 74, 65),
    (14, 2, 76, 100),
    # Measure 5-6: variation (pp -> mp)
    (16, 0.5, 79, 95),
    (16.5, 0.5, 76, 70),
    (17, 1, 72, 80),
    (18, 1, 74, 60),
    (19, 1, 76, 75),
    (20, 1.5, 72, 85),
    (21.5, 0.5, 69, 50),
    (22, 1, 67, 60),
    (23, 1, 69, 55),
    # Measure 7-8: climax and resolution (ff -> fff)
    (24, 0.5, 72, 100),
    (24.5, 0.5, 74, 95),
    (25, 0.5, 76, 110),
    (25.5, 0.5, 77, 115),
    (26, 2, 79, 127),
    (28, 1, 76, 105),
    (29, 1, 74, 85),
    (30, 2, 72, 110),
]

# Build note list with role labels for visual hierarchy
starts, durations, pitches, velocities, roles = [], [], [], [], []

for beat, dur, chord_pitches, chord_vels in chords:
    for p, v in zip(chord_pitches, chord_vels, strict=True):
        starts.append(beat)
        durations.append(dur)
        pitches.append(p)
        velocities.append(min(v, 127))
        roles.append("Accompaniment")

for beat, dur, pitch, vel in melody_notes:
    starts.append(beat)
    durations.append(dur)
    pitches.append(pitch)
    velocities.append(min(vel, 127))
    roles.append("Melody")

df = pd.DataFrame({"start": starts, "duration": durations, "pitch": pitches, "velocity": velocities, "role": roles})
df["end"] = df["start"] + df["duration"]

# Melody notes are taller to stand out visually
df["pitch_top"] = np.where(df["role"] == "Melody", df["pitch"] + 0.45, df["pitch"] + 0.35)
df["pitch_bottom"] = np.where(df["role"] == "Melody", df["pitch"] - 0.45, df["pitch"] - 0.35)

# Note labels for tooltips
note_names_all = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
df["note_name"] = [f"{note_names_all[p % 12]}{p // 12 - 1}" for p in df["pitch"]]

# Determine pitch range
pitch_min = df["pitch"].min() - 1
pitch_max = df["pitch"].max() + 1

# Background rows for black keys - much more visible contrast
all_pitches = list(range(pitch_min, pitch_max + 1))
black_pitches_in_range = [p for p in all_pitches if p in black_key_pitches]
bg_rows = pd.DataFrame(
    {
        "pitch_bottom": [p - 0.5 for p in black_pitches_in_range],
        "pitch_top": [p + 0.5 for p in black_pitches_in_range],
        "xmin": [0.0] * len(black_pitches_in_range),
        "xmax": [32.0] * len(black_pitches_in_range),
    }
)

# Y-axis labels: only show note names for white keys
y_breaks = [p for p in all_pitches if p not in black_key_pitches]
white_note_letters = {0: "C", 2: "D", 4: "E", 5: "F", 7: "G", 9: "A", 11: "B"}
y_labels = [f"{white_note_letters[p % 12]}{p // 12 - 1}" for p in y_breaks]

# Beat and measure grid lines
beat_lines = pd.DataFrame({"x": [float(b) for b in range(0, 33)]})
measure_lines = pd.DataFrame({"x": [float(m) for m in range(0, 33, 4)]})

# Separate melody and accompaniment for layered rendering
df_accomp = df[df["role"] == "Accompaniment"].copy()
df_melody = df[df["role"] == "Melody"].copy()

# Plot
plot = (
    ggplot()
    # Black key background shading - dark enough to be clearly visible
    + geom_rect(
        data=bg_rows,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="pitch_bottom", ymax="pitch_top"),
        fill="#D4D4D8",
        color="rgba(0,0,0,0)",
        alpha=0.8,
    )
    # Beat grid lines (light)
    + geom_vline(data=beat_lines, mapping=aes(xintercept="x"), color="#E0E0E0", size=0.3)
    # Measure grid lines (stronger)
    + geom_vline(data=measure_lines, mapping=aes(xintercept="x"), color="#9E9E9E", size=1.0)
    # Accompaniment notes (more transparent, thinner)
    + geom_rect(
        data=df_accomp,
        mapping=aes(xmin="start", xmax="end", ymin="pitch_bottom", ymax="pitch_top", fill="velocity"),
        color="#FFFFFF",
        size=0.3,
        alpha=0.6,
        tooltips=layer_tooltips().line("@note_name").line("vel: @velocity").line("beat: @start — @end"),
    )
    # Melody notes (opaque, taller, with border)
    + geom_rect(
        data=df_melody,
        mapping=aes(xmin="start", xmax="end", ymin="pitch_bottom", ymax="pitch_top", fill="velocity"),
        color="#1A1A2E",
        size=0.6,
        alpha=1.0,
        tooltips=layer_tooltips().line("@note_name").line("vel: @velocity").line("beat: @start — @end"),
    )
    # Perceptually-uniform color scale with wide range
    + scale_fill_gradient2(low="#1E3A5F", mid="#7B2D8E", high="#FF6F00", midpoint=80, name="Velocity", limits=[30, 127])
    + scale_x_continuous(name="Time (beats)", breaks=[0, 4, 8, 12, 16, 20, 24, 28, 32], limits=[0, 32])
    + scale_y_continuous(name="Pitch", breaks=y_breaks, labels=y_labels, limits=[pitch_min - 0.5, pitch_max + 0.5])
    + labs(title="piano-roll-midi · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FAFAFA", color="#999999", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

if os.path.exists("lets-plot-images"):
    import shutil

    shutil.rmtree("lets-plot-images")
