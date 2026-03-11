""" pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data
np.random.seed(42)
sample_rate = 22050
duration = 3.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Synthesize a melody: C4, E4, G4, C5 with harmonics
melody_freqs = [261.6, 329.6, 392.0, 523.3]
audio_signal = np.zeros(n_samples)
for i, freq in enumerate(melody_freqs):
    start = int(i * n_samples / len(melody_freqs))
    end = int((i + 1) * n_samples / len(melody_freqs))
    segment_t = t[start:end]
    envelope = np.sin(np.linspace(0, np.pi, end - start))
    audio_signal[start:end] += 0.5 * envelope * np.sin(2 * np.pi * freq * segment_t)
    for harmonic in [2, 3, 5]:
        audio_signal[start:end] += (0.15 / harmonic) * envelope * np.sin(2 * np.pi * freq * harmonic * segment_t)

audio_signal += 0.02 * np.random.randn(n_samples)

# STFT via numpy
n_fft = 2048
hop_length = 512
n_mels = 128

window = np.hanning(n_fft)
n_frames = 1 + (n_samples - n_fft) // hop_length
stft_matrix = np.zeros((n_fft // 2 + 1, n_frames))
for frame_idx in range(n_frames):
    start_sample = frame_idx * hop_length
    frame = audio_signal[start_sample : start_sample + n_fft] * window
    spectrum = np.fft.rfft(frame)
    stft_matrix[:, frame_idx] = np.abs(spectrum) ** 2

times = np.arange(n_frames) * hop_length / sample_rate
frequencies = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)

# Mel filter bank
mel_low = 2595 * np.log10(1 + 0 / 700)
mel_high = 2595 * np.log10(1 + (sample_rate / 2) / 700)
mel_points = np.linspace(mel_low, mel_high, n_mels + 2)
hz_points = 700 * (10 ** (mel_points / 2595) - 1)
fft_bins = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

mel_filterbank = np.zeros((n_mels, len(frequencies)))
for m in range(1, n_mels + 1):
    f_left = fft_bins[m - 1]
    f_center = fft_bins[m]
    f_right = fft_bins[m + 1]
    for k in range(f_left, min(f_center, len(frequencies))):
        if f_center != f_left:
            mel_filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)
    for k in range(f_center, min(f_right, len(frequencies))):
        if f_right != f_center:
            mel_filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)

mel_spec = mel_filterbank @ stft_matrix
mel_spec_db = 10 * np.log10(mel_spec + 1e-10)

# Mel band center frequencies in Hz (for y-axis labels)
mel_center_hz = 700 * (10 ** (np.linspace(mel_low, mel_high, n_mels) / 2595) - 1)

# Downsample for geom_tile performance
time_step = max(1, len(times) // 200)
mel_step = max(1, n_mels // 96)
times_ds = times[::time_step]
mel_indices_ds = np.arange(0, n_mels, mel_step)
mel_spec_ds = mel_spec_db[::mel_step][:, ::time_step]

# Build DataFrame using mel band index as y-axis
time_grid, mel_idx_grid = np.meshgrid(times_ds, mel_indices_ds)
df = pd.DataFrame(
    {"Time (s)": time_grid.flatten(), "Mel Band": mel_idx_grid.flatten(), "Power (dB)": mel_spec_ds.flatten()}
)

# Y-axis breaks: map Hz values to mel band indices
label_hz = [100, 200, 500, 1000, 2000, 5000, 10000]
label_mel_vals = [2595 * np.log10(1 + f / 700) for f in label_hz]
mel_range = np.linspace(mel_low, mel_high, n_mels)
label_indices = [float(np.interp(mv, mel_range, np.arange(n_mels))) for mv in label_mel_vals]
label_strs = ["100", "200", "500", "1k", "2k", "5k", "10k"]

# Plot
plot = (
    ggplot(df, aes(x="Time (s)", y="Mel Band", fill="Power (dB)"))
    + geom_tile()
    + scale_fill_viridis(option="inferno", name="Power (dB)")
    + scale_y_continuous(breaks=label_indices, labels=label_strs)
    + labs(x="Time (s)", y="Frequency (Hz)", title="spectrogram-mel \u00b7 letsplot \u00b7 pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
    )
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
