"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - simulate a chromagram for a short musical passage
# Pattern: C major chord (C, E, G) → G major chord (G, B, D) → Am (A, C, E) → F major (F, A, C)
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_pitches = len(pitch_classes)
n_frames = 120
time_seconds = np.linspace(0, 8, n_frames)

# Base low energy across all pitches
chroma = np.random.uniform(0.02, 0.12, (n_pitches, n_frames))

# Define chord regions with realistic energy patterns
chord_regions = [
    (0, 30, {"C": 0.9, "E": 0.75, "G": 0.8}),  # C major
    (30, 60, {"G": 0.92, "B": 0.78, "D": 0.72}),  # G major
    (60, 90, {"A": 0.88, "C": 0.76, "E": 0.82}),  # A minor
    (90, 120, {"F": 0.85, "A": 0.74, "C": 0.80}),  # F major
]

for start, end, notes in chord_regions:
    for note, energy in notes.items():
        idx = pitch_classes.index(note)
        chroma[idx, start:end] = energy + np.random.normal(0, 0.05, end - start)
        # Add harmonics bleeding into adjacent frames for realism
        if start > 0:
            chroma[idx, start - 3 : start] = np.linspace(0.1, energy * 0.7, 3)
        if end < n_frames:
            tail = min(3, n_frames - end)
            chroma[idx, end : end + tail] = np.linspace(energy * 0.7, 0.1, tail)

chroma = np.clip(chroma, 0, 1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

time_edges = np.linspace(0, 8, n_frames + 1)
pitch_edges = np.arange(n_pitches + 1) - 0.5

im = ax.pcolormesh(time_edges, pitch_edges, chroma, cmap="inferno", shading="flat", vmin=0, vmax=1)

# Style
ax.set_yticks(np.arange(n_pitches))
ax.set_yticklabels(pitch_classes, fontsize=16)
ax.set_xlabel("Time (seconds)", fontsize=20)
ax.set_ylabel("Pitch Class", fontsize=20)
ax.set_title("heatmap-chromagram · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02, aspect=30)
cbar.set_label("Energy", fontsize=18, labelpad=12)
cbar.ax.tick_params(labelsize=16)
cbar.outline.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
