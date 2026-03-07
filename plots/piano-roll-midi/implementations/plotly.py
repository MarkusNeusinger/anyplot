""" pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data - C major chord progression (I-V-vi-IV) with melody over 4 measures
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BLACK_KEY_INDICES = {1, 3, 6, 8, 10}

notes = [
    # (start_beat, duration, midi_pitch, velocity)
    # Measure 1 - C major chord (close voicing with melody)
    (0.0, 2.0, 48, 80),  # C3 bass
    (0.0, 2.0, 55, 75),  # G3
    (0.0, 2.0, 60, 70),  # C4 (mid)
    (0.0, 2.0, 64, 72),  # E4 (mid)
    (0.0, 0.5, 72, 100),  # C5 melody
    (0.5, 0.5, 74, 95),  # D5 melody
    (1.0, 1.0, 76, 110),  # E5 melody
    (2.0, 2.0, 48, 78),  # C3 bass
    (2.0, 2.0, 55, 73),  # G3
    (2.0, 2.0, 60, 68),  # C4 (mid)
    (2.0, 2.0, 64, 70),  # E4 (mid)
    (2.0, 0.75, 79, 105),  # G5 melody
    (2.75, 0.25, 76, 85),  # E5 melody
    (3.0, 1.0, 77, 100),  # F5 melody
    # Measure 2 - G major chord
    (4.0, 2.0, 47, 82),  # B2 bass
    (4.0, 2.0, 55, 76),  # G3
    (4.0, 2.0, 59, 72),  # B3 (mid)
    (4.0, 2.0, 62, 74),  # D4 (mid)
    (4.0, 0.5, 76, 108),  # E5 melody
    (4.5, 0.5, 74, 90),  # D5 melody
    (5.0, 1.0, 72, 100),  # C5 melody
    (6.0, 2.0, 47, 80),  # B2 bass
    (6.0, 2.0, 55, 74),  # G3
    (6.0, 2.0, 59, 70),  # B3 (mid)
    (6.0, 2.0, 62, 72),  # D4 (mid)
    (6.0, 1.0, 67, 95),  # G4 melody
    (7.0, 0.5, 69, 88),  # A4 melody
    (7.5, 0.5, 71, 92),  # B4 melody
    # Measure 3 - A minor chord
    (8.0, 2.0, 45, 85),  # A2 bass
    (8.0, 2.0, 52, 78),  # E3
    (8.0, 2.0, 57, 72),  # A3 (mid)
    (8.0, 2.0, 60, 74),  # C4 (mid)
    (8.0, 1.0, 72, 112),  # C5 melody
    (9.0, 0.5, 74, 96),  # D5 melody
    (9.5, 0.5, 76, 90),  # E5 melody
    (10.0, 2.0, 45, 83),  # A2 bass
    (10.0, 2.0, 52, 76),  # E3
    (10.0, 2.0, 57, 70),  # A3 (mid)
    (10.0, 2.0, 64, 72),  # E4 (mid)
    (10.0, 1.5, 76, 105),  # E5 melody
    (11.5, 0.5, 74, 88),  # D5 melody
    # Measure 4 - F major chord
    (12.0, 2.0, 53, 88),  # F3 bass
    (12.0, 2.0, 57, 80),  # A3
    (12.0, 2.0, 60, 74),  # C4 (mid)
    (12.0, 2.0, 65, 76),  # F4 (mid)
    (12.0, 1.0, 72, 115),  # C5 melody
    (13.0, 0.5, 71, 92),  # B4 melody
    (13.5, 0.5, 69, 85),  # A4 melody
    (14.0, 2.0, 53, 86),  # F3 bass
    (14.0, 2.0, 57, 78),  # A3
    (14.0, 2.0, 60, 72),  # C4 (mid)
    (14.0, 2.0, 65, 74),  # F4 (mid)
    (14.0, 2.0, 72, 120),  # C5 melody (final)
]

starts = np.array([n[0] for n in notes])
durations = np.array([n[1] for n in notes])
pitches = np.array([n[2] for n in notes])
velocities = np.array([n[3] for n in notes])

pitch_min = int(pitches.min()) - 1
pitch_max = int(pitches.max()) + 1
total_beats = 16
beats_per_measure = 4

# Classify notes: melody (highest pitch per onset) vs accompaniment
is_melody = np.zeros(len(notes), dtype=bool)
unique_starts = np.unique(starts)
for s in unique_starts:
    mask = starts == s
    idx = np.where(mask)[0]
    max_pitch_idx = idx[np.argmax(pitches[idx])]
    is_melody[max_pitch_idx] = True

# Normalize velocities for color mapping
vel_min = float(velocities.min())
vel_max = float(velocities.max())
vel_normalized = (velocities - vel_min) / (vel_max - vel_min)

# Plasma colorscale key stops for np.interp (avoids custom function)
_t = [0, 0.25, 0.5, 0.75, 1.0]
_r, _g, _b = [13, 126, 229, 253, 240], [8, 3, 107, 191, 249], [135, 168, 93, 36, 33]
note_colors = [
    f"rgb({int(np.interp(v, _t, _r))},{int(np.interp(v, _t, _g))},{int(np.interp(v, _t, _b))})" for v in vel_normalized
]

# Plot
fig = go.Figure()

# Background shading for black keys
for p in range(pitch_min, pitch_max + 1):
    if (p % 12) in BLACK_KEY_INDICES:
        fig.add_shape(
            type="rect",
            x0=0,
            x1=total_beats,
            y0=p - 0.5,
            y1=p + 0.5,
            fillcolor="rgba(30, 30, 60, 0.07)",
            line={"width": 0},
            layer="below",
        )

# Measure boundary lines (thicker, more visible)
for m in range(total_beats // beats_per_measure + 1):
    fig.add_shape(
        type="line",
        x0=m * beats_per_measure,
        x1=m * beats_per_measure,
        y0=pitch_min - 0.5,
        y1=pitch_max + 0.5,
        line={"color": "rgba(0, 0, 0, 0.35)", "width": 2.5},
        layer="below",
    )

# Beat grid lines (thinner)
for b in range(total_beats + 1):
    if b % beats_per_measure != 0:
        fig.add_shape(
            type="line",
            x0=b,
            x1=b,
            y0=pitch_min - 0.5,
            y1=pitch_max + 0.5,
            line={"color": "rgba(0, 0, 0, 0.08)", "width": 1, "dash": "dot"},
            layer="below",
        )

# Horizontal pitch grid lines
for p in range(pitch_min, pitch_max + 2):
    fig.add_shape(
        type="line",
        x0=0,
        x1=total_beats,
        y0=p - 0.5,
        y1=p - 0.5,
        line={"color": "rgba(0, 0, 0, 0.05)", "width": 1},
        layer="below",
    )

# Note rectangles with visual hierarchy: melody thicker/opaque, accompaniment thinner
for i in range(len(notes)):
    height = 0.42 if is_melody[i] else 0.35
    opacity = 0.95 if is_melody[i] else 0.78
    border_w = 2.0 if is_melody[i] else 1.0
    fig.add_shape(
        type="rect",
        x0=starts[i],
        x1=starts[i] + durations[i],
        y0=pitches[i] - height,
        y1=pitches[i] + height,
        fillcolor=note_colors[i],
        line={"color": "rgba(255,255,255,0.8)", "width": border_w},
        layer="above",
        opacity=opacity,
    )

# Invisible scatter for hover info and colorbar
hover_labels = [
    f"{'♪ ' if is_melody[i] else ''}{NOTE_NAMES[p % 12]}{p // 12 - 1}"
    f"<br>Beat: {s:.1f}<br>Duration: {d:.2g} beats<br>Velocity: {v}"
    for i, (s, d, p, v) in enumerate(notes)
]
fig.add_trace(
    go.Scatter(
        x=starts + durations / 2,
        y=pitches,
        mode="markers",
        marker={
            "size": 1,
            "opacity": 0,
            "color": velocities,
            "colorscale": "Plasma",
            "colorbar": {
                "title": {"text": "Velocity<br>(MIDI 0–127)", "font": {"size": 18}},
                "tickfont": {"size": 16},
                "thickness": 20,
                "len": 0.6,
            },
            "cmin": int(vel_min),
            "cmax": int(vel_max),
        },
        text=hover_labels,
        hoverinfo="text",
        showlegend=False,
    )
)

# Y-axis: show only natural notes (white keys) to reduce density
pitch_range = list(range(pitch_min, pitch_max + 1))
white_key_pitches = [p for p in pitch_range if (p % 12) not in BLACK_KEY_INDICES]
white_key_labels = [f"{NOTE_NAMES[p % 12]}{p // 12 - 1}" for p in white_key_pitches]

# X-axis: measure.beat labels
beat_ticks = list(range(total_beats + 1))
beat_labels = [f"M{b // beats_per_measure + 1}.{b % beats_per_measure + 1}" for b in beat_ticks]

# Style
fig.update_layout(
    title={
        "text": "piano-roll-midi · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Beat Position (Measure.Beat)", "font": {"size": 22}},
        "tickvals": beat_ticks,
        "ticktext": beat_labels,
        "tickfont": {"size": 16},
        "range": [-0.3, total_beats + 0.3],
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Pitch (MIDI Note Name)", "font": {"size": 22}},
        "tickvals": white_key_pitches,
        "ticktext": white_key_labels,
        "tickfont": {"size": 16},
        "range": [pitch_min - 0.8, pitch_max + 0.8],
        "showgrid": False,
    },
    template="plotly_white",
    margin={"l": 100, "r": 120, "t": 100, "b": 80},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
