""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Generate a chirp signal (frequency increases over time)
np.random.seed(42)
sample_rate = 4000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Create chirp signal: frequency sweeps from 100 Hz to 1000 Hz
f0 = 100  # Start frequency
f1 = 1000  # End frequency
signal = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))

# Add a second component: a tone burst in the middle
burst_start = int(0.8 * sample_rate)
burst_end = int(1.2 * sample_rate)
burst_freq = 500  # Hz
signal[burst_start:burst_end] += 0.7 * np.sin(2 * np.pi * burst_freq * t[burst_start:burst_end])

# Add some noise
signal += 0.1 * np.random.randn(len(signal))

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Compute and plot spectrogram
# NFFT controls frequency resolution, noverlap controls time resolution
_Pxx, _freqs, _times, im = ax.specgram(
    signal,
    Fs=sample_rate,
    NFFT=256,
    noverlap=200,
    cmap="viridis",
    vmin=-80,  # dB floor
)

# Add colorbar
cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label("Power/Frequency (dB/Hz)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("Time (s)", fontsize=20)
ax.set_ylabel("Frequency (Hz)", fontsize=20)
ax.set_title("spectrogram-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
