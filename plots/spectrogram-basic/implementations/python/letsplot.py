"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIME = "Time (seconds)"  # role: extra
SIGNAL = "Amplitude"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate
FREQUENCY = "Frequency (Hz)"  # role: extra
POWER = "Power (dB)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("signal.csv")
np.random.seed(42)
rate = 1000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(rate * duration))
# Linear chirp sweeping 10 Hz to 200 Hz, plus noise
chirp = signal.chirp(t, f0=10, f1=200, t1=duration, method="linear") + 0.1 * np.random.randn(len(t))
df = pd.DataFrame({TIME: t, SIGNAL: chirp, SAMPLE_RATE: rate})

# Plot
fs = df[SAMPLE_RATE].iloc[0]
nperseg = 128
frequencies, times, Sxx = signal.spectrogram(df[SIGNAL].to_numpy(), fs=fs, nperseg=nperseg, noverlap=nperseg * 3 // 4)
Sxx_db = 10 * np.log10(Sxx + 1e-10)

time_grid, freq_grid = np.meshgrid(times + df[TIME].min(), frequencies)
tiles = pd.DataFrame({TIME: time_grid.flatten(), FREQUENCY: freq_grid.flatten(), POWER: Sxx_db.flatten()})
# Keep the lower half of the spectrum, where the sweep lives
tiles = tiles[tiles[FREQUENCY] <= fs / 4]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
    legend_text=element_text(size=10, color=INK_SOFT),
)

plot = (
    ggplot(tiles, aes(x=TIME, y=FREQUENCY, fill=POWER))
    + geom_tile()
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=POWER)
    + labs(title="spectrogram-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
