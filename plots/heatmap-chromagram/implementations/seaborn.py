""" pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-17
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn styling
sns.set_style("dark", {"axes.facecolor": "#1a1a2e"})
sns.set_context("talk", font_scale=1.0)

# Data
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 160
duration = 8.0
time_seconds = np.linspace(0, duration, n_frames)

chromagram = np.random.uniform(0.03, 0.15, size=(12, n_frames))

# Chord progression: C major (0-2s, 6-7s), G major (2-4s), Am (4-6s), F major (7-8s)
for t_idx in range(n_frames):
    t = time_seconds[t_idx]
    if (0 <= t < 2) or (6 <= t < 7):
        # C major: C, E, G
        chromagram[0, t_idx] += 0.75  # C
        chromagram[4, t_idx] += 0.55  # E
        chromagram[7, t_idx] += 0.50  # G
    elif 2 <= t < 4:
        # G major: G, B, D
        chromagram[7, t_idx] += 0.75  # G
        chromagram[11, t_idx] += 0.55  # B
        chromagram[2, t_idx] += 0.50  # D
    elif 4 <= t < 6:
        # A minor: A, C, E
        chromagram[9, t_idx] += 0.70  # A
        chromagram[0, t_idx] += 0.50  # C
        chromagram[4, t_idx] += 0.55  # E
    elif 7 <= t <= 8:
        # F major: F, A, C
        chromagram[5, t_idx] += 0.70  # F
        chromagram[9, t_idx] += 0.50  # A
        chromagram[0, t_idx] += 0.45  # C

# Add passing tones between chord transitions
for t_idx in range(n_frames):
    t = time_seconds[t_idx]
    # Passing tones near transitions
    if 1.8 <= t < 2.2:
        chromagram[1, t_idx] += 0.2  # C# passing tone
    if 3.8 <= t < 4.2:
        chromagram[6, t_idx] += 0.2  # F# passing tone
    if 5.8 <= t < 6.2:
        chromagram[10, t_idx] += 0.15  # A# passing tone

# Smooth transitions with convolution
for row in range(12):
    kernel = np.array([0.05, 0.15, 0.3, 0.3, 0.15, 0.05])
    chromagram[row] = np.convolve(chromagram[row], kernel, mode="same")

# Normalize to 0-1
chromagram = chromagram / chromagram.max()

df_chroma = pd.DataFrame(chromagram, index=pitch_classes)

# Calculate tick positions for round integer seconds
tick_times = np.arange(0, int(duration) + 1)
tick_positions = [t / duration * n_frames for t in tick_times]
tick_labels = [f"{int(t)}" for t in tick_times]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0f0f23")

hm = sns.heatmap(
    df_chroma,
    ax=ax,
    cmap="magma",
    vmin=0,
    vmax=1,
    cbar_kws={"label": "Energy", "shrink": 0.75, "aspect": 30, "pad": 0.02},
    linewidths=0,
    rasterized=True,
    xticklabels=False,
)

# Spine removal
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#555555")
ax.spines["left"].set_color("#555555")

# Axis styling
ax.set_xlabel("Time (seconds)", fontsize=20, color="#cccccc", labelpad=12)
ax.set_ylabel("Pitch Class", fontsize=20, color="#cccccc", labelpad=12)
ax.set_title("heatmap-chromagram · seaborn · pyplots.ai", fontsize=24, fontweight="bold", color="#e8e8e8", pad=20)

ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, rotation=0, ha="center")
ax.tick_params(axis="both", labelsize=16, length=0, colors="#bbbbbb")
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=16)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14, colors="#bbbbbb")
cbar.set_label("Energy", fontsize=18, color="#cccccc")
cbar.outline.set_edgecolor("#555555")

fig.patch.set_facecolor("#0f0f23")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#0f0f23")
