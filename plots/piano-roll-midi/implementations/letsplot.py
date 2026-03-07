""" pyplots.ai
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
chords = [
    # Measure 1: C major
    (0, 4, [48, 52, 55, 60], [90, 85, 80, 100]),
    # Measure 2: A minor
    (4, 4, [48, 52, 57, 60], [85, 80, 75, 95]),
    # Measure 3: F major
    (8, 4, [48, 53, 57, 60], [88, 82, 78, 98]),
    # Measure 4: G major
    (12, 4, [47, 50, 55, 59], [92, 87, 83, 105]),
    # Measure 5: C major
    (16, 4, [48, 52, 55, 60], [80, 75, 70, 90]),
    # Measure 6: A minor
    (20, 4, [48, 52, 57, 60], [75, 70, 65, 85]),
    # Measure 7: F major
    (24, 4, [48, 53, 57, 60], [95, 90, 85, 110]),
    # Measure 8: G major -> resolve
    (28, 4, [47, 50, 55, 59], [100, 95, 90, 115]),
]

# Melody over the chords
melody_notes = [
    # Measure 1-2: ascending phrase
    (0, 1, 72, 100),
    (1, 0.5, 74, 90),
    (1.5, 0.5, 76, 85),
    (2, 1, 79, 110),
    (3, 1, 76, 95),
    (4, 1.5, 72, 105),
    (5.5, 0.5, 71, 80),
    (6, 1, 69, 90),
    (7, 0.5, 67, 75),
    (7.5, 0.5, 69, 85),
    # Measure 3-4: responding phrase
    (8, 1, 72, 100),
    (9, 1, 77, 115),
    (10, 0.5, 76, 90),
    (10.5, 0.5, 74, 85),
    (11, 1, 72, 95),
    (12, 1, 71, 100),
    (13, 0.5, 72, 90),
    (13.5, 0.5, 74, 80),
    (14, 2, 76, 110),
    # Measure 5-6: variation
    (16, 0.5, 79, 105),
    (16.5, 0.5, 76, 90),
    (17, 1, 72, 100),
    (18, 1, 74, 85),
    (19, 1, 76, 95),
    (20, 1.5, 72, 100),
    (21.5, 0.5, 69, 80),
    (22, 1, 67, 90),
    (23, 1, 69, 88),
    # Measure 7-8: climax and resolution
    (24, 0.5, 72, 110),
    (24.5, 0.5, 74, 105),
    (25, 0.5, 76, 115),
    (25.5, 0.5, 77, 120),
    (26, 2, 79, 127),
    (28, 1, 76, 110),
    (29, 1, 74, 95),
    (30, 2, 72, 120),
]

# Build note list
starts, durations, pitches, velocities = [], [], [], []

for beat, dur, chord_pitches, chord_vels in chords:
    for p, v in zip(chord_pitches, chord_vels, strict=True):
        starts.append(beat)
        durations.append(dur)
        pitches.append(p)
        velocities.append(min(v, 127))

for beat, dur, pitch, vel in melody_notes:
    starts.append(beat)
    durations.append(dur)
    pitches.append(pitch)
    velocities.append(min(vel, 127))

df = pd.DataFrame({"start": starts, "duration": durations, "pitch": pitches, "velocity": velocities})
df["end"] = df["start"] + df["duration"]
df["pitch_top"] = df["pitch"] + 0.4
df["pitch_bottom"] = df["pitch"] - 0.4

# Determine pitch range
pitch_min = df["pitch"].min() - 1
pitch_max = df["pitch"].max() + 1

# Background rows for black keys
all_pitches = list(range(pitch_min, pitch_max + 1))
bg_rows = pd.DataFrame(
    {
        "pitch_bottom": [p - 0.5 for p in all_pitches if p in black_key_pitches],
        "pitch_top": [p + 0.5 for p in all_pitches if p in black_key_pitches],
        "xmin": [0] * len([p for p in all_pitches if p in black_key_pitches]),
        "xmax": [32] * len([p for p in all_pitches if p in black_key_pitches]),
    }
)

# Y-axis labels: only show note names for white keys
y_breaks = [p for p in all_pitches if p not in black_key_pitches]
white_note_letters = {0: "C", 2: "D", 4: "E", 5: "F", 7: "G", 9: "A", 11: "B"}
y_labels = [f"{white_note_letters[p % 12]}{p // 12 - 1}" for p in y_breaks]

# Beat and measure grid lines
beat_lines = pd.DataFrame({"x": [float(b) for b in range(0, 33)]})
measure_lines = pd.DataFrame({"x": [float(m) for m in range(0, 33, 4)]})

# Plot
plot = (
    ggplot()
    # Black key background shading
    + geom_rect(
        data=bg_rows,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="pitch_bottom", ymax="pitch_top"),
        fill="#F0F0F0",
        color="rgba(0,0,0,0)",
        alpha=0.6,
    )
    # Beat grid lines (light)
    + geom_vline(data=beat_lines, mapping=aes(xintercept="x"), color="#E0E0E0", size=0.4)
    # Measure grid lines (stronger)
    + geom_vline(data=measure_lines, mapping=aes(xintercept="x"), color="#BDBDBD", size=0.8)
    # Note rectangles colored by velocity
    + geom_rect(
        data=df,
        mapping=aes(xmin="start", xmax="end", ymin="pitch_bottom", ymax="pitch_top", fill="velocity"),
        color="#FFFFFF",
        size=0.5,
        alpha=0.9,
    )
    + scale_fill_gradient(low="#306998", high="#E53935", name="Velocity", limits=[40, 127])
    + scale_x_continuous(
        name="Time (beats)",
        breaks=[0, 4, 8, 12, 16, 20, 24, 28, 32],
        labels=["1", "5", "9", "13", "17", "21", "25", "29", "33"],
        limits=[0, 32],
    )
    + scale_y_continuous(name="Pitch", breaks=y_breaks, labels=y_labels, limits=[pitch_min - 0.5, pitch_max + 0.5])
    + labs(title="piano-roll-midi \u00b7 letsplot \u00b7 pyplots.ai")
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
        panel_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

if os.path.exists("lets-plot-images"):
    import shutil

    shutil.rmtree("lets-plot-images")
