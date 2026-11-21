""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import sys

import numpy as np
import pandas as pd


sys.path.pop(0)
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: first series is brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB re 1 µg)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
# Motor vibration: 30 Hz shaft (1800 rpm) with harmonics, 600 Hz gear mesh (20 teeth) with shaft sidebands
rng = np.random.default_rng(7)
fs = 8192  # sampling rate (Hz)
n = 4096  # samples -> 2 Hz bins
t = np.arange(n) / fs
signal = (
    0.80 * np.sin(2 * np.pi * 30 * t)  # shaft imbalance
    + 0.35 * np.sin(2 * np.pi * 60 * t + 0.6)  # 2x shaft (misalignment)
    + 0.15 * np.sin(2 * np.pi * 90 * t + 1.1)  # 3x shaft
    + 0.50 * np.sin(2 * np.pi * 600 * t + 0.3)  # gear mesh
    + 0.16 * np.sin(2 * np.pi * 570 * t + 2.0)  # lower sideband
    + 0.16 * np.sin(2 * np.pi * 630 * t + 1.4)  # upper sideband
    + 0.22 * np.sin(2 * np.pi * 1200 * t + 0.9)  # 2x gear mesh
    + 0.02 * rng.standard_normal(n)  # broadband noise floor
)
window = np.hanning(n)
spectrum = np.abs(np.fft.rfft(signal * window)) / window.sum() * 2
freqs = np.fft.rfftfreq(n, 1 / fs)
keep = (freqs >= 10) & (freqs <= 2000)
df = pd.DataFrame(
    {
        FREQUENCY: freqs[keep],
        AMPLITUDE: 20 * np.log10(spectrum[keep] / 1e-6),  # dB re 1 µg
    }
)

# Plot: log10 of frequency drives the x position, ticks are 1-2-5 steps inside the data range
table = df.dropna(subset=[FREQUENCY, AMPLITUDE])
log_f = np.log10(table[FREQUENCY].to_numpy())
decades = range(int(np.floor(log_f.min())), int(np.ceil(log_f.max())) + 1)
ticks = [m * 10.0**d for d in decades for m in (1, 2, 5)]
ticks = [v for v in ticks if table[FREQUENCY].min() <= v <= table[FREQUENCY].max()]

y_low = float(np.floor(table[AMPLITUDE].min() / 10) * 10)
y_high = float(np.ceil(table[AMPLITUDE].max() / 10) * 10)

TITLE = "spectrum-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=0.45,
    opacity_hover=0.6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=TITLE,
    x_title=FREQUENCY + ", log scale",
    y_title=AMPLITUDE,
    show_dots=False,
    fill=True,
    show_x_guides=True,
    show_y_guides=True,
    show_legend=False,
    range=(y_low, y_high),
    xrange=(float(log_f.min()), float(log_f.max())),
    x_labels=[float(np.log10(v)) for v in ticks],
    x_value_formatter=lambda v: f"{10**v:g}",
    value_formatter=lambda v: f"{v:g}",
    truncate_label=-1,
    margin=60,
)
chart.add(AMPLITUDE, list(zip(log_f.tolist(), table[AMPLITUDE].tolist(), strict=True)))

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
