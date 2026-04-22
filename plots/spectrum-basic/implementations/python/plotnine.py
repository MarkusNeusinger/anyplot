""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotation_logticks,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_x_log10,
    theme,
    theme_minimal,
)


# Data: Create a synthetic signal with multiple frequency components
np.random.seed(42)

# Sampling parameters
sample_rate = 4096  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create signal with multiple frequency components
# Simulating a mechanical vibration signal with fundamental and harmonics
fundamental_freq = 50  # Hz (e.g., motor rotation)
signal = (
    1.0 * np.sin(2 * np.pi * fundamental_freq * t)  # Fundamental
    + 0.5 * np.sin(2 * np.pi * 2 * fundamental_freq * t)  # 2nd harmonic
    + 0.25 * np.sin(2 * np.pi * 3 * fundamental_freq * t)  # 3rd harmonic
    + 0.15 * np.sin(2 * np.pi * 500 * t)  # High frequency component
    + 0.1 * np.random.randn(n_samples)  # Noise
)

# Compute FFT
fft_result = np.fft.fft(signal)
frequencies = np.fft.fftfreq(n_samples, 1 / sample_rate)

# Take positive frequencies only
positive_mask = frequencies > 0
frequencies = frequencies[positive_mask]
amplitudes = np.abs(fft_result[positive_mask]) * 2 / n_samples

# Convert to dB scale for better visualization
amplitudes_db = 20 * np.log10(amplitudes + 1e-10)

# Create DataFrame for plotnine
df = pd.DataFrame({"frequency": frequencies, "amplitude": amplitudes_db})

# Filter to relevant frequency range (10 Hz to 1000 Hz)
df = df[(df["frequency"] >= 10) & (df["frequency"] <= 1000)]

# Create plot
plot = (
    ggplot(df, aes(x="frequency", y="amplitude"))
    + geom_line(color="#306998", size=1.2, alpha=0.9)
    + scale_x_log10()
    + annotation_logticks(sides="b")
    + labs(x="Frequency (Hz)", y="Amplitude (dB)", title="spectrum-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_text(alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
