""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - simulate a chromagram with chord progressions
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 120
time_seconds = np.linspace(0, 24, n_frames)
frame_width = time_seconds[1] - time_seconds[0]

# Chord templates (relative energy per pitch class)
c_major = np.array([1.0, 0.0, 0.1, 0.0, 0.8, 0.1, 0.0, 0.7, 0.0, 0.05, 0.0, 0.05])
g_major = np.array([0.1, 0.0, 0.15, 0.0, 0.05, 0.1, 0.0, 1.0, 0.0, 0.05, 0.0, 0.7])
a_minor = np.array([0.7, 0.0, 0.1, 0.0, 0.8, 0.1, 0.0, 0.05, 0.0, 1.0, 0.0, 0.05])
f_major = np.array([0.8, 0.0, 0.05, 0.0, 0.1, 1.0, 0.0, 0.05, 0.0, 0.7, 0.0, 0.05])

# Build chromagram: cycle through C -> G -> Am -> F progression
energy = np.zeros((12, n_frames))
chord_sequence = [c_major, g_major, a_minor, f_major]
frames_per_chord = n_frames // len(chord_sequence)

for i, chord in enumerate(chord_sequence):
    start = i * frames_per_chord
    end = start + frames_per_chord if i < len(chord_sequence) - 1 else n_frames
    for j in range(start, end):
        blend = np.random.uniform(0.7, 1.0)
        noise = np.random.uniform(0.0, 0.15, 12)
        energy[:, j] = chord * blend + noise

# Smooth transitions between chords
for i in range(1, n_frames):
    energy[:, i] = 0.7 * energy[:, i] + 0.3 * energy[:, i - 1]

# Normalize to 0-1
energy = energy / energy.max()

# Build long-form dataframe with bin edges for proper rect rendering
rows = []
for t_idx, t_val in enumerate(time_seconds):
    for p_idx, pitch in enumerate(pitch_classes):
        rows.append(
            {
                "t1": round(t_val, 3),
                "t2": round(t_val + frame_width, 3),
                "Pitch Class": pitch,
                "Energy": round(energy[p_idx, t_idx], 3),
            }
        )

df = pd.DataFrame(rows)

# Plot
heatmap = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(
            "t1:Q",
            title="Time (seconds)",
            axis=alt.Axis(labelFontSize=15, titleFontSize=20, titlePadding=12, values=list(range(0, 25, 2))),
            scale=alt.Scale(domain=[0, 24.2]),
        ),
        x2="t2:Q",
        y=alt.Y(
            "Pitch Class:N",
            title="Pitch Class",
            sort=pitch_classes,
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, titlePadding=12),
        ),
        color=alt.Color(
            "Energy:Q",
            scale=alt.Scale(scheme="inferno"),
            legend=alt.Legend(
                title="Energy",
                titleFontSize=16,
                labelFontSize=14,
                gradientLength=350,
                gradientThickness=16,
                titlePadding=8,
                offset=12,
                direction="vertical",
            ),
        ),
        tooltip=[
            alt.Tooltip("Pitch Class:N"),
            alt.Tooltip("t1:Q", title="Time (s)", format=".1f"),
            alt.Tooltip("Energy:Q", format=".3f"),
        ],
    )
)

# Combine and configure
chart = (
    heatmap.properties(
        width=1600,
        height=900,
        title=alt.Title(
            "heatmap-chromagram · altair · pyplots.ai",
            subtitle="Pitch class energy over time · C → G → Am → F chord progression",
            fontSize=26,
            subtitleFontSize=16,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
