""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 for annotations

# Generate synthetic signal with multiple frequency components
np.random.seed(42)

# Sampling parameters
sample_rate = 1000  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create signal with multiple frequency components
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
amplitude = np.abs(fft_result[positive_mask]) * 2 / n_samples

# Convert to dB scale
amplitude_db = 20 * np.log10(amplitude + 1e-10)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot spectrum line
ax.plot(frequencies, amplitude_db, linewidth=3, color=BRAND, alpha=0.9)

# Fill under the curve
ax.fill_between(frequencies, amplitude_db, alpha=0.25, color=BRAND)

# Mark peak frequencies
peaks = [50, 120, 200]
for peak_freq in peaks:
    idx = np.argmin(np.abs(frequencies - peak_freq))
    ax.axvline(x=peak_freq, color=ACCENT, linestyle="--", linewidth=2, alpha=0.7)
    ax.scatter(
        [frequencies[idx]], [amplitude_db[idx]], s=200, color=ACCENT, zorder=5, edgecolors=PAGE_BG, linewidth=1.5
    )
    ax.annotate(
        f"{peak_freq} Hz",
        xy=(frequencies[idx], amplitude_db[idx]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=14,
        fontweight="bold",
        color=INK,
        bbox={
            "facecolor": PAGE_BG if THEME == "light" else "#242420",
            "edgecolor": INK_SOFT,
            "alpha": 0.8,
            "boxstyle": "round,pad=0.3",
        },
    )

# Style
ax.set_xlabel("Frequency (Hz)", fontsize=20, color=INK)
ax.set_ylabel("Amplitude (dB)", fontsize=20, color=INK)
ax.set_title("spectrum-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

# Axis limits
ax.set_xlim(0, 300)
ax.set_ylim(-60, 10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
