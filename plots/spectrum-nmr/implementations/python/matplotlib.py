""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-09
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data - synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
ppm = np.linspace(-0.5, 5.0, 6000)
spectrum = np.zeros_like(ppm)

# Lorentzian peak helper: amplitude / (1 + ((x - center) / width)^2)
w = 0.025
j = 0.055

# TMS reference peak at 0 ppm (singlet)
spectrum += 0.3 / (1 + ((ppm - 0.0) / 0.015) ** 2)

# CH3 triplet near 1.18 ppm (ratio 1:2:1)
spectrum += 0.50 / (1 + ((ppm - (1.18 - j)) / w) ** 2)
spectrum += 1.00 / (1 + ((ppm - 1.18) / w) ** 2)
spectrum += 0.50 / (1 + ((ppm - (1.18 + j)) / w) ** 2)

# CH2 quartet near 3.69 ppm (ratio 1:3:3:1)
spectrum += 0.25 / (1 + ((ppm - (3.69 - 1.5 * j)) / w) ** 2)
spectrum += 0.75 / (1 + ((ppm - (3.69 - 0.5 * j)) / w) ** 2)
spectrum += 0.75 / (1 + ((ppm - (3.69 + 0.5 * j)) / w) ** 2)
spectrum += 0.25 / (1 + ((ppm - (3.69 + 1.5 * j)) / w) ** 2)

# OH singlet near 2.61 ppm
spectrum += 0.40 / (1 + ((ppm - 2.61) / w) ** 2)

# Add subtle baseline noise
spectrum += np.random.normal(0, 0.003, len(ppm))
spectrum = np.clip(spectrum, 0, None)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.plot(ppm, spectrum, linewidth=2.8, color="#306998", zorder=3)
ax.fill_between(ppm, spectrum, alpha=0.12, color="#306998", zorder=2)

# Highlight peak regions with axvspan
peak_regions = [(-0.15, 0.15, "TMS"), (1.0, 1.35, "CH₃"), (2.45, 2.75, "OH"), (3.5, 3.9, "CH₂")]
for lo, hi, _ in peak_regions:
    ax.axvspan(lo, hi, alpha=0.06, color="#306998", zorder=1)

# Annotations for key peaks with path effects for readability
annotations = [
    (0.0, "TMS\n0.00 ppm", (40, 30)),
    (1.18, "CH₃ (triplet)\n1.18 ppm", (80, -50)),
    (2.61, "OH (singlet)\n2.61 ppm", (-55, 35)),
    (3.69, "CH₂ (quartet)\n3.69 ppm", (-60, 40)),
]

text_outline = [pe.withStroke(linewidth=3, foreground="white")]

for peak_ppm, label, offset in annotations:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_height = spectrum[peak_idx]
    ax.annotate(
        label,
        xy=(peak_ppm, peak_height),
        xytext=offset,
        textcoords="offset points",
        fontsize=16,
        fontweight="semibold",
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "-|>", "color": "#555555", "lw": 1.5, "mutation_scale": 12},
        color="#222222",
        path_effects=text_outline,
        zorder=5,
    )

# Integration ratio bar under each peak group (distinctive matplotlib feature)
ratio_data = [(1.18, 3, "3H"), (2.61, 1, "1H"), (3.69, 2, "2H")]
bar_y = -0.06
for center, ratio, rlabel in ratio_data:
    bar_width = 0.25 * ratio / 3
    ax.plot(
        [center - bar_width, center + bar_width],
        [bar_y, bar_y],
        linewidth=5,
        color="#306998",
        alpha=0.5,
        solid_capstyle="round",
        zorder=4,
    )
    ax.text(
        center,
        bar_y - 0.025,
        rlabel,
        ha="center",
        va="top",
        fontsize=14,
        color="#306998",
        fontweight="bold",
        path_effects=text_outline,
    )

# Custom minor ticks (distinctive matplotlib feature)
ax.xaxis.set_major_locator(mticker.MultipleLocator(1.0))
ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.2))
ax.tick_params(axis="x", which="minor", length=3, width=0.8, color="#999999")
ax.tick_params(axis="x", which="major", length=6, width=1.2)

# Style
ax.set_xlabel("Chemical Shift (ppm)", fontsize=20, labelpad=12)
ax.set_ylabel("Intensity", fontsize=20)
ax.set_title("Ethanol ¹H NMR · spectrum-nmr · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(5.0, -0.5)
ax.set_ylim(-0.1, 1.25)
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

# Molecule label using ax.text with transform (distinctive feature)
ax.text(
    0.98,
    0.95,
    "CH₃CH₂OH",
    transform=ax.transAxes,
    fontsize=22,
    fontweight="bold",
    ha="right",
    va="top",
    color="#306998",
    alpha=0.35,
    fontstyle="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
