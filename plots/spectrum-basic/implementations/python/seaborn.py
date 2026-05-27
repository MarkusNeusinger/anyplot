""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # First series - machinery signal
ACCENT = "#C475FD"  # Peak markers

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
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
    },
)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Use seaborn lineplot for the spectrum with Okabe-Ito brand color
sns.lineplot(x=frequencies, y=amplitude_db, ax=ax, color=BRAND, linewidth=2.5)

# Fill under the curve for better visualization
ax.fill_between(frequencies, amplitude_db, alpha=0.3, color=BRAND)

# Mark peak frequencies with Okabe-Ito accent color
peak_indices = np.where((amplitude_db > -20) & (frequencies > 10))[0]
for idx in peak_indices:
    if amplitude_db[idx] > amplitude_db[max(0, idx - 5) : min(len(amplitude_db), idx + 6)].mean() + 5:
        ax.axvline(x=frequencies[idx], color=ACCENT, alpha=0.5, linestyle="--", linewidth=1.5)

# Styling
ax.set_xlabel("Frequency (Hz)", fontsize=20, color=INK)
ax.set_ylabel("Amplitude (dB)", fontsize=20, color=INK)
ax.set_title("spectrum-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(0, 300)  # Focus on the frequency range of interest
ax.set_ylim(-60, 10)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.xaxis.grid(False)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
