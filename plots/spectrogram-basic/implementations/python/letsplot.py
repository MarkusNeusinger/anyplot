"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from scipy import signal


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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

# Filter to relevant frequency range (0-250 Hz) to avoid wasted space
df = df[df["frequency"] <= 250]

# Create spectrogram using geom_tile with theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
)

plot = (
    ggplot(df, aes(x="time", y="frequency", fill="power"))
    + geom_tile()
    + scale_fill_viridis(name="Power (dB)")
    + labs(x="Time (seconds)", y="Frequency (Hz)", title="spectrogram-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700) and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
