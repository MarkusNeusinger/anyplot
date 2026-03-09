""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data — synthetic 1H NMR spectrum of ethanol
np.random.seed(42)
ppm = np.linspace(-0.5, 12.0, 6000)
width = 0.012

# Build spectrum from Lorentzian peaks: intensity * w^2 / ((x - x0)^2 + w^2)
spectrum = np.zeros_like(ppm)

# TMS reference peak at 0 ppm
w_tms = 0.01
spectrum += 0.4 * w_tms**2 / ((ppm - 0.0) ** 2 + w_tms**2)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 ratio, J ~ 0.07 ppm)
j_ch3 = 0.07
spectrum += 0.5 * width**2 / ((ppm - (1.18 - j_ch3)) ** 2 + width**2)
spectrum += 1.0 * width**2 / ((ppm - 1.18) ** 2 + width**2)
spectrum += 0.5 * width**2 / ((ppm - (1.18 + j_ch3)) ** 2 + width**2)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 ratio, J ~ 0.07 ppm)
j_ch2 = 0.07
spectrum += 0.25 * width**2 / ((ppm - (3.69 - 1.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.75 * width**2 / ((ppm - (3.69 - 0.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.75 * width**2 / ((ppm - (3.69 + 0.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.25 * width**2 / ((ppm - (3.69 + 1.5 * j_ch2)) ** 2 + width**2)

# OH singlet near 2.61 ppm
w_oh = 0.025
spectrum += 0.35 * w_oh**2 / ((ppm - 2.61) ** 2 + w_oh**2)

# Add subtle baseline noise
spectrum += np.random.normal(0, 0.003, len(ppm))
spectrum = np.clip(spectrum, 0, None)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.lineplot(x=ppm, y=spectrum, ax=ax, color="#306998", linewidth=1.5)

# Reverse x-axis (NMR convention: high ppm on left)
ax.invert_xaxis()
ax.set_xlim(12.0, -0.5)

# Annotate key peaks with staggered positions
peak_labels = [
    (0.0, "TMS\n0.00 ppm", (0.8, 0.45)),
    (1.18, "CH₃ triplet\n1.18 ppm", (1.18, 0.70)),
    (2.61, "OH singlet\n2.61 ppm", (4.5, 0.55)),
    (3.69, "CH₂ quartet\n3.69 ppm", (5.8, 0.70)),
]

max_intensity = spectrum.max()
for peak_ppm, label, text_pos in peak_labels:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_intensity = spectrum[peak_idx]
    ax.annotate(
        label,
        xy=(peak_ppm, peak_intensity),
        xytext=(text_pos[0], max_intensity * text_pos[1]),
        fontsize=13,
        ha="center",
        va="bottom",
        color="#333333",
        arrowprops={"arrowstyle": "-", "color": "#aaaaaa", "lw": 0.8},
    )

# Style
ax.set_xlabel("Chemical Shift (ppm)", fontsize=20)
ax.set_ylabel("Intensity", fontsize=20)
ax.set_title(
    "¹H NMR Spectrum of Ethanol · spectrum-nmr · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20
)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_yticks([])
ax.set_ylim(-0.01, max_intensity * 1.3)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
