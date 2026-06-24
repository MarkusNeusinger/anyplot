"""anyplot.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Imprint sequential colormap for single-polarity energy data
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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
        chromagram[0, t_idx] += 0.75  # C
        chromagram[4, t_idx] += 0.55  # E
        chromagram[7, t_idx] += 0.50  # G
    elif 2 <= t < 4:
        chromagram[7, t_idx] += 0.75  # G
        chromagram[11, t_idx] += 0.55  # B
        chromagram[2, t_idx] += 0.50  # D
    elif 4 <= t < 6:
        chromagram[9, t_idx] += 0.70  # A
        chromagram[0, t_idx] += 0.50  # C
        chromagram[4, t_idx] += 0.55  # E
    elif 7 <= t <= 8:
        chromagram[5, t_idx] += 0.70  # F
        chromagram[9, t_idx] += 0.50  # A
        chromagram[0, t_idx] += 0.45  # C

# Passing tones near chord transitions
for t_idx in range(n_frames):
    t = time_seconds[t_idx]
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

chromagram = chromagram / chromagram.max()
df_chroma = pd.DataFrame(chromagram, index=pitch_classes)

tick_times = np.arange(0, int(duration) + 1)
tick_positions = [t / duration * n_frames for t in tick_times]
tick_labels = [str(int(t)) for t in tick_times]

# Plot — square canvas for heatmap (2400×2400)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(
    df_chroma,
    ax=ax,
    cmap=imprint_seq,
    vmin=0,
    vmax=1,
    cbar_kws={"label": "Energy", "shrink": 0.82, "aspect": 22, "pad": 0.02},
    linewidths=0,
    rasterized=True,
    xticklabels=False,
)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["left"].set_color(INK_SOFT)

# Axis labels and title
ax.set_xlabel("Time (seconds)", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("Pitch Class", fontsize=10, color=INK, labelpad=8)
ax.set_title("heatmap-chromagram · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)

ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, rotation=0, ha="center")
ax.tick_params(axis="both", labelsize=8, length=0, colors=INK_SOFT)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.set_facecolor(PAGE_BG)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label("Energy", fontsize=10, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

# Chord transition annotations — vertical dashed lines + chord labels above plot
chord_bounds = [0, 40, 80, 120, 140, 160]
chord_names = ["C", "G", "Am", "C", "F"]
for bound in chord_bounds[1:-1]:
    ax.axvline(x=bound, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.65, zorder=5)
for start, end, name in zip(chord_bounds[:-1], chord_bounds[1:], chord_names, strict=False):
    center_frac = ((start + end) / 2) / n_frames
    ax.text(center_frac, 1.012, name, ha="center", va="bottom", fontsize=7.5, color=INK_SOFT, transform=ax.transAxes)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
