"""anyplot.ai
bode-basic: Bode Plot for Frequency Response
Library: matplotlib 3.11.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — stable third-order open-loop transfer function with complex conjugate poles:
# H(s) = K * wn^2 / ((s^2 + 2*zeta*wn*s + wn^2) * (1 + s/wp))
# Underdamped second-order pair (zeta=0.2, fn=50 Hz) → clear +8 dB resonance peak
# High-frequency pole at 300 Hz; K=1.0 gives GM ≈ 8 dB and PM ≈ 23°
fn = 50.0
zeta = 0.2
K = 1.0
wn = 2 * np.pi * fn
wp = 2 * np.pi * 300.0

# Coefficients: denominator of (s^2 + 2*zeta*wn*s + wn^2)(s/wp + 1)
num = [K * wn**2]
den = [1.0 / wp, 1.0 + 2 * zeta * wn / wp, 2 * zeta * wn + wn**2 / wp, wn**2]

sys = signal.TransferFunction(num, den)
frequency_hz = np.logspace(-1, 3, 600)
omega = 2 * np.pi * frequency_hz
_, magnitude_db, phase_deg_raw = signal.bode(sys, w=omega)
# scipy.signal.bode does not unwrap phase — unwrap to avoid -180° / +180° jumps
phase_deg = np.unwrap(phase_deg_raw, period=360)

# Compute gain crossover (0 dB crossing)
sign_changes_mag = np.diff(np.sign(magnitude_db))
gain_crossover_idx = np.where(sign_changes_mag != 0)[0]
if len(gain_crossover_idx) > 0:
    gc_idx = gain_crossover_idx[0]
    gain_crossover_freq = frequency_hz[gc_idx]
    phase_at_gc = phase_deg[gc_idx]
    phase_margin = 180 + phase_at_gc
else:
    gain_crossover_freq = None

# Compute phase crossover (-180 deg crossing)
sign_changes_phase = np.diff(np.sign(phase_deg + 180))
phase_crossover_idx = np.where(sign_changes_phase != 0)[0]
if len(phase_crossover_idx) > 0:
    pc_idx = phase_crossover_idx[0]
    phase_crossover_freq = frequency_hz[pc_idx]
    gain_at_pc = magnitude_db[pc_idx]
    gain_margin = -gain_at_pc
else:
    phase_crossover_freq = None

# Plot — landscape canvas: figsize=(8, 4.5) × dpi=400 → exactly 3200×1800 px
fig, (ax_mag, ax_phase) = plt.subplots(
    2,
    1,
    figsize=(8, 4.5),
    dpi=400,
    sharex=True,
    facecolor=PAGE_BG,
    gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08},
)
ax_mag.set_facecolor(PAGE_BG)
ax_phase.set_facecolor(PAGE_BG)

# Imprint palette positions for stability margin annotations (avoid red-green pairing)
GM_COLOR = IMPRINT_PALETTE[2]  # blue #4467A3 — gain margin
PM_COLOR = IMPRINT_PALETTE[1]  # lavender #C475FD — phase margin

ANNOT_BBOX = {"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9, "boxstyle": "round,pad=0.3"}

# Magnitude plot
ax_mag.semilogx(frequency_hz, magnitude_db, color=IMPRINT_PALETTE[0], linewidth=2.5)
ax_mag.axhline(y=0, color=INK_SOFT, linewidth=1, linestyle="--", alpha=0.6)

# Gain margin annotation
if phase_crossover_freq is not None:
    ax_mag.vlines(phase_crossover_freq, gain_at_pc, 0, colors=GM_COLOR, linewidth=2.0)
    ax_mag.plot(phase_crossover_freq, gain_at_pc, "o", color=GM_COLOR, markersize=8, zorder=5)
    ax_mag.annotate(
        f"GM = {gain_margin:.1f} dB",
        xy=(phase_crossover_freq, (gain_at_pc + 0) / 2),
        xytext=(phase_crossover_freq * 3, (gain_at_pc + 0) / 2 + 4),
        fontsize=8,
        color=GM_COLOR,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": GM_COLOR, "lw": 1.5},
        bbox=ANNOT_BBOX,
    )

# Phase plot
ax_phase.semilogx(frequency_hz, phase_deg, color=IMPRINT_PALETTE[0], linewidth=2.5)
ax_phase.axhline(y=-180, color=INK_SOFT, linewidth=1, linestyle="--", alpha=0.6)

# Phase margin annotation
if gain_crossover_freq is not None:
    ax_phase.vlines(gain_crossover_freq, -180, phase_at_gc, colors=PM_COLOR, linewidth=2.0)
    ax_phase.plot(gain_crossover_freq, phase_at_gc, "o", color=PM_COLOR, markersize=8, zorder=5)
    ax_phase.annotate(
        f"PM = {phase_margin:.1f}°",
        xy=(gain_crossover_freq, (-180 + phase_at_gc) / 2),
        xytext=(gain_crossover_freq * 3, (-180 + phase_at_gc) / 2 - 15),
        fontsize=8,
        color=PM_COLOR,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": PM_COLOR, "lw": 1.5},
        bbox=ANNOT_BBOX,
    )

# Style — Magnitude panel
title = "bode-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax_mag.set_ylabel("Magnitude (dB)", fontsize=10, color=INK)
ax_mag.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax_mag.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_mag.spines["top"].set_visible(False)
ax_mag.spines["right"].set_visible(False)
ax_mag.spines["left"].set_color(INK_SOFT)
ax_mag.spines["bottom"].set_color(INK_SOFT)
ax_mag.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax_mag.xaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax_mag.set_ylim(-25, 15)

# Style — Phase panel
ax_phase.set_xlabel("Frequency (Hz)", fontsize=10, color=INK)
ax_phase.set_ylabel("Phase (°)", fontsize=10, color=INK)
ax_phase.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_phase.spines["top"].set_visible(False)
ax_phase.spines["right"].set_visible(False)
ax_phase.spines["left"].set_color(INK_SOFT)
ax_phase.spines["bottom"].set_color(INK_SOFT)
ax_phase.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax_phase.xaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax_phase.set_yticks([0, -45, -90, -135, -180, -225, -270])

# Save — bbox_inches must stay default (None) to preserve exact 3200×1800 canvas
fig.subplots_adjust(left=0.1, right=0.95, top=0.93, bottom=0.1)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
