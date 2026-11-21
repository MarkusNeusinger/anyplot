"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp for continuous power runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SIGNAL = "Signal (a.u.)"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate
TIME = "Time (s)"  # role: extra
FREQUENCY = "Frequency (Hz)"  # role: extra
POWER = "Power (dB)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("spectrogram.csv")
np.random.seed(42)
sample_rate = 1000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))

# Chirp signal: frequency sweeps linearly from 50 Hz to 200 Hz, plus noise
chirp_signal = signal.chirp(t, f0=50, f1=200, t1=duration, method="linear")
chirp_signal += 0.3 * np.random.randn(len(chirp_signal))

# Short-time Fourier transform, power in dB
frequencies, times, Sxx = signal.spectrogram(chirp_signal, fs=sample_rate, nperseg=128, noverlap=64)
time_grid, freq_grid = np.meshgrid(times, frequencies)
df = pd.DataFrame({TIME: time_grid.ravel(), FREQUENCY: freq_grid.ravel(), POWER: 10 * np.log10(Sxx.ravel() + 1e-10)})
df = df[df[FREQUENCY] <= 250]

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
    panel_grid_minor=element_line(color=INK, size=0.15, alpha=0.06),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=12, weight="bold"),
    legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    figure_size=(8, 4.5),
    text=element_text(size=8),
)

plot = (
    ggplot(df, aes(x=TIME, y=FREQUENCY, fill=POWER))
    + geom_tile()
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2])
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + labs(title="spectrogram-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
