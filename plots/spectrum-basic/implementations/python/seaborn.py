""" anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, LogLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_PEAKS = 4  # dominant components to highlight

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
# Synthetic machinery vibration: 50 Hz fundamental, harmonics at 100 and 150 Hz, a 220 Hz component, noise
np.random.seed(42)
sample_rate = 1000  # Hz
n_samples = 1000
t = np.arange(n_samples) / sample_rate
signal = (
    2.0 * np.sin(2 * np.pi * 50 * t)
    + 1.2 * np.sin(2 * np.pi * 100 * t)
    + 0.8 * np.sin(2 * np.pi * 150 * t)
    + 0.3 * np.sin(2 * np.pi * 220 * t)
    + 0.4 * np.random.randn(n_samples)
)
fft_result = np.fft.rfft(signal)
frequencies = np.fft.rfftfreq(n_samples, 1 / sample_rate)
magnitude = np.abs(fft_result) * 2 / n_samples
df = pd.DataFrame({FREQUENCY: frequencies[1:], AMPLITUDE: 20 * np.log10(magnitude[1:] + 1e-10)})

# Plot: reads only df and the constants above
freq = df[FREQUENCY].to_numpy()
amp = df[AMPLITUDE].to_numpy()

# Dominant components: the tallest local maxima
is_peak = np.r_[False, (amp[1:-1] > amp[:-2]) & (amp[1:-1] > amp[2:]), False]
peak_idx = np.flatnonzero(is_peak)
peak_idx = peak_idx[np.argsort(amp[peak_idx])[::-1][:N_PEAKS]]
peaks = df.iloc[np.sort(peak_idx)]

floor = np.floor(np.nanmin(amp) / 10) * 10
top = np.nanmax(amp) + 0.12 * (np.nanmax(amp) - floor)

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(data=df, x=FREQUENCY, y=AMPLITUDE, ax=ax, color=IMPRINT_PALETTE[0], linewidth=1.2)
ax.fill_between(freq, amp, floor, color=IMPRINT_PALETTE[0], alpha=0.25, linewidth=0)

# Peak highlights, each labelled with its frequency
sns.scatterplot(
    data=peaks,
    x=FREQUENCY,
    y=AMPLITUDE,
    ax=ax,
    color=IMPRINT_PALETTE[1],
    s=45,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    zorder=3,
)
for _, row in peaks.iterrows():
    ax.annotate(
        f"{row[FREQUENCY]:.0f} Hz",
        xy=(row[FREQUENCY], row[AMPLITUDE]),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        fontsize=8,
        color=INK,
    )

# Logarithmic frequency axis with readable ticks
ax.set_xscale("log")
ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,)))
ax.xaxis.set_minor_locator(LogLocator(base=10, subs=(2.0, 5.0)))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.set_xlim(np.nanmin(freq), np.nanmax(freq))
ax.set_ylim(floor, top)

# Style
ax.set_title("spectrum-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(FREQUENCY, fontsize=10, color=INK)
ax.set_ylabel(AMPLITUDE, fontsize=10, color=INK)
ax.tick_params(axis="both", which="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.xaxis.grid(False)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
