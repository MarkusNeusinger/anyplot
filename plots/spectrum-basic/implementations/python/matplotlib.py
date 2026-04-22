""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Generate synthetic signal with multiple frequency components
np.random.seed(42)

# Sampling parameters
sample_rate = 1000  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create signal with multiple frequency components
# 50 Hz fundamental, 120 Hz harmonic, 200 Hz component, plus noise
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz fundamental
    + 0.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz harmonic
    + 0.3 * np.sin(2 * np.pi * 200 * t)  # 200 Hz component
    + 0.1 * np.random.randn(n_samples)  # Noise
)

# Compute FFT
fft_result = np.fft.fft(signal)
frequencies = np.fft.fftfreq(n_samples, 1 / sample_rate)

# Take only positive frequencies
positive_mask = frequencies >= 0
frequencies = frequencies[positive_mask]
amplitude = np.abs(fft_result[positive_mask]) * 2 / n_samples  # Normalized amplitude

# Convert to dB scale (with floor to avoid log of zero)
amplitude_db = 20 * np.log10(amplitude + 1e-10)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot spectrum
ax.plot(frequencies, amplitude_db, linewidth=2.5, color="#306998", alpha=0.9)

# Fill under the curve for visual emphasis
ax.fill_between(frequencies, amplitude_db, alpha=0.3, color="#306998")

# Mark peak frequencies
peaks = [50, 120, 200]
for peak_freq in peaks:
    idx = np.argmin(np.abs(frequencies - peak_freq))
    ax.axvline(x=peak_freq, color="#FFD43B", linestyle="--", linewidth=2, alpha=0.8)
    ax.scatter(
        [frequencies[idx]], [amplitude_db[idx]], s=200, color="#FFD43B", zorder=5, edgecolors="black", linewidths=1.5
    )
    ax.annotate(
        f"{peak_freq} Hz",
        xy=(frequencies[idx], amplitude_db[idx]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=14,
        fontweight="bold",
        color="#306998",
    )

# Styling
ax.set_xlabel("Frequency (Hz)", fontsize=20)
ax.set_ylabel("Amplitude (dB)", fontsize=20)
ax.set_title("spectrum-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits
ax.set_xlim(0, 300)
ax.set_ylim(-60, 10)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
