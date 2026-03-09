""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
ppm = np.linspace(-0.5, 12, 6000)
spectrum = np.zeros_like(ppm)

# Lorentzian peak helper: amplitude / (1 + ((x - center) / width)^2)
w = 0.008
j = 0.035

# TMS reference peak at 0 ppm (singlet)
spectrum += 0.3 / (1 + ((ppm - 0.0) / 0.006) ** 2)

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
ax.plot(ppm, spectrum, linewidth=1.5, color="#306998")
ax.fill_between(ppm, spectrum, alpha=0.08, color="#306998")

# Annotations for key peaks
annotations = [
    (0.0, "TMS\n0.00 ppm", (30, 25)),
    (1.18, "CH₃ (triplet)\n1.18 ppm", (-60, 35)),
    (2.61, "OH (singlet)\n2.61 ppm", (0, 30)),
    (3.69, "CH₂ (quartet)\n3.69 ppm", (0, 30)),
]

for peak_ppm, label, offset in annotations:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_height = spectrum[peak_idx]
    ax.annotate(
        label,
        xy=(peak_ppm, peak_height),
        xytext=offset,
        textcoords="offset points",
        fontsize=14,
        fontweight="medium",
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "-", "color": "#555555", "lw": 1.2},
        color="#333333",
    )

# Style
ax.set_xlabel("Chemical Shift (ppm)", fontsize=20)
ax.set_ylabel("Intensity", fontsize=20)
ax.set_title("Ethanol ¹H NMR · spectrum-nmr · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(12, -0.5)
ax.set_ylim(-0.02, 1.25)
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
