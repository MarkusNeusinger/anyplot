""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_tile, ggplot, labs, scale_fill_gradientn, theme, theme_minimal
from scipy import signal


# Data - Generate a chirp signal with increasing frequency
np.random.seed(42)
sample_rate = 1000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Create chirp signal: frequency increases from 50 Hz to 200 Hz
f0, f1 = 50, 200
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")
chirp_signal += 0.3 * np.random.randn(len(chirp_signal))  # Add noise

# Compute spectrogram using Short-Time Fourier Transform
nperseg = 128
noverlap = nperseg // 2
frequencies, times, Sxx = signal.spectrogram(chirp_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Convert power to dB scale
Sxx_db = 10 * np.log10(Sxx + 1e-10)

# Create DataFrame for plotnine (convert 2D grid to long format)
time_grid, freq_grid = np.meshgrid(times, frequencies)
df = pd.DataFrame({"Time": time_grid.ravel(), "Frequency": freq_grid.ravel(), "Power": Sxx_db.ravel()})

# Filter to relevant frequency range (0-500 Hz)
df = df[df["Frequency"] <= 500]

# Create spectrogram plot using geom_tile (heatmap)
plot = (
    ggplot(df, aes(x="Time", y="Frequency", fill="Power"))
    + geom_tile()
    + scale_fill_gradientn(colors=["#000033", "#306998", "#4A90A4", "#FFD43B", "#FFFFFF"], name="Power (dB)")
    + labs(x="Time (s)", y="Frequency (Hz)", title="spectrogram-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
