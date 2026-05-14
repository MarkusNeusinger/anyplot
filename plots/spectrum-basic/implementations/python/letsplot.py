""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-14
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Grid color (theme-adaptive)
GRID_COLOR = "rgba(26, 26, 23, 0.08)" if THEME == "light" else "rgba(240, 239, 232, 0.08)"

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
amplitude_db = 20 * np.log10(amplitude + 1e-10)

# Create DataFrame for lets-plot
df = pd.DataFrame({"frequency": frequencies, "amplitude": amplitude_db})

# Filter to show meaningful frequency range (0-300 Hz)
df = df[df["frequency"] <= 300]

# Create plot with theme-adaptive styling
plot = (
    ggplot(df, aes(x="frequency", y="amplitude"))
    + geom_line(color=BRAND, size=1.2, alpha=0.9)
    + geom_area(fill=BRAND, alpha=0.2)
    + labs(x="Frequency (Hz)", y="Amplitude (dB)", title="spectrum-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, face="bold"),
        axis_line=element_line(color=INK_SOFT, size=0.3),
    )
    + ggsize(1600, 900)  # Will be scaled 3x to 4800x2700
)

# Save as PNG and HTML (ggsave saves to lets-plot-images/ subdirectory)
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files to current directory
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")

# Clean up empty subdirectory if all files are moved
try:
    if not os.listdir("lets-plot-images"):
        os.rmdir("lets-plot-images")
except OSError:
    pass
