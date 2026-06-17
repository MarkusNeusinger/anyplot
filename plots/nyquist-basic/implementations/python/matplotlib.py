""" anyplot.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: matplotlib 3.11.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-17
"""

import os
import sys


# Remove script directory from sys.path so it doesn't shadow the installed matplotlib package.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir and p != ""]

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from scipy import signal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series
CRITICAL_COLOR = "#AE3030"  # Imprint semantic red for critical/error

# Data — cascaded third-order system: G(s) = 2 / (s+1)(0.5s+1)(0.2s+1)
num = [2.0]
den = np.polymul(np.polymul([1, 1], [0.5, 1]), [0.2, 1])
system = signal.TransferFunction(num, den)

omega = np.logspace(-1.5, 2, 800)
_, H = signal.freqresp(system, w=omega)

real = H.real
imag = H.imag

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(real, imag, color=BRAND, linewidth=2.5, label="G(jω)", zorder=3)
ax.plot(real, -imag, color=BRAND, linewidth=2.5, alpha=0.35, linestyle="--", label="G(−jω)", zorder=3)

# Direction arrows along the curve
for frac in [0.08, 0.2, 0.4, 0.65]:
    idx = int(frac * len(omega))
    ax.annotate(
        "",
        xy=(real[idx + 1], imag[idx + 1]),
        xytext=(real[idx], imag[idx]),
        arrowprops={"arrowstyle": "-|>", "color": BRAND, "lw": 2.0, "mutation_scale": 18},
        zorder=4,
    )

# Unit circle
unit_circle = Circle((0, 0), 1, fill=False, color=INK_SOFT, linewidth=1.5, linestyle=":", zorder=2)
ax.add_patch(unit_circle)

# Critical point (-1, 0)
ax.plot(
    -1,
    0,
    marker="x",
    color=CRITICAL_COLOR,
    markersize=14,
    markeredgewidth=3.0,
    zorder=5,
    label="Critical point (−1, 0)",
)

# Frequency annotations at key points
freq_annotations = [(0.3, (15, 12)), (1.0, (15, 12)), (2.0, (-15, -18)), (5.0, (-15, 14)), (10.0, (12, 12))]
for freq_val, (ox, oy) in freq_annotations:
    idx = np.argmin(np.abs(omega - freq_val))
    ax.plot(real[idx], imag[idx], "o", color=BRAND, markersize=6, zorder=5)
    ha = "left" if ox > 0 else "right"
    va = "bottom" if oy > 0 else "top"
    ax.annotate(
        f"ω={freq_val:g}",
        xy=(real[idx], imag[idx]),
        xytext=(ox, oy),
        textcoords="offset points",
        fontsize=16,
        color=INK_SOFT,
        fontweight="medium",
        ha=ha,
        va=va,
        zorder=5,
    )

# Style
ax.set_xlabel("Real", fontsize=10, color=INK)
ax.set_ylabel("Imaginary", fontsize=10, color=INK)
title = "nyquist-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_aspect("equal")
ax.axhline(0, color=INK_SOFT, linewidth=0.8, alpha=0.4, zorder=1)
ax.axvline(0, color=INK_SOFT, linewidth=0.8, alpha=0.4, zorder=1)

for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.10, right=0.96, top=0.93, bottom=0.10)

# Save
plt.savefig(os.path.join(_script_dir, f"plot-{THEME}.png"), dpi=400, facecolor=PAGE_BG)
