"""anyplot.ai
spectrogram-basic: Spectrogram Time-Frequency Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (continuous data uses the sequential cmap derived from it)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Constants
WINDOW_SIZE = 256  # samples per analysis window
WINDOW_OVERLAP = 200  # overlapping samples between windows (smoother time axis)
POWER_FLOOR = 1e-10  # avoids log of zero in the dB conversion
N_TICKS = 5
FLOOR_PERCENTILE = 20  # color range starts here so isolated deep-noise cells don't flatten the contrast

# Columns: set these to your table's column names
SIGNAL = "Amplitude"  # role: signal
SAMPLE_RATE = "Sample rate (Hz)"  # role: sample_rate

# Data: replace this block with your own table, for example df = pd.read_csv("signal.csv")
# Chirp sweeping 100 Hz to 800 Hz over 2 s, sampled at 4 kHz, with a little noise
np.random.seed(42)
_sample_rate = 4000  # Hz
_duration = 2.0  # seconds
_t = np.linspace(0, _duration, int(_sample_rate * _duration), endpoint=False)
_chirp = signal.chirp(_t, f0=100, f1=800, t1=_duration, method="linear")
df = pd.DataFrame({SIGNAL: _chirp + np.random.randn(len(_t)) * 0.1, SAMPLE_RATE: _sample_rate})

# Plot: reads only df and the constants above
sample_rate = df[SAMPLE_RATE].median()
duration = len(df) / sample_rate
samples = df[SIGNAL].interpolate(limit_direction="both").to_numpy()  # a gap in the signal is bridged, not zeroed
frequencies, times, power = signal.spectrogram(samples, fs=sample_rate, nperseg=WINDOW_SIZE, noverlap=WINDOW_OVERLAP)
power_db = 10 * np.log10(power + POWER_FLOOR)

# Tick positions in cell units; the heatmap's y axis is inverted so low frequencies sit at the bottom
time_ticks = np.linspace(0, power_db.shape[1], N_TICKS)
time_labels = [f"{v:.1f}" for v in np.linspace(0, duration, N_TICKS)]
freq_ticks = np.linspace(0, power_db.shape[0], N_TICKS)
freq_labels = [f"{round(v)}" for v in np.linspace(frequencies[0], frequencies[-1], N_TICKS)]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(
    power_db[::-1],
    ax=ax,
    cmap=imprint_seq,
    vmin=np.percentile(power_db, FLOOR_PERCENTILE),
    vmax=power_db.max(),
    cbar=True,
    cbar_kws={"label": "Power (dB)", "shrink": 0.85, "pad": 0.02},
    xticklabels=False,
    yticklabels=False,
    rasterized=True,
)

# Style
title = "spectrogram-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, color=INK, pad=10)
ax.set_xticks(time_ticks, time_labels, rotation=0)
ax.set_yticks(freq_ticks, freq_labels[::-1], rotation=0)
ax.set_xlabel("Time (s)", fontsize=10, color=INK)
ax.set_ylabel("Frequency (Hz)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.ax.yaxis.label.set_size(10)
cbar.ax.yaxis.label.set_color(INK)
cbar.outline.set_edgecolor(INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.95, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
