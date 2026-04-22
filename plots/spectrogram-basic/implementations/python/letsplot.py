""" pyplots.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *
from scipy import signal


LetsPlot.setup_html()

# Generate chirp signal (frequency increases over time)
np.random.seed(42)
sample_rate = 1000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Chirp signal: frequency sweeps from 10 Hz to 200 Hz
f0, f1 = 10, 200
chirp_signal = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear")
chirp_signal += 0.1 * np.random.randn(len(t))  # Add noise

# Compute spectrogram using scipy
nperseg = 128
noverlap = 96
frequencies, times, Sxx = signal.spectrogram(chirp_signal, fs=sample_rate, nperseg=nperseg, noverlap=noverlap)

# Convert to dB scale for better visualization
Sxx_db = 10 * np.log10(Sxx + 1e-10)

# Create mesh data for heatmap
time_grid, freq_grid = np.meshgrid(times, frequencies)
df = pd.DataFrame({"time": time_grid.flatten(), "frequency": freq_grid.flatten(), "power": Sxx_db.flatten()})

# Create spectrogram using geom_tile
plot = (
    ggplot(df, aes(x="time", y="frequency", fill="power"))
    + geom_tile()
    + scale_fill_viridis(name="Power (dB)")
    + labs(x="Time (seconds)", y="Frequency (Hz)", title="spectrogram-basic · lets-plot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
