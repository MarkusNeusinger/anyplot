""" anyplot.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter1d


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Seaborn theme — warm cream/near-black surfaces with Imprint chrome
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Imprint sequential colormap — green → blue for trace density
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — NRZ signal with bandwidth-limited transitions, jitter, and noise
np.random.seed(42)
n_traces = 400
samples_per_ui = 200
ui_span = 2
n_display = samples_per_ui * ui_span
noise_sigma = 0.05
jitter_sigma = 0.03
bw_filter_sigma = 12

all_time = []
all_voltage = []
t_ui = np.linspace(0, ui_span, n_display, endpoint=False)

for _ in range(n_traces):
    n_bits = 8
    bits = np.random.randint(0, 2, size=n_bits)
    samples_total = samples_per_ui * n_bits

    signal_raw = np.repeat(bits.astype(float), samples_per_ui)
    signal_smooth = gaussian_filter1d(signal_raw, sigma=bw_filter_sigma)

    jitter_shift = int(np.random.normal(0, jitter_sigma * samples_per_ui))
    signal_smooth = np.roll(signal_smooth, jitter_shift)
    signal_smooth += np.random.normal(0, noise_sigma, samples_total)

    start_bit = 3
    start_idx = start_bit * samples_per_ui
    end_idx = start_idx + n_display
    segment = signal_smooth[start_idx:end_idx]

    all_time.extend(t_ui.tolist())
    all_voltage.extend(segment.tolist())

df = pd.DataFrame({"time": all_time, "voltage": all_voltage})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Seaborn 2D histogram — density heatmap; thresh=1 makes zero-count bins transparent
sns.histplot(
    data=df,
    x="time",
    y="voltage",
    bins=[300, 180],
    stat="count",
    thresh=1,
    cbar=True,
    cbar_kws={"label": "Trace Density", "shrink": 0.8},
    cmap=imprint_seq,
    ax=ax,
)

# NRZ reference levels at logic 0 and 1
ax.axhline(y=0.0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.4)
ax.axhline(y=1.0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.4)

ax.set_xlim(0, 2)
ax.set_ylim(-0.3, 1.3)
ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])

# Style
title = "eye-diagram-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Time (UI)", fontsize=10, color=INK)
ax.set_ylabel("Voltage (V)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax, top=True, right=True)

# Style colorbar text
if len(fig.axes) > 1:
    cbar_ax = fig.axes[-1]
    cbar_ax.tick_params(colors=INK_SOFT, labelsize=8)
    cbar_ax.yaxis.label.set_color(INK)
    for spine in cbar_ax.spines.values():
        spine.set_color(INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
