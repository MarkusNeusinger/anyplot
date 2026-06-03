""" anyplot.ai
waveform-audio: Audio Waveform Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-03
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # #009E73 — always first series

# Data: simulated seismic recording — P-wave and S-wave arrivals
np.random.seed(42)
sample_rate = 1000  # Hz
duration = 10.0  # seconds
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

signal = np.random.normal(0, 0.015, num_samples)  # background microseismic noise

# P-wave arrival at t=2s: ~10 Hz, moderate amplitude, 2 s duration
p_start = int(2.0 * sample_rate)
p_len = int(2.0 * sample_rate)
p_env = np.concatenate(
    [np.linspace(0, 1, int(0.15 * p_len)), np.ones(int(0.35 * p_len)), np.linspace(1, 0.08, p_len - int(0.50 * p_len))]
)
p_t = np.arange(p_len) / sample_rate
signal[p_start : p_start + p_len] += 0.32 * p_env * np.sin(2 * np.pi * 10 * p_t)
signal[p_start : p_start + p_len] += np.random.normal(0, 0.025, p_len)

# S-wave arrival at t=4s: ~3 Hz, high amplitude, 4 s duration
s_start = int(4.0 * sample_rate)
s_len = int(4.0 * sample_rate)
s_env = np.concatenate(
    [np.linspace(0, 1, int(0.10 * s_len)), np.ones(int(0.40 * s_len)), np.linspace(1, 0.12, s_len - int(0.50 * s_len))]
)
s_t = np.arange(s_len) / sample_rate
signal[s_start : s_start + s_len] += 0.88 * s_env * np.sin(2 * np.pi * 3 * s_t)
signal[s_start : s_start + s_len] += np.random.normal(0, 0.03, s_len)

# Coda (8–10 s): decaying mixed frequencies
c_start = int(8.0 * sample_rate)
c_len = int(2.0 * sample_rate)
c_env = np.linspace(0.12, 0.02, c_len)
c_t = np.arange(c_len) / sample_rate
signal[c_start : c_start + c_len] += c_env * (0.6 * np.sin(2 * np.pi * 3 * c_t) + 0.4 * np.sin(2 * np.pi * 8 * c_t))

amplitude = signal / np.abs(signal).max()  # normalise to [-1, 1]

# Min/max envelope for dense rendering — avoids aliasing at plot resolution
chunk_size = 40  # 1000 Hz / 40 = 25 envelope points per second
num_chunks = num_samples // chunk_size
amp_chunks = amplitude[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)
time_chunks = time[: num_chunks * chunk_size].reshape(num_chunks, chunk_size)
env_max = amp_chunks.max(axis=1)
env_min = amp_chunks.min(axis=1)
env_time = time_chunks.mean(axis=1)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Phase region backgrounds — Imprint palette, deuteranopia-safe (no red/green pair)
phases = [
    (0, 2, "Background\nNoise", INK_MUTED),
    (2, 4, "P-wave", IMPRINT_PALETTE[2]),  # blue  #4467A3
    (4, 8, "S-wave", IMPRINT_PALETTE[1]),  # lavender #C475FD
    (8, 10, "Coda", IMPRINT_PALETTE[3]),  # ochre #BD8233
]
for t0, t1, label, clr in phases:
    ax.axvspan(t0, t1, alpha=0.07, color=clr, zorder=0)
    ax.text(
        (t0 + t1) / 2,
        0.97,
        label,
        ha="center",
        va="top",
        fontsize=6,
        fontweight="semibold",
        color=clr,
        alpha=0.95,
        transform=ax.get_xaxis_transform(),
        path_effects=[pe.withStroke(linewidth=1.5, foreground=PAGE_BG)],
    )

# Waveform: filled min/max envelope around zero baseline
ax.fill_between(env_time, env_max, env_min, color=BRAND, alpha=0.5, linewidth=0, zorder=2)
ax.plot(env_time, env_max, color=BRAND, linewidth=0.8, alpha=0.75, zorder=3)
ax.plot(env_time, env_min, color=BRAND, linewidth=0.8, alpha=0.75, zorder=3)

# Zero reference line
ax.axhline(y=0, color=INK_SOFT, linewidth=0.8, alpha=0.5, zorder=1)

# P and S arrival markers
for t_arr, _lbl, clr in [(2, "P", IMPRINT_PALETTE[2]), (4, "S", IMPRINT_PALETTE[1])]:
    ax.axvline(x=t_arr, color=clr, linewidth=1.0, linestyle="--", alpha=0.65, zorder=4)

# Style
title = "waveform-audio · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)
ax.set_xlabel("Time (s)", fontsize=10, color=INK)
ax.set_ylabel("Amplitude", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_ylim(-1.08, 1.08)
ax.set_xlim(0, duration)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
