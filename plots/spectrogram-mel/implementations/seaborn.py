""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-11
"""

import os
import sys


# Avoid local seaborn.py shadowing the real seaborn package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.signal import stft


sys.path.insert(0, _script_dir)

# Seaborn theming for distinctive look
sns.set_theme(
    style="dark",
    rc={
        "axes.facecolor": "#1a1a2e",
        "figure.facecolor": "#0f0f1a",
        "text.color": "#e0e0e0",
        "axes.labelcolor": "#e0e0e0",
        "xtick.color": "#c0c0c0",
        "ytick.color": "#c0c0c0",
    },
)
sns.set_context("talk", font_scale=1.1)

# Data
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_fft = 2048
hop_length = 512
n_mels = 128
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Synthesize audio: melody with harmonics and percussive transients
note_names = ["C4", "E4", "G4", "C5", "A4", "F4", "D4", "C4"]
freqs_melody = [261.6, 329.6, 392.0, 523.3, 440.0, 349.2, 293.7, 261.6]
segment_len = len(t) // len(freqs_melody)
audio = np.zeros_like(t)
for i, freq in enumerate(freqs_melody):
    start = i * segment_len
    end = start + segment_len if i < len(freqs_melody) - 1 else len(t)
    seg_t = t[start:end]
    envelope = np.exp(-2.0 * (seg_t - seg_t[0]) / (seg_t[-1] - seg_t[0] + 1e-9))
    # Add click transient at note onset
    onset_env = np.exp(-80.0 * (seg_t - seg_t[0]))
    audio[start:end] = (
        0.6 * np.sin(2 * np.pi * freq * seg_t)
        + 0.3 * np.sin(2 * np.pi * 2 * freq * seg_t)
        + 0.1 * np.sin(2 * np.pi * 3 * freq * seg_t)
    ) * envelope + 0.15 * onset_env * np.sin(2 * np.pi * 5 * freq * seg_t)
audio += 0.02 * np.random.randn(len(audio))

# Compute STFT
freqs_stft, times_stft, Zxx = stft(audio, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)
power_spectrum = np.abs(Zxx) ** 2

# Mel filterbank
f_min, f_max = 0.0, sample_rate / 2.0
mel_min = 2595.0 * np.log10(1.0 + f_min / 700.0)
mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
bin_indices = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

filterbank = np.zeros((n_mels, len(freqs_stft)))
for m in range(1, n_mels + 1):
    f_left, f_center, f_right = bin_indices[m - 1], bin_indices[m], bin_indices[m + 1]
    for k in range(f_left, f_center):
        if f_center != f_left:
            filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)
    for k in range(f_center, f_right):
        if f_right != f_center:
            filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)

# Apply mel filterbank and convert to dB
mel_spec = filterbank @ power_spectrum
mel_spec_db = 10 * np.log10(np.maximum(mel_spec, 1e-10))
mel_spec_db -= mel_spec_db.max()

# Build DataFrame for seaborn heatmap (flip so low freq at bottom)
mel_center_freqs = 700.0 * (10.0 ** (mel_points[1:-1] / 2595.0) - 1.0)
mel_spec_flipped = mel_spec_db[::-1]

df_spec = pd.DataFrame(mel_spec_flipped, index=np.arange(n_mels), columns=np.arange(mel_spec_flipped.shape[1]))

# Use seaborn color palette to build custom colormap
cmap_colors = sns.color_palette("magma", as_cmap=True)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
hm = sns.heatmap(
    df_spec,
    ax=ax,
    cmap=cmap_colors,
    vmin=-80,
    vmax=0,
    cbar_kws={"label": "Power (dB)", "pad": 0.015, "aspect": 30, "shrink": 0.85},
    xticklabels=False,
    yticklabels=False,
    rasterized=True,
)

# X-axis: time ticks
x_tick_seconds = np.arange(0, 4.5, 0.5)
x_tick_positions = [np.argmin(np.abs(times_stft - s)) for s in x_tick_seconds]
ax.set_xticks(x_tick_positions)
ax.set_xticklabels([f"{s:.1f}" for s in x_tick_seconds])

# Y-axis: Hz labels at key mel band positions (flipped coordinates)
tick_freqs = [100, 200, 500, 1000, 2000, 4000, 8000]
tick_positions_y = []
tick_labels_y = []
for freq in tick_freqs:
    idx = np.argmin(np.abs(mel_center_freqs - freq))
    tick_positions_y.append(n_mels - 1 - idx)
    tick_labels_y.append(f"{freq // 1000}k Hz" if freq >= 1000 else f"{freq} Hz")

ax.set_yticks(tick_positions_y)
ax.set_yticklabels(tick_labels_y)

# Colorbar refinement
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14, colors="#c0c0c0")
cbar.set_label("Power (dB)", fontsize=18, color="#e0e0e0")
cbar.outline.set_edgecolor("#444466")
cbar.outline.set_linewidth(0.8)

# Note boundary lines and labels for storytelling
for i in range(1, len(freqs_melody)):
    boundary_time = i * segment_len / sample_rate
    x_pos = np.argmin(np.abs(times_stft - boundary_time))
    ax.axvline(x=x_pos, color="#ffffff", alpha=0.12, linewidth=0.8, linestyle="--")

# Label notes at top of plot
for i, name in enumerate(note_names):
    mid_time = (i + 0.5) * segment_len / sample_rate
    x_pos = np.argmin(np.abs(times_stft - mid_time))
    ax.text(x_pos, -1.5, name, ha="center", va="bottom", fontsize=12, color="#ffcc66", fontweight="bold", alpha=0.85)

# Harmonic bracket annotations on the last note (C4) to show overtone series
last_note_mid = (len(freqs_melody) - 0.5) * segment_len / sample_rate
x_anno = np.argmin(np.abs(times_stft - last_note_mid))
for h, label in [(1, "f\u2080"), (2, "2f\u2080"), (3, "3f\u2080")]:
    freq_h = freqs_melody[0] * h
    mel_idx = np.argmin(np.abs(mel_center_freqs - freq_h))
    y_pos = n_mels - 1 - mel_idx
    ax.plot(x_anno, y_pos, marker="<", color="#ffcc66", markersize=6, alpha=0.85)
    ax.text(
        x_anno + 3,
        y_pos,
        label,
        fontsize=11,
        color="#ffcc66",
        fontweight="bold",
        alpha=0.9,
        va="center",
        ha="left",
        bbox={"boxstyle": "round,pad=0.15", "facecolor": "#1a1a2e", "edgecolor": "none", "alpha": 0.7},
    )

# Style refinement
ax.set_xlabel("Time (s)", fontsize=20, labelpad=10)
ax.set_ylabel("Frequency (mel scale)", fontsize=20, labelpad=10)
ax.set_title(
    "spectrogram-mel \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="bold", pad=20, color="#ffffff"
)
ax.tick_params(axis="both", labelsize=16, length=4, width=0.8)

# Remove heavy spines, add subtle border
for spine in ax.spines.values():
    spine.set_edgecolor("#444466")
    spine.set_linewidth(0.8)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
