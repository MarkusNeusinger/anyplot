"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 120
time_seconds = np.linspace(0, 8, n_frames)

chromagram = np.random.uniform(0.05, 0.2, size=(12, n_frames))

# C major chord (C, E, G) from 0-2s and 4-6s
for t_idx in range(n_frames):
    t = time_seconds[t_idx]
    if (0 <= t < 2) or (4 <= t < 6):
        chromagram[0, t_idx] += 0.7  # C
        chromagram[4, t_idx] += 0.55  # E
        chromagram[7, t_idx] += 0.5  # G
    elif (2 <= t < 4) or (6 <= t < 8):
        chromagram[7, t_idx] += 0.7  # G
        chromagram[11, t_idx] += 0.55  # B
        chromagram[2, t_idx] += 0.5  # D

# Add smooth transitions between chords
for row in range(12):
    kernel = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
    chromagram[row] = np.convolve(chromagram[row], kernel, mode="same")

# Normalize to 0-1
chromagram = chromagram / chromagram.max()

df_chroma = pd.DataFrame(chromagram, index=pitch_classes)

# Select time labels at regular intervals
tick_positions = np.linspace(0, n_frames - 1, 9, dtype=int)
tick_labels = [f"{time_seconds[i]:.1f}" for i in tick_positions]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.heatmap(
    df_chroma,
    ax=ax,
    cmap="magma",
    vmin=0,
    vmax=1,
    cbar_kws={"label": "Energy", "shrink": 0.8},
    linewidths=0,
    rasterized=True,
)

# Style
ax.set_xlabel("Time (seconds)", fontsize=20)
ax.set_ylabel("Pitch Class", fontsize=20)
ax.set_title("heatmap-chromagram · seaborn · pyplots.ai", fontsize=24, fontweight="medium")

ax.set_xticks(tick_positions + 0.5)
ax.set_xticklabels(tick_labels, rotation=0, ha="center")
ax.tick_params(axis="both", labelsize=16, length=0)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Energy", fontsize=18)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
