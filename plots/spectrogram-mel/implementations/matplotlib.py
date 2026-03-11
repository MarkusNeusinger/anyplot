""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.ticker import FuncFormatter


# Data - synthesize a rich audio signal with melody-like frequency components
np.random.seed(42)
sample_rate = 22050
duration = 4.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Melody: frequency sweeps and harmonics simulating speech-like signal
melody_freq = 220 + 80 * np.sin(2 * np.pi * 0.5 * t)
audio_signal = 0.5 * np.sin(2 * np.pi * melody_freq * t)
audio_signal += 0.3 * np.sin(2 * np.pi * 2 * melody_freq * t)
audio_signal += 0.15 * np.sin(2 * np.pi * 3 * melody_freq * t)

# Add percussive bursts at regular intervals
for onset in np.arange(0.0, duration, 0.5):
    onset_idx = int(onset * sample_rate)
    burst_len = int(0.05 * sample_rate)
    end_idx = min(onset_idx + burst_len, n_samples)
    envelope = np.exp(-np.linspace(0, 8, end_idx - onset_idx))
    audio_signal[onset_idx:end_idx] += 0.4 * envelope * np.random.randn(end_idx - onset_idx)

# Add a rising tone in the second half
rising_freq = np.linspace(500, 2000, n_samples)
rising_mask = np.zeros(n_samples)
rising_mask[n_samples // 2 :] = np.linspace(0, 0.3, n_samples - n_samples // 2)
audio_signal += rising_mask * np.sin(2 * np.pi * rising_freq * t)

# Normalize
audio_signal = audio_signal / np.max(np.abs(audio_signal))

# Compute mel-spectrogram manually
n_fft = 2048
hop_length = 512
n_mels = 128

# STFT
n_frames = 1 + (n_samples - n_fft) // hop_length
window = np.hanning(n_fft)
stft_matrix = np.zeros((n_fft // 2 + 1, n_frames))
for i in range(n_frames):
    start = i * hop_length
    frame = audio_signal[start : start + n_fft] * window
    spectrum = np.fft.rfft(frame)
    stft_matrix[:, i] = np.abs(spectrum) ** 2

# Mel filter bank (vectorized)
f_min = 0.0
f_max = sample_rate / 2.0
mel_min = 2595.0 * np.log10(1.0 + f_min / 700.0)
mel_max = 2595.0 * np.log10(1.0 + f_max / 700.0)
mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
fft_freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)

mel_filterbank = np.zeros((n_mels, len(fft_freqs)))
for m in range(n_mels):
    f_left, f_center, f_right = hz_points[m], hz_points[m + 1], hz_points[m + 2]
    up_slope = np.where(
        (fft_freqs >= f_left) & (fft_freqs <= f_center) & (f_center > f_left),
        (fft_freqs - f_left) / (f_center - f_left),
        0.0,
    )
    down_slope = np.where(
        (fft_freqs > f_center) & (fft_freqs <= f_right) & (f_right > f_center),
        (f_right - fft_freqs) / (f_right - f_center),
        0.0,
    )
    mel_filterbank[m] = up_slope + down_slope

# Apply mel filter bank and convert to dB
mel_spectrogram = mel_filterbank @ stft_matrix
mel_spectrogram = np.maximum(mel_spectrogram, 1e-10)
mel_spectrogram_db = 10.0 * np.log10(mel_spectrogram)
ref_db = mel_spectrogram_db.max()
mel_spectrogram_db = mel_spectrogram_db - ref_db

# Time and frequency axes
time_axis = np.arange(n_frames) * hop_length / sample_rate
mel_freqs = hz_points[1:-1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0a0a0f")
ax.set_facecolor("#0a0a0f")

img = ax.pcolormesh(
    time_axis,
    np.arange(n_mels),
    mel_spectrogram_db,
    cmap="magma",
    shading="gouraud",
    norm=Normalize(vmin=-80, vmax=0),
    rasterized=True,
)

# Y-axis: show Hz labels at mel band edges
tick_hz_values = [64, 128, 256, 512, 1024, 2048, 4096, 8000]
tick_mel_indices = []
tick_labels = []
for hz in tick_hz_values:
    if hz <= f_max:
        idx = np.argmin(np.abs(mel_freqs - hz))
        tick_mel_indices.append(idx)
        if hz >= 1000:
            tick_labels.append(f"{hz / 1000:.0f}k")
        else:
            tick_labels.append(f"{hz}")
ax.set_yticks(tick_mel_indices)
ax.set_yticklabels(tick_labels)

# X-axis formatting with FuncFormatter
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))

# Colorbar with musically meaningful dB levels
cbar = fig.colorbar(img, ax=ax, pad=0.02, aspect=30)
cbar.set_label("Power (dB)", fontsize=20, color="#cccccc")
cbar.set_ticks([0, -10, -20, -40, -60, -80])
cbar.set_ticklabels(["0", "−10", "−20", "−40", "−60", "−80"])
cbar.ax.tick_params(labelsize=14, colors="#cccccc")
cbar.outline.set_edgecolor("#333333")
cbar.outline.set_linewidth(0.5)

# Subtle horizontal reference lines at key frequency bands
speech_band_idx = np.argmin(np.abs(mel_freqs - 300))
ax.axhline(y=speech_band_idx, color="#ffffff", alpha=0.08, linewidth=0.6, linestyle="--")
harmonic_band_idx = np.argmin(np.abs(mel_freqs - 1000))
ax.axhline(y=harmonic_band_idx, color="#ffffff", alpha=0.08, linewidth=0.6, linestyle="--")

# Style
text_color = "#cccccc"
ax.set_xlabel("Time (s)", fontsize=20, color=text_color, labelpad=10)
ax.set_ylabel("Frequency (Hz)", fontsize=20, color=text_color, labelpad=10)
ax.set_title("spectrogram-mel · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", color="#e8e8e8", pad=16)
ax.tick_params(axis="both", labelsize=16, colors=text_color)
ax.tick_params(axis="x", which="both", length=4, width=0.8, color="#555555")
ax.tick_params(axis="y", which="both", length=4, width=0.8, color="#555555")

# Remove all spines for cleaner look
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
