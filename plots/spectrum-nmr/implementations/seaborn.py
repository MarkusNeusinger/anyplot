""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn styling — distinctive context and style management
sns.set_style("ticks", {"axes.linewidth": 0.8})
sns.set_context("talk", font_scale=1.1, rc={"lines.linewidth": 1.8})

# Data — synthetic 1H NMR spectrum of ethanol
np.random.seed(42)
ppm = np.linspace(-0.5, 5.5, 6000)
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

# Build DataFrame for seaborn — enables semantic data handling
df = pd.DataFrame({"Chemical Shift (ppm)": ppm, "Intensity": spectrum})

# Assign peak regions for hue-based coloring
peak_regions = []
peak_palette = {}
for s in ppm:
    if 3.5 <= s <= 3.9:
        peak_regions.append("CH₂ quartet")
    elif 1.0 <= s <= 1.4:
        peak_regions.append("CH₃ triplet")
    elif 2.4 <= s <= 2.8:
        peak_regions.append("OH singlet")
    elif -0.1 <= s <= 0.1:
        peak_regions.append("TMS")
    else:
        peak_regions.append("Baseline")

df["Region"] = peak_regions

# Custom palette using seaborn color palette tools
region_colors = sns.color_palette("deep", n_colors=5)
peak_palette = {
    "CH₂ quartet": region_colors[0],
    "CH₃ triplet": region_colors[1],
    "OH singlet": region_colors[2],
    "TMS": region_colors[3],
    "Baseline": "#888888",
}

# Plot — use seaborn lineplot with hue for region-based coloring
fig, ax = plt.subplots(figsize=(16, 9))

# Plot baseline segments first (thin, gray)
df_baseline = df[df["Region"] == "Baseline"]
sns.lineplot(
    data=df_baseline, x="Chemical Shift (ppm)", y="Intensity", color="#888888", linewidth=0.8, ax=ax, legend=False
)

# Overlay each peak region with its own color
for region in ["TMS", "CH₃ triplet", "OH singlet", "CH₂ quartet"]:
    df_region = df[df["Region"] == region]
    sns.lineplot(
        data=df_region,
        x="Chemical Shift (ppm)",
        y="Intensity",
        color=peak_palette[region],
        linewidth=2.2,
        ax=ax,
        label=region,
    )

# Add rug marks at peak centers — distinctive seaborn feature
peak_centers = pd.DataFrame({"Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69]})
sns.rugplot(data=peak_centers, x="Chemical Shift (ppm)", height=0.04, linewidth=1.5, color="#306998", ax=ax)

# Reverse x-axis (NMR convention: high ppm on left)
ax.invert_xaxis()
ax.set_xlim(5.5, -0.5)

# Annotate key peaks with staggered positions
max_intensity = spectrum.max()
peak_labels = [
    (0.0, "TMS\n0.00 ppm", (0.5, 0.55)),
    (1.18, "CH₃ triplet\n1.18 ppm", (1.18, 0.80)),
    (2.61, "OH singlet\n2.61 ppm", (2.61, 0.65)),
    (3.69, "CH₂ quartet\n3.69 ppm", (4.2, 0.80)),
]

for peak_ppm, label, text_pos in peak_labels:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_intensity = spectrum[peak_idx]
    ax.annotate(
        label,
        xy=(peak_ppm, peak_intensity),
        xytext=(text_pos[0], max_intensity * text_pos[1]),
        fontsize=15,
        ha="center",
        va="bottom",
        color="#333333",
        arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.0},
    )

# Style using seaborn's despine
ax.set_ylabel("Intensity", fontsize=20)
ax.set_title(
    "¹H NMR Spectrum of Ethanol · spectrum-nmr · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20
)
ax.set_yticks([])
ax.set_ylim(-0.01, max_intensity * 1.3)

# Legend — seaborn-styled
ax.legend(
    loc="upper right",
    fontsize=14,
    frameon=True,
    framealpha=0.9,
    edgecolor="#cccccc",
    title="Peak Assignment",
    title_fontsize=15,
)

sns.despine(ax=ax, left=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
