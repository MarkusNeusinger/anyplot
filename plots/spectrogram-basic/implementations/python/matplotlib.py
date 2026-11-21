"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap (brand green -> blue) for continuous power values
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Columns: set these to your table's column names
TIME = "Time (s)"  # role: sample_rate
SIGNAL = "Amplitude"  # role: signal

# Data: replace this block with your own table, for example df = pd.read_csv("signal.csv")
rng = np.random.default_rng(42)
sample_rate = 4000  # Hz
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Chirp sweeping from 100 Hz to 1000 Hz
f0, f1 = 100, 1000
x = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration)))

# A 500 Hz tone burst between 0.8 s and 1.2 s
burst = (t >= 0.8) & (t < 1.2)
x[burst] += 0.7 * np.sin(2 * np.pi * 500 * t[burst])

# Background noise
x += 0.1 * rng.standard_normal(len(t))

df = pd.DataFrame({TIME: t, SIGNAL: x})

# Plot
fs = 1 / df[TIME].diff().median()
freqs, times, power = signal.spectrogram(df[SIGNAL].to_numpy(), fs=fs, nperseg=256, noverlap=200, scaling="density")
power_db = 10 * np.log10(power + 1e-10)

# Clip the colour range so the weak noise floor stays visible beside the strong components
vmin, vmax = np.percentile(power_db, [2, 99.9])

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

im = ax.pcolormesh(times, freqs, power_db, shading="gouraud", cmap=imprint_seq, vmin=vmin, vmax=vmax, rasterized=True)

cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label("Power/Frequency (dB/Hz)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_xlabel(TIME, fontsize=10, color=INK)
ax.set_ylabel("Frequency (Hz)", fontsize=10, color=INK)
ax.set_title("spectrogram-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
