""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.signal import stft


# Data
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_fft = 2048
hop_length = 512
n_mels = 128
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Synthesize audio: melody with harmonics
freqs_melody = [261.6, 329.6, 392.0, 523.3, 440.0, 349.2, 293.7, 261.6]
segment_len = len(t) // len(freqs_melody)
audio = np.zeros_like(t)
for i, freq in enumerate(freqs_melody):
    start = i * segment_len
    end = start + segment_len if i < len(freqs_melody) - 1 else len(t)
    seg_t = t[start:end]
    envelope = np.exp(-2.0 * (seg_t - seg_t[0]) / (seg_t[-1] - seg_t[0] + 1e-9))
    audio[start:end] = (
        0.6 * np.sin(2 * np.pi * freq * seg_t)
        + 0.3 * np.sin(2 * np.pi * 2 * freq * seg_t)
        + 0.1 * np.sin(2 * np.pi * 3 * freq * seg_t)
    ) * envelope
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
time_labels = [f"{t:.1f}" for t in times_stft]
freq_labels = [f"{f:.0f}" for f in mel_center_freqs]
mel_spec_flipped = mel_spec_db[::-1]
freq_labels_flipped = freq_labels[::-1]

df_spec = pd.DataFrame(mel_spec_flipped, index=freq_labels_flipped, columns=time_labels)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.heatmap(
    df_spec,
    ax=ax,
    cmap="magma",
    vmin=-80,
    vmax=0,
    cbar_kws={"label": "Power (dB)", "pad": 0.02},
    xticklabels=False,
    yticklabels=False,
)

# X-axis: time ticks
x_tick_seconds = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
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

# Colorbar styling
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Power (dB)", fontsize=20)

# Style
ax.set_xlabel("Time (s)", fontsize=20)
ax.set_ylabel("Frequency (mel scale)", fontsize=20)
ax.set_title("spectrogram-mel · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
