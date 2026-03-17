""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 120
frame_duration = 0.05
time_frames = np.arange(n_frames) * frame_duration

# Chord profiles (energy distribution across 12 pitch classes)
c_major = np.array([1.0, 0.05, 0.1, 0.05, 0.8, 0.1, 0.05, 0.7, 0.05, 0.1, 0.05, 0.1])
g_major = np.array([0.1, 0.05, 0.7, 0.05, 0.1, 0.05, 0.05, 1.0, 0.05, 0.1, 0.05, 0.8])
a_minor = np.array([0.7, 0.05, 0.1, 0.05, 0.8, 0.1, 0.05, 0.1, 0.05, 1.0, 0.05, 0.1])
f_major = np.array([0.8, 0.05, 0.1, 0.05, 0.1, 1.0, 0.05, 0.1, 0.05, 0.7, 0.05, 0.1])

# Build chromagram with chord progression: C -> G -> Am -> F
chord_names = ["C maj", "G maj", "A min", "F maj"]
chords = [c_major, g_major, a_minor, f_major]
segment_length = n_frames // len(chords)

energy = np.zeros((12, n_frames))
for i, chord in enumerate(chords):
    start = i * segment_length
    end = start + segment_length if i < len(chords) - 1 else n_frames
    for t in range(start, end):
        noise = np.random.normal(0, 0.06, 12)
        energy[:, t] = np.clip(chord + noise, 0, 1.2)

# Smooth transitions between chords
for i in range(1, len(chords)):
    boundary = i * segment_length
    blend_width = 4
    for offset in range(-blend_width, blend_width):
        t = boundary + offset
        if 0 <= t < n_frames:
            alpha = (offset + blend_width) / (2 * blend_width)
            prev_chord = chords[i - 1]
            curr_chord = chords[i]
            blended = (1 - alpha) * prev_chord + alpha * curr_chord
            noise = np.random.normal(0, 0.04, 12)
            energy[:, t] = np.clip(blended + noise, 0, 1.2)

# Custom colorscale: dark navy -> deep purple -> hot magenta -> warm orange -> bright gold
custom_colorscale = [
    [0.0, "#0d0628"],
    [0.15, "#1b0c42"],
    [0.3, "#44146e"],
    [0.45, "#721f81"],
    [0.55, "#b5367a"],
    [0.7, "#e55c30"],
    [0.85, "#f9a242"],
    [1.0, "#fcffa4"],
]

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=energy,
        x=np.round(time_frames, 2),
        y=pitch_classes,
        colorscale=custom_colorscale,
        zmin=0,
        zmax=1.2,
        colorbar={
            "title": {"text": "Energy", "font": {"size": 20, "family": "Arial Black"}},
            "tickfont": {"size": 16, "family": "Arial"},
            "thickness": 20,
            "len": 0.75,
            "outlinewidth": 0,
            "tickvals": [0, 0.3, 0.6, 0.9, 1.2],
        },
        hoverongaps=False,
        hovertemplate="<b>%{y}</b> at %{x}s<br>Energy: %{z:.3f}<extra></extra>",
        xgap=0.5,
        ygap=1,
    )
)

# Add vertical lines and annotations for chord sections
for i in range(len(chords)):
    start_time = i * segment_length * frame_duration
    end_time = (i + 1) * segment_length * frame_duration if i < len(chords) - 1 else n_frames * frame_duration
    mid_time = (start_time + end_time) / 2

    # Chord label annotation above the heatmap
    fig.add_annotation(
        x=mid_time,
        y=1.08,
        yref="paper",
        text=f"<b>{chord_names[i]}</b>",
        showarrow=False,
        font={"size": 20, "color": "#444444", "family": "Arial"},
    )

    # Dashed vertical separator lines between chord sections
    if i > 0:
        boundary_time = start_time
        fig.add_shape(
            type="line",
            x0=boundary_time,
            x1=boundary_time,
            y0=-0.5,
            y1=11.5,
            line={"color": "rgba(255,255,255,0.6)", "width": 2, "dash": "dot"},
        )

# Bracket line connecting chord labels
fig.add_shape(
    type="line",
    x0=0,
    x1=n_frames * frame_duration - frame_duration,
    y0=1.04,
    y1=1.04,
    yref="paper",
    line={"color": "#bbbbbb", "width": 1.5},
)

# Style
fig.update_layout(
    title={
        "text": "heatmap-chromagram · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial Black", "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {"text": "Time (seconds)", "font": {"size": 22, "family": "Arial"}, "standoff": 12},
        "tickfont": {"size": 16, "family": "Arial"},
        "showgrid": False,
        "dtick": 0.5,
        "zeroline": False,
        "showline": True,
        "linecolor": "#cccccc",
        "linewidth": 1,
        "ticks": "outside",
        "tickcolor": "#cccccc",
        "ticklen": 6,
    },
    yaxis={
        "title": {"text": "Pitch Class", "font": {"size": 22, "family": "Arial"}, "standoff": 8},
        "tickfont": {"size": 16, "family": "Arial", "color": "#333333"},
        "showgrid": False,
        "categoryorder": "array",
        "categoryarray": pitch_classes,
        "zeroline": False,
        "showline": True,
        "linecolor": "#cccccc",
        "linewidth": 1,
        "ticks": "outside",
        "tickcolor": "#cccccc",
        "ticklen": 6,
    },
    template="plotly_white",
    plot_bgcolor="#0d0628",
    paper_bgcolor="#fafafa",
    margin={"l": 90, "r": 50, "t": 110, "b": 70},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
