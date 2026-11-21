"""anyplot.ai
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26, 26, 23, 0.08)" if THEME == "light" else "rgba(240, 239, 232, 0.08)"

# Imprint palette: first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
np.random.seed(42)
sample_rate = 1024  # Hz
n_samples = 1024
t = np.arange(n_samples) / sample_rate
# 50 Hz fundamental, 120 Hz harmonic, 200 Hz component, plus noise
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)
    + 0.5 * np.sin(2 * np.pi * 120 * t)
    + 0.3 * np.sin(2 * np.pi * 200 * t)
    + 0.1 * np.random.randn(n_samples)
)
fft_result = np.fft.fft(signal)
frequencies = np.fft.fftfreq(n_samples, 1 / sample_rate)
positive_mask = (frequencies >= 0) & (frequencies <= 300)
df = pd.DataFrame(
    {FREQUENCY: frequencies[positive_mask], AMPLITUDE: 20 * np.log10(np.abs(fft_result[positive_mask]) + 1e-10)}
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=FREQUENCY, y=AMPLITUDE))
    + geom_line(color=IMPRINT_PALETTE[0], size=1.0, alpha=0.9)
    + geom_area(fill=IMPRINT_PALETTE[0], alpha=0.2)
    + labs(title="spectrum-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_line=element_line(color=INK_SOFT, size=0.3),
    )
    + ggsize(800, 450)  # scaled 4x to 3200 x 1800
)

# Save as PNG and HTML (ggsave writes into a lets-plot-images/ subdirectory)
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

for ext in ("png", "html"):
    src = f"lets-plot-images/plot-{THEME}.{ext}"
    if os.path.exists(src):
        shutil.move(src, f"plot-{THEME}.{ext}")

try:
    os.rmdir("lets-plot-images")
except OSError:
    pass
