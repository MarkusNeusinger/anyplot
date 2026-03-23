""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_raster,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Synthetic chromagram: C major -> G major -> A minor -> F major
np.random.seed(42)
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_pitches = len(pitch_classes)
n_frames = 200
frame_duration = 0.05
time_seconds = np.arange(n_frames) * frame_duration

# Base energy (low background noise)
chroma = np.random.uniform(0.02, 0.10, (n_pitches, n_frames))

# Chord definitions (indices into pitch_classes)
chords = {
    "C_major": [0, 4, 7],  # C, E, G
    "G_major": [7, 11, 2],  # G, B, D
    "A_minor": [9, 0, 4],  # A, C, E
    "F_major": [5, 9, 0],  # F, A, C
}

# Assign chords to time segments with varying intensities
segments = [(0, 50, "C_major"), (50, 100, "G_major"), (100, 150, "A_minor"), (150, 200, "F_major")]

for start, end, chord_name in segments:
    root, third, fifth = chords[chord_name]
    chroma[root, start:end] += np.random.uniform(0.7, 0.95, end - start)
    chroma[third, start:end] += np.random.uniform(0.5, 0.75, end - start)
    chroma[fifth, start:end] += np.random.uniform(0.55, 0.8, end - start)

# Smooth transitions between chords
kernel = np.ones(5) / 5
for i in range(n_pitches):
    chroma[i] = np.convolve(chroma[i], kernel, mode="same")

# Normalize to 0-1
chroma = chroma / chroma.max()

# Build long-form DataFrame with numeric axes for geom_raster
time_grid, pitch_grid = np.meshgrid(time_seconds, np.arange(n_pitches))
df = pd.DataFrame(
    {
        "time": time_grid.ravel(),
        "pitch_idx": pitch_grid.ravel(),
        "energy": np.round(chroma.ravel(), 4),
        "pitch_name": np.repeat(pitch_classes, n_frames),
    }
)

# Inferno colormap - extended color stops for smoother perceptual gradients
inferno_colors = [
    "#000004",
    "#0d0829",
    "#1b0c41",
    "#300a5b",
    "#420a68",
    "#560f6d",
    "#6a176e",
    "#7e1e6c",
    "#932667",
    "#a72f5f",
    "#bc3754",
    "#cd4247",
    "#dd513a",
    "#e8642b",
    "#f37819",
    "#f98e09",
    "#fca50a",
    "#fbbe23",
    "#f6d746",
    "#f1ed71",
    "#fcffa4",
]

# Plot
plot = (
    ggplot(df, aes(x="time", y="pitch_idx", fill="energy"))
    + geom_raster(
        tooltips=layer_tooltips()
        .format("@time", ".2f")
        .format("@energy", ".3f")
        .line("@pitch_name at @time s")
        .line("Energy: @energy")
    )
    + scale_fill_gradientn(
        colors=inferno_colors, name="Energy", guide=guide_colorbar(barwidth=14, barheight=260, nbin=256)
    )
    + scale_x_continuous(
        name="Time (seconds)", breaks=list(np.arange(0, n_frames * frame_duration + 0.5, 1.0)), expand=[0, 0]
    )
    + scale_y_continuous(name="Pitch Class", breaks=list(range(n_pitches)), labels=pitch_classes, expand=[0, 0])
    + labs(
        title="heatmap-chromagram · letsplot · pyplots.ai", subtitle="Chord progression: C maj → G maj → A min → F maj"
    )
    + theme(
        plot_title=element_text(size=28, face="bold", color="#1a1a2e", margin=[0, 0, 4, 0]),
        plot_subtitle=element_text(size=18, color="#5a5a7a", face="italic", margin=[0, 0, 10, 0]),
        axis_title_x=element_text(size=20, color="#2d2d44", margin=[10, 0, 0, 0]),
        axis_title_y=element_text(size=20, color="#2d2d44", margin=[0, 10, 0, 0]),
        axis_text_x=element_text(size=16, color="#3d3d55"),
        axis_text_y=element_text(size=16, face="bold", color="#2d2d44"),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        legend_text=element_text(size=14, color="#3d3d55"),
        legend_title=element_text(size=16, face="bold", color="#2d2d44"),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="#0a0a1a", color="#0a0a1a"),
        plot_background=element_rect(fill="#f5f5f0", color="#f5f5f0"),
        plot_margin=[40, 30, 20, 20],
        legend_background=element_rect(fill="#f5f5f0", color="#f5f5f0"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
