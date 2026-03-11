"""pyplots.ai
spectrogram-mel: Mel-Spectrogram for Audio Analysis
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.signal import stft


# Data - synthesize a 3-second audio signal with speech-like frequency components
np.random.seed(42)
sample_rate = 22050
duration = 3.0
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Build a rich audio signal: fundamental + harmonics with time-varying amplitude
fundamental = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * t) * np.exp(-0.3 * t)
    + 0.4 * np.sin(2 * np.pi * 440 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.5 * t))
    + 0.3 * np.sin(2 * np.pi * 880 * t) * np.exp(-0.5 * t)
    + 0.2 * np.sin(2 * np.pi * 1320 * t) * (1 - t / duration)
    + 0.15 * np.sin(2 * np.pi * 3300 * t) * np.exp(-1.0 * t)
    + 0.1 * np.random.randn(n_samples) * np.exp(-0.8 * t)
)

# Add a frequency sweep (chirp) from 500 to 4000 Hz in the middle section
chirp_mask = (t > 0.8) & (t < 2.0)
chirp_freq = 500 + (4000 - 500) * (t[chirp_mask] - 0.8) / 1.2
signal[chirp_mask] += 0.35 * np.sin(2 * np.pi * np.cumsum(chirp_freq) / sample_rate)

# STFT
n_fft = 2048
hop_length = 512
_, time_bins, Zxx = stft(signal, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)
power_spec = np.abs(Zxx) ** 2

# Mel filterbank
n_mels = 128
freq_bins = np.linspace(0, sample_rate / 2, power_spec.shape[0])

mel_low = 2595.0 * np.log10(1.0 + 0 / 700.0)
mel_high = 2595.0 * np.log10(1.0 + (sample_rate / 2) / 700.0)
mel_points = np.linspace(mel_low, mel_high, n_mels + 2)
hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)

filterbank = np.zeros((n_mels, power_spec.shape[0]))
for i in range(n_mels):
    lower, center, upper = hz_points[i], hz_points[i + 1], hz_points[i + 2]
    for j, freq in enumerate(freq_bins):
        if lower <= freq <= center and center != lower:
            filterbank[i, j] = (freq - lower) / (center - lower)
        elif center < freq <= upper and upper != center:
            filterbank[i, j] = (upper - freq) / (upper - center)

# Apply mel filterbank and convert to dB
mel_spec = filterbank @ power_spec
mel_spec_db = 10 * np.log10(np.maximum(mel_spec, 1e-10))
mel_spec_db -= mel_spec_db.max()

# Build long-form DataFrame using log-frequency for even tile spacing
mel_center_freqs = 700.0 * (10.0 ** (mel_points[1:-1] / 2595.0) - 1.0)
log_freqs = np.log10(np.maximum(mel_center_freqs, 1.0))
log_heights = np.diff(np.log10(np.maximum(hz_points, 1.0)))

time_step = time_bins[1] - time_bins[0] if len(time_bins) > 1 else hop_length / sample_rate
time_grid, mel_idx_grid = np.meshgrid(time_bins, np.arange(n_mels))

df = pd.DataFrame(
    {
        "Time (s)": time_grid.ravel(),
        "log_freq": log_freqs[mel_idx_grid.ravel()],
        "tile_height": log_heights[mel_idx_grid.ravel()],
        "Power (dB)": mel_spec_db.ravel(),
    }
)

# Y-axis tick positions at key mel band edges
y_ticks_hz = [64, 128, 256, 512, 1024, 2048, 4096, 8000]
y_ticks_hz = [f for f in y_ticks_hz if f <= sample_rate / 2]
y_ticks_log = [np.log10(f) for f in y_ticks_hz]

# Plot
plot = (
    ggplot(df, aes(x="Time (s)", y="log_freq", fill="Power (dB)"))
    + geom_tile(aes(height="tile_height"), width=time_step, color=None)
    + scale_fill_gradientn(
        colors=[
            "#000004",
            "#1b0c41",
            "#4a0c6b",
            "#781c6d",
            "#a52c60",
            "#cf4446",
            "#ed6925",
            "#fb9b06",
            "#f7d13d",
            "#fcffa4",
        ],
        name="Power (dB)",
    )
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(breaks=y_ticks_log, labels=[str(f) for f in y_ticks_hz], expand=(0, 0))
    + labs(x="Time (s)", y="Frequency (Hz)", title="spectrogram-mel \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif"),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 8}),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 8}),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_key_height=40,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#000004", color="none"),
        plot_background=element_rect(fill="#f7f7f7", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
