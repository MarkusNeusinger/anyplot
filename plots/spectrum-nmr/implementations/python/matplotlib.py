""" anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-03
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Theme-adaptive chrome (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first categorical series always brand green
BRAND = "#009E73"

# Data: synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
ppm = np.linspace(-0.5, 5.0, 6000)
spectrum = np.zeros_like(ppm)

w = 0.025  # Lorentzian half-width
j = 0.078  # J-coupling constant — wider than minimal so multiplet splitting is visually striking

# Lorentzian peaks: A / (1 + ((x - x0) / w)^2)
# TMS reference singlet at 0.00 ppm
spectrum += 0.30 / (1 + ((ppm - 0.00) / 0.015) ** 2)

# CH3 triplet ~1.18 ppm  (1 : 2 : 1 ratio)
spectrum += 0.50 / (1 + ((ppm - (1.18 - j)) / w) ** 2)
spectrum += 1.00 / (1 + ((ppm - 1.18) / w) ** 2)
spectrum += 0.50 / (1 + ((ppm - (1.18 + j)) / w) ** 2)

# CH2 quartet ~3.69 ppm  (1 : 3 : 3 : 1 ratio)
spectrum += 0.25 / (1 + ((ppm - (3.69 - 1.5 * j)) / w) ** 2)
spectrum += 0.75 / (1 + ((ppm - (3.69 - 0.5 * j)) / w) ** 2)
spectrum += 0.75 / (1 + ((ppm - (3.69 + 0.5 * j)) / w) ** 2)
spectrum += 0.25 / (1 + ((ppm - (3.69 + 1.5 * j)) / w) ** 2)

# OH singlet ~2.61 ppm
spectrum += 0.40 / (1 + ((ppm - 2.61) / w) ** 2)

# Subtle baseline noise
spectrum += np.random.normal(0, 0.003, len(ppm))
spectrum = np.clip(spectrum, 0, None)

# Canvas — landscape 3200 × 1800 px (16:9)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Spectrum trace + area fill
ax.plot(ppm, spectrum, linewidth=2.5, color=BRAND, zorder=3)
ax.fill_between(ppm, spectrum, alpha=0.12, color=BRAND, zorder=2)

# Subtle peak-region highlight bands
for lo, hi in [(-0.15, 0.15), (1.00, 1.42), (2.45, 2.75), (3.50, 3.92)]:
    ax.axvspan(lo, hi, alpha=0.06, color=BRAND, zorder=1)

# Peak annotations with theme-matched path-effect outline
text_outline = [pe.withStroke(linewidth=3, foreground=ELEVATED_BG)]
annotations = [
    (0.00, "TMS\n0.00 ppm", (42, 28)),
    (1.18, "CH₃ (triplet)\n1.18 ppm", (82, -48)),
    (2.61, "OH (singlet)\n2.61 ppm", (-55, 34)),
    (3.69, "CH₂ (quartet)\n3.69 ppm", (-60, 38)),
]
for peak_ppm, label, offset in annotations:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    ax.annotate(
        label,
        xy=(peak_ppm, spectrum[peak_idx]),
        xytext=offset,
        textcoords="offset points",
        fontsize=9,
        fontweight="semibold",
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "-|>", "color": INK_MUTED, "lw": 1.5, "mutation_scale": 12},
        color=INK,
        path_effects=text_outline,
        zorder=5,
    )

# Integration bars — prominent thick lines below baseline
bar_y = -0.07
for center, ratio, rlabel in [(1.18, 3, "3H"), (2.61, 1, "1H"), (3.69, 2, "2H")]:
    hw = 0.28 * ratio / 3
    ax.plot(
        [center - hw, center + hw],
        [bar_y, bar_y],
        linewidth=7,
        color=BRAND,
        alpha=0.75,
        solid_capstyle="round",
        zorder=4,
    )
    ax.text(
        center,
        bar_y - 0.028,
        rlabel,
        ha="center",
        va="top",
        fontsize=8,
        color=BRAND,
        fontweight="bold",
        path_effects=text_outline,
    )

# Minor x-axis ticks at 0.2 ppm intervals (standard NMR scale)
ax.xaxis.set_major_locator(mticker.MultipleLocator(1.0))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.2))
ax.tick_params(axis="x", which="minor", length=3, width=0.8, color=INK_SOFT)
ax.tick_params(axis="x", which="major", length=6, width=1.2)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

# Title — length-aware fontsize scaling
title = "Ethanol ¹H NMR · spectrum-nmr · matplotlib · anyplot.ai"
title_fs = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

ax.set_title(title, fontsize=title_fs, fontweight="medium", pad=14, color=INK)
ax.set_xlabel("Chemical Shift (ppm)", fontsize=10, labelpad=10, color=INK)
ax.set_ylabel("Intensity", fontsize=10, color=INK)

# NMR conventions: reversed x-axis, no y-ticks
ax.set_xlim(5.0, -0.5)
ax.set_ylim(-0.12, 1.30)
ax.set_yticks([])

# Spine styling — remove top, right, left (NMR convention); keep bottom
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

# Molecule formula watermark
ax.text(
    0.98,
    0.95,
    "CH₃CH₂OH",
    transform=ax.transAxes,
    fontsize=11,
    fontweight="bold",
    ha="right",
    va="top",
    color=BRAND,
    alpha=0.30,
    fontstyle="italic",
)

fig.subplots_adjust(left=0.06, right=0.97, top=0.91, bottom=0.15)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
