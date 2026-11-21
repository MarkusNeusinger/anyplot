"""anyplot.ai
spectrum-basic: Frequency Spectrum Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_PEAKS = 3  # number of dominant components to annotate

# Columns
FREQUENCY = "Frequency (Hz)"  # role: frequency
AMPLITUDE = "Amplitude (dB)"  # role: amplitude

# Data: replace this block with your own table, for example df = pd.read_csv("spectrum.csv")
np.random.seed(42)
sample_rate = 1000  # Hz
n_samples = 1000
t = np.arange(n_samples) / sample_rate
signal = (
    1.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz fundamental
    + 0.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz component
    + 0.3 * np.sin(2 * np.pi * 200 * t)  # 200 Hz component
    + 0.1 * np.random.randn(n_samples)  # noise floor
)
fft_result = np.fft.fft(signal)
freqs = np.fft.fftfreq(n_samples, 1 / sample_rate)
positive = freqs >= 0
df = pd.DataFrame(
    {FREQUENCY: freqs[positive], AMPLITUDE: 20 * np.log10(np.abs(fft_result[positive]) * 2 / n_samples + 1e-10)}
)

# Plot
x = df[FREQUENCY].to_numpy()
y = df[AMPLITUDE].to_numpy()

# Dominant components: the largest local maxima of the spectrum
is_local_max = np.r_[False, (y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]), False]
peak_idx = np.sort(np.flatnonzero(is_local_max)[np.argsort(y[is_local_max])[::-1][:N_PEAKS]])

y_top = np.nanmax(y) + 10
y_bottom = np.nanmax(y) - 60

title = "spectrum-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(x, y, linewidth=1.5, color=IMPRINT_PALETTE[0], alpha=0.9)
ax.fill_between(x, y, y_bottom, alpha=0.25, color=IMPRINT_PALETTE[0])

ax.scatter(x[peak_idx], y[peak_idx], s=60, color=IMPRINT_PALETTE[1], zorder=5, edgecolors=PAGE_BG, linewidth=0.8)
for i in peak_idx:
    ax.annotate(
        f"{x[i]:.0f} Hz",
        xy=(x[i], y[i]),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=7,
        fontweight="bold",
        color=INK,
        bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "boxstyle": "round,pad=0.3"},
    )

# Style
ax.set_xlabel(FREQUENCY, fontsize=10, color=INK)
ax.set_ylabel(AMPLITUDE, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

ax.set_xlim(0, np.nanmax(x) * 0.6)
ax.set_ylim(y_bottom, y_top)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
