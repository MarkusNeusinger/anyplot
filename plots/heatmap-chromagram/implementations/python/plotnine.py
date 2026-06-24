"""anyplot.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-06-24
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    geom_vline,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap — single-polarity energy data (brand green → blue)
SEQ_LOW = "#009E73"  # Imprint position 1 — low energy
SEQ_HIGH = "#4467A3"  # Imprint position 3 — high energy

# Data — C → G → Am → F chord progression chromagram
np.random.seed(42)
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 80
duration_sec = 8.0
time_step = duration_sec / n_frames
time_frames = np.linspace(0, duration_sec, n_frames)

chroma = np.random.uniform(0.02, 0.15, (12, n_frames))

chord_regions = [
    (0, 20, [0, 4, 7], "C"),  # C major: C-E-G
    (20, 40, [7, 11, 2], "G"),  # G major: G-B-D
    (40, 60, [9, 0, 4], "Am"),  # A minor: A-C-E
    (60, 80, [5, 9, 0], "F"),  # F major: F-A-C
]

for start, end, notes, _ in chord_regions:
    for note in notes:
        chroma[note, start:end] += np.random.uniform(0.55, 0.85, end - start)
    for note in notes:
        harmonic = (note + 7) % 12
        chroma[harmonic, start:end] += np.random.uniform(0.1, 0.25, end - start)

chroma = chroma / chroma.max()

for boundary in [20, 40, 60]:
    idx = max(0, boundary - 2)
    end_idx = min(n_frames, boundary + 2)
    for col in range(idx, end_idx):
        blend = (col - idx) / (end_idx - idx)
        chroma[:, col] = chroma[:, col] * (0.7 + 0.3 * blend)

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

chord_labels = pd.DataFrame(
    {
        "Time (s)": [1.0, 3.0, 5.0, 7.0],
        "Pitch Class": pd.Categorical(["B"] * 4, categories=pitch_classes[::-1], ordered=True),
        "label": ["C maj", "G maj", "A min", "F maj"],
        "alpha": [0.9] * 4,
    }
)

boundary_times = [time_frames[20], time_frames[40], time_frames[60]]

title = "heatmap-chromagram · python · plotnine · anyplot.ai"

# Plot
plot = (
    ggplot(df, aes(x="Time (s)", y="Pitch Class", fill="Energy"))
    + geom_tile(width=time_step, height=1)
    + geom_vline(xintercept=boundary_times, linetype="dashed", color="#FFFFFF", alpha=0.6, size=0.8)
    + geom_text(
        aes(x="Time (s)", y="Pitch Class", label="label", alpha="alpha"),
        data=chord_labels,
        inherit_aes=False,
        color="#FFFFFF",
        size=3.5,
        fontweight="bold",
        va="bottom",
        nudge_y=0.3,
    )
    + scale_alpha_identity()
    + scale_fill_gradient(
        low=SEQ_LOW,
        high=SEQ_HIGH,
        name="Energy",
        breaks=[0.0, 0.25, 0.50, 0.75, 1.00],
        labels=["0.00", "0.25", "0.50", "0.75", "1.00"],
    )
    + scale_x_continuous(
        expand=(0, 0),
        breaks=np.arange(0, duration_sec + 0.5, 1.0),
        labels=[f"{x:.0f}" for x in np.arange(0, duration_sec + 0.5, 1.0)],
    )
    + scale_y_discrete(expand=(0, 0))
    + labs(
        x="Time (s)",
        y="Pitch Class",
        title=title,
        subtitle="Pitch class energy over time: C → G → Am → F chord progression",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(family="sans-serif", color=INK),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK, margin={"b": 4}),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT, margin={"b": 6}),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 6}),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 4}),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT, ha="right", margin={"r": 2}),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_key_height=40,
        legend_key_width=12,
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
