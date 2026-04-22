""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import signal


# Data - chirp signal with increasing frequency
np.random.seed(42)
sample_rate = 4000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Create a chirp signal: frequency increases from 100 Hz to 800 Hz
f0, f1 = 100, 800
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")

# Add some noise for realism
chirp_signal += np.random.randn(len(chirp_signal)) * 0.1

# Compute spectrogram using scipy
nperseg = 256  # Window size
noverlap = 200  # Overlap for smoother visualization
frequencies, times, Sxx = signal.spectrogram(chirp_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Convert to dB scale for better visualization
Sxx_dB = 10 * np.log10(Sxx + 1e-10)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Flip data vertically so low frequencies are at bottom (standard convention)
Sxx_dB_flipped = np.flipud(Sxx_dB)

# Use seaborn heatmap for the spectrogram visualization
sns.heatmap(
    Sxx_dB_flipped,
    ax=ax,
    cmap="viridis",
    cbar=True,
    cbar_kws={"label": "Power (dB)", "shrink": 0.8},
    xticklabels=False,
    yticklabels=False,
    rasterized=True,
)

# Set proper axis labels and ticks
# Calculate tick positions for time axis
time_tick_positions = np.linspace(0, Sxx_dB.shape[1], 5)
time_tick_labels = [f"{t:.1f}" for t in np.linspace(0, duration, 5)]
ax.set_xticks(time_tick_positions)
ax.set_xticklabels(time_tick_labels, fontsize=16)

# Calculate tick positions for frequency axis (low to high, bottom to top)
freq_tick_positions = np.linspace(0, Sxx_dB.shape[0], 5)
freq_tick_labels = [f"{int(f)}" for f in np.linspace(frequencies[0], frequencies[-1], 5)]
ax.set_yticks(freq_tick_positions)
ax.set_yticklabels(freq_tick_labels[::-1], fontsize=16)

# Labels and styling
ax.set_xlabel("Time (s)", fontsize=20)
ax.set_ylabel("Frequency (Hz)", fontsize=20)
ax.set_title("spectrogram-basic · seaborn · pyplots.ai", fontsize=24, pad=20)

# Adjust colorbar label size
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.ax.yaxis.label.set_size(18)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
