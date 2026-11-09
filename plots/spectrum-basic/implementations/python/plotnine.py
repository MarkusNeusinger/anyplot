""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotation_logticks,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_x_log10,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1, the single spectrum

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
# A 1 s machine-vibration signal: 50 Hz motor fundamental, two harmonics, a 500 Hz bearing tone, noise
np.random.seed(42)
sample_rate = 4096  # Hz
t = np.arange(sample_rate) / sample_rate
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)
    + 0.5 * np.sin(2 * np.pi * 100 * t)
    + 0.25 * np.sin(2 * np.pi * 150 * t)
    + 0.15 * np.sin(2 * np.pi * 500 * t)
    + 0.1 * np.random.randn(t.size)
)
frequencies = np.fft.rfftfreq(t.size, 1 / sample_rate)
amplitudes = np.abs(np.fft.rfft(signal)) * 2 / t.size
in_band = (frequencies >= 10) & (frequencies <= 1000)
df = pd.DataFrame({FREQUENCY: frequencies[in_band], AMPLITUDE: 20 * np.log10(amplitudes[in_band] + 1e-10)})

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=FREQUENCY, y=AMPLITUDE))
    + geom_line(color=BRAND, size=0.6)
    + scale_x_log10()
    + annotation_logticks(sides="b", color=INK_SOFT, size=0.4, alpha=0.8)
    + labs(title="spectrum-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=12, weight="bold", color=INK),
        plot_title_position="plot",
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
