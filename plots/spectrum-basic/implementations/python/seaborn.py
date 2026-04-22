""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Create a synthetic signal with multiple frequency components
np.random.seed(42)

# Sampling parameters
sample_rate = 1000  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create signal with multiple frequency components (simulating machinery vibration)
# Fundamental frequency at 50 Hz, harmonics at 100 Hz and 150 Hz, plus some noise
signal = (
    2.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz fundamental
    + 1.2 * np.sin(2 * np.pi * 100 * t)  # 100 Hz harmonic
    + 0.8 * np.sin(2 * np.pi * 150 * t)  # 150 Hz harmonic
    + 0.3 * np.sin(2 * np.pi * 220 * t)  # 220 Hz component
    + 0.4 * np.random.randn(n_samples)  # noise
)

# Compute FFT
fft_result = np.fft.fft(signal)
frequencies = np.fft.fftfreq(n_samples, 1 / sample_rate)

# Take only positive frequencies
positive_mask = frequencies >= 0
frequencies = frequencies[positive_mask]
amplitude = np.abs(fft_result[positive_mask]) * 2 / n_samples  # Normalize amplitude

# Convert to dB scale for better visualization
amplitude_db = 20 * np.log10(amplitude + 1e-10)  # Add small value to avoid log(0)

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn lineplot for the spectrum
sns.lineplot(x=frequencies, y=amplitude_db, ax=ax, color="#306998", linewidth=2.5)

# Fill under the curve for better visualization
ax.fill_between(frequencies, amplitude_db, alpha=0.3, color="#306998")

# Mark peak frequencies
peak_indices = np.where((amplitude_db > -20) & (frequencies > 10))[0]
for idx in peak_indices:
    if amplitude_db[idx] > amplitude_db[max(0, idx - 5) : min(len(amplitude_db), idx + 6)].mean() + 5:
        ax.axvline(x=frequencies[idx], color="#FFD43B", alpha=0.5, linestyle="--", linewidth=1.5)

# Styling
ax.set_xlabel("Frequency (Hz)", fontsize=20)
ax.set_ylabel("Amplitude (dB)", fontsize=20)
ax.set_title("spectrum-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 300)  # Focus on the frequency range of interest
ax.set_ylim(-60, 10)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
