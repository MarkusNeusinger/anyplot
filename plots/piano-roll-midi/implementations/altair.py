"""pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: A short melodic phrase with chords (C major progression with melody)
np.random.seed(42)

# MIDI note name mapping
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


# Build a musical phrase: chords + melody over 8 measures (32 beats in 4/4)
notes = []

# Bass line (lower octave)
bass_pattern = [
    (0, 2, 48),
    (2, 2, 52),
    (4, 2, 53),
    (6, 2, 48),
    (8, 2, 50),
    (10, 2, 48),
    (12, 2, 45),
    (14, 2, 47),
    (16, 2, 48),
    (18, 2, 52),
    (20, 2, 53),
    (22, 2, 48),
    (24, 2, 50),
    (26, 2, 48),
    (28, 2, 47),
    (30, 2, 48),
]
for start, dur, pitch in bass_pattern:
    notes.append({"start": start, "duration": dur, "pitch": pitch, "velocity": np.random.randint(60, 80)})

# Chord voicings (mid range)
chord_hits = [
    (0, [60, 64, 67]),
    (4, [60, 65, 69]),
    (8, [62, 65, 69]),
    (12, [59, 62, 67]),
    (16, [60, 64, 67]),
    (20, [60, 65, 69]),
    (24, [62, 65, 69]),
    (28, [59, 64, 67]),
]
for start, pitches in chord_hits:
    for p in pitches:
        notes.append({"start": start, "duration": 3.5, "pitch": p, "velocity": np.random.randint(50, 75)})

# Melody (upper range, varying rhythms and velocities)
melody = [
    (0, 1, 72, 100),
    (1, 0.5, 74, 90),
    (1.5, 0.5, 76, 85),
    (2, 1, 77, 105),
    (3, 1, 76, 95),
    (4, 1.5, 74, 100),
    (5.5, 0.5, 72, 80),
    (6, 1, 71, 90),
    (7, 0.5, 72, 85),
    (7.5, 0.5, 74, 80),
    (8, 2, 76, 110),
    (10, 1, 74, 90),
    (11, 1, 72, 85),
    (12, 1.5, 71, 95),
    (13.5, 0.5, 72, 80),
    (14, 1, 74, 100),
    (15, 1, 76, 95),
    (16, 1, 77, 115),
    (17, 0.5, 79, 100),
    (17.5, 0.5, 77, 90),
    (18, 1, 76, 105),
    (19, 0.5, 74, 85),
    (19.5, 0.5, 72, 80),
    (20, 1.5, 74, 100),
    (21.5, 0.5, 76, 90),
    (22, 2, 77, 110),
    (24, 1, 79, 120),
    (25, 1, 77, 105),
    (26, 1, 76, 100),
    (27, 1, 74, 90),
    (28, 1.5, 72, 95),
    (29.5, 0.5, 74, 85),
    (30, 2, 72, 110),
]
for start, dur, pitch, vel in melody:
    notes.append({"start": start, "duration": dur, "pitch": pitch, "velocity": vel})

df = pd.DataFrame(notes)
df["end"] = df["start"] + df["duration"]

# Create note labels (e.g., C4, D#5)
df["note_name"] = df["pitch"].apply(lambda p: f"{NOTE_NAMES[p % 12]}{p // 12 - 1}")

# Determine pitch range with margin
pitch_min = df["pitch"].min() - 1
pitch_max = df["pitch"].max() + 1
all_pitches = list(range(pitch_min, pitch_max + 1))

# Black key indicators for background shading
black_key_semitones = {1, 3, 6, 8, 10}

# Create background rows for piano key coloring
bg_rows = []
for p in all_pitches:
    is_black = (p % 12) in black_key_semitones
    bg_rows.append(
        {"pitch": p, "note_name": f"{NOTE_NAMES[p % 12]}{p // 12 - 1}", "is_black": is_black, "start": 0, "end": 32}
    )

bg_df = pd.DataFrame(bg_rows)

# Sort order for y-axis (low pitch at bottom, high at top — reversed for Altair)
pitch_labels = [f"{NOTE_NAMES[p % 12]}{p // 12 - 1}" for p in reversed(all_pitches)]

# Background: alternating shading for black/white keys
background = (
    alt.Chart(bg_df)
    .mark_bar()
    .encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, 32])),
        x2="end:Q",
        y=alt.Y("note_name:N", sort=pitch_labels),
        color=alt.condition(alt.datum.is_black, alt.value("#e0e0e0"), alt.value("#f8f8f8")),
    )
)

# Beat grid lines (vertical rules at each beat)
beat_positions = pd.DataFrame({"beat": list(range(33))})
beat_grid = (
    alt.Chart(beat_positions).mark_rule(strokeDash=[2, 2], opacity=0.3, color="#999999").encode(x=alt.X("beat:Q"))
)

# Measure lines (stronger lines every 4 beats)
measure_positions = pd.DataFrame({"beat": list(range(0, 33, 4))})
measure_grid = (
    alt.Chart(measure_positions).mark_rule(opacity=0.6, color="#666666", strokeWidth=1.5).encode(x=alt.X("beat:Q"))
)

# Piano roll notes
note_bars = (
    alt.Chart(df)
    .mark_bar(cornerRadius=3, stroke="#222222", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "start:Q",
            title="Beat",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=20,
                values=list(range(0, 33, 4)),
                labelExpr="'M' + (datum.value / 4 + 1)",
            ),
        ),
        x2="end:Q",
        y=alt.Y("note_name:N", sort=pitch_labels, title="Pitch", axis=alt.Axis(labelFontSize=14, titleFontSize=20)),
        color=alt.Color(
            "velocity:Q",
            title="Velocity",
            scale=alt.Scale(scheme="viridis", domain=[40, 127]),
            legend=alt.Legend(titleFontSize=18, labelFontSize=14, orient="right", gradientLength=300),
        ),
        tooltip=[
            alt.Tooltip("note_name:N", title="Note"),
            alt.Tooltip("start:Q", title="Start (beat)"),
            alt.Tooltip("duration:Q", title="Duration"),
            alt.Tooltip("velocity:Q", title="Velocity"),
        ],
    )
)

# Layer everything together
chart = (
    (background + beat_grid + measure_grid + note_bars)
    .properties(
        width=1500,
        height=850,
        title=alt.Title(text="piano-roll-midi · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
