"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-17
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    (0, 30, "C maj", {"C": 0.9, "E": 0.75, "G": 0.8}),
    (30, 60, "G maj", {"G": 0.92, "B": 0.78, "D": 0.72}),
    (60, 90, "A min", {"A": 0.88, "C": 0.76, "E": 0.82}),
    (90, 120, "F maj", {"F": 0.85, "A": 0.74, "C": 0.80}),
]

for start, end, _, notes in chord_regions:
    for note, energy in notes.items():
        idx = pitch_classes.index(note)
        chroma[idx, start:end] = energy + np.random.normal(0, 0.05, end - start)
        # Harmonic bleeding into adjacent frames for realism
        if start > 0:
            chroma[idx, start - 3 : start] = np.linspace(0.1, energy * 0.7, 3)
        if end < n_frames:
            tail = min(3, n_frames - end)
            chroma[idx, end : end + tail] = np.linspace(energy * 0.7, 0.1, tail)

chroma = np.clip(chroma, 0, 1)

# Custom colormap: deep charcoal → teal → warm gold (music-inspired palette)
cmap_colors = ["#0d0d1a", "#0f2027", "#1a535c", "#4ecdc4", "#f7b733", "#ffe066"]
cmap = mcolors.LinearSegmentedColormap.from_list("chromagram", cmap_colors, N=256)

# PowerNorm to enhance contrast between quiet and active regions
norm = mcolors.PowerNorm(gamma=0.7, vmin=0, vmax=1)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0a0a12")
ax.set_facecolor("#0a0a12")

time_edges = np.linspace(0, 8, n_frames + 1)
pitch_edges = np.arange(n_pitches + 1) - 0.5

im = ax.pcolormesh(time_edges, pitch_edges, chroma, cmap=cmap, norm=norm, shading="flat", rasterized=True)

# Chord region labels and dividers for storytelling
for start, end, label, _ in chord_regions:
    t_mid = (time_seconds[start] + time_seconds[min(end - 1, n_frames - 1)]) / 2
    ax.text(
        t_mid,
        n_pitches - 0.15,
        label,
        ha="center",
        va="top",
        fontsize=15,
        fontstyle="italic",
        color="#c0c0c0",
        fontweight="medium",
    )
    if start > 0:
        t_boundary = time_seconds[start]
        ax.axvline(t_boundary, color="#555555", linewidth=0.8, linestyle="--", alpha=0.6)

# Style
ax.set_yticks(np.arange(n_pitches))
ax.set_yticklabels(pitch_classes, fontsize=16, fontfamily="monospace", color="#d0d0d0")
ax.set_xlabel("Time (seconds)", fontsize=20, color="#d0d0d0", labelpad=10)
ax.set_ylabel("Pitch Class", fontsize=20, color="#d0d0d0", labelpad=10)
ax.set_title("heatmap-chromagram · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", color="#e8e8e8", pad=20)
ax.tick_params(axis="both", labelsize=16, colors="#a0a0a0")
ax.xaxis.set_major_locator(mticker.MultipleLocator(1))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.25))
ax.tick_params(axis="x", which="minor", length=2, color="#444444")

for spine in ax.spines.values():
    spine.set_visible(False)

# Colorbar with custom formatting
cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02, aspect=30)
cbar.set_label("Energy", fontsize=18, labelpad=12, color="#d0d0d0")
cbar.ax.tick_params(labelsize=16, colors="#a0a0a0")
cbar.outline.set_visible(False)
cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
cbar.ax.set_yticklabels(["0.0", "0.25", "0.5", "0.75", "1.0"])

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
