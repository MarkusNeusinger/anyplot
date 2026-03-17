"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Data - simulate chromagram for a musical passage with chord changes
np.random.seed(42)
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 80
duration_sec = 8.0
time_frames = np.linspace(0, duration_sec, n_frames)

# Build chromagram matrix (12 pitch classes x n_frames)
chroma = np.random.uniform(0.02, 0.15, (12, n_frames))

# Simulate chord progression: C major (C-E-G) -> G major (G-B-D) -> Am (A-C-E) -> F major (F-A-C)
chord_regions = [
    (0, 20, [0, 4, 7]),  # C major: C=0, E=4, G=7
    (20, 40, [7, 11, 2]),  # G major: G=7, B=11, D=2
    (40, 60, [9, 0, 4]),  # A minor: A=9, C=0, E=4
    (60, 80, [5, 9, 0]),  # F major: F=5, A=9, C=0
]

for start, end, notes in chord_regions:
    for note in notes:
        chroma[note, start:end] += np.random.uniform(0.55, 0.85, end - start)
    # Add weaker harmonics for realism
    for note in notes:
        harmonic = (note + 7) % 12
        chroma[harmonic, start:end] += np.random.uniform(0.1, 0.25, end - start)

# Normalize to 0-1
chroma = chroma / chroma.max()

# Smooth transitions between chords
for boundary in [20, 40, 60]:
    idx = max(0, boundary - 2)
    end_idx = min(n_frames, boundary + 2)
    for col in range(idx, end_idx):
        blend = (col - idx) / (end_idx - idx)
        chroma[:, col] = chroma[:, col] * (0.7 + 0.3 * blend)

# Build long-form DataFrame
time_idx, pitch_idx = np.meshgrid(np.arange(n_frames), np.arange(12))
df = pd.DataFrame(
    {
        "Time (s)": time_frames[time_idx.ravel()],
        "Pitch Class": pd.Categorical(
            [pitch_classes[i] for i in pitch_idx.ravel()], categories=pitch_classes[::-1], ordered=True
        ),
        "Energy": chroma.ravel(),
    }
)

# Plot
plot = (
    ggplot(df, aes(x="Time (s)", y="Pitch Class", fill="Energy"))
    + geom_tile()
    + scale_fill_gradientn(
        colors=["#0d0887", "#5302a3", "#8b0aa5", "#b83289", "#db5c68", "#f48849", "#febd2a", "#f0f921"], name="Energy"
    )
    + scale_x_continuous(expand=(0, 0))
    + scale_y_discrete(expand=(0, 0))
    + labs(
        x="Time (s)",
        y="Pitch Class",
        title="heatmap-chromagram · plotnine · pyplots.ai",
        subtitle="Chromagram showing pitch class energy over time (C → G → Am → F progression)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif"),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 2}),
        plot_subtitle=element_text(size=16, ha="center", color="#555555", margin={"b": 8}),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 8}),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16, ha="right", margin={"r": 4}),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_key_height=40,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="#f7f7f7", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
