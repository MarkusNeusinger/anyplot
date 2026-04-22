""" pyplots.ai
spectrum-basic: Frequency Spectrum Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Generate a synthetic signal with multiple frequency components
np.random.seed(42)

# Sampling parameters
sample_rate = 1024  # Hz
duration = 1.0  # seconds
n_samples = int(sample_rate * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# Create a signal with multiple frequency components
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
amplitude = np.abs(fft_result[positive_mask])

# Convert to dB scale (power spectrum)
amplitude_db = 20 * np.log10(amplitude + 1e-10)  # Add small value to avoid log(0)

# Create DataFrame for lets-plot
df = pd.DataFrame({"frequency": frequencies, "amplitude": amplitude_db})

# Filter to show meaningful frequency range (0-300 Hz)
df = df[df["frequency"] <= 300]

# Create plot
plot = (
    ggplot(df, aes(x="frequency", y="amplitude"))
    + geom_line(color="#306998", size=1.2, alpha=0.9)
    + geom_area(fill="#306998", alpha=0.3)
    + labs(x="Frequency (Hz)", y="Amplitude (dB)", title="spectrum-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.3),
        panel_grid_minor=element_line(color="#E0E0E0", size=0.2),
    )
    + ggsize(1600, 900)  # Will be scaled 3x to 4800x2700
)

# Save as PNG (scaled 3x for 4800x2700 resolution)
ggsave(plot, "plot.png", scale=3, path=".")

# Save as HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
