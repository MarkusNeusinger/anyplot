"""pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn styling — distinctive context and style management
sns.set_style("ticks", {"axes.linewidth": 0.8, "font.family": "serif"})
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

# Vectorized region assignment using np.select (replaces verbose for-loop)
conditions = [
    (ppm >= 3.5) & (ppm <= 3.9),
    (ppm >= 1.0) & (ppm <= 1.4),
    (ppm >= 2.4) & (ppm <= 2.8),
    (ppm >= -0.1) & (ppm <= 0.1),
]
choices = ["CH₂ quartet", "CH₃ triplet", "OH singlet", "TMS"]
df["Region"] = np.select(conditions, choices, default="Baseline")

# Colorblind-safe palette using seaborn's built-in colorblind palette
cb_palette = sns.color_palette("colorblind")
peak_palette = {
    "CH₂ quartet": cb_palette[0],  # blue
    "CH₃ triplet": cb_palette[2],  # green-teal (distinguishable)
    "OH singlet": cb_palette[4],  # sky blue
    "TMS": cb_palette[1],  # orange
    "Baseline": "#9e9e9e",
}

# Plot — use seaborn lineplot with hue for region-based coloring
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

# Plot baseline segments first (thin, muted)
df_baseline = df[df["Region"] == "Baseline"]
sns.lineplot(
    data=df_baseline, x="Chemical Shift (ppm)", y="Intensity", color="#b0b0b0", linewidth=0.7, ax=ax, legend=False
)

# Overlay each peak region with its own color and increasing linewidth for emphasis
region_order = ["TMS", "OH singlet", "CH₃ triplet", "CH₂ quartet"]
region_lw = {"TMS": 1.8, "OH singlet": 2.0, "CH₃ triplet": 2.4, "CH₂ quartet": 2.6}
for region in region_order:
    df_region = df[df["Region"] == region]
    sns.lineplot(
        data=df_region,
        x="Chemical Shift (ppm)",
        y="Intensity",
        color=peak_palette[region],
        linewidth=region_lw[region],
        ax=ax,
        label=region,
    )

# Add rug marks at peak centers — distinctive seaborn feature
peak_centers = pd.DataFrame({"Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69]})
sns.rugplot(data=peak_centers, x="Chemical Shift (ppm)", height=0.04, linewidth=2.0, color="#306998", ax=ax)

# Fill under peaks using seaborn fill_between via matplotlib for emphasis
for region in region_order:
    mask = df["Region"] == region
    ax.fill_between(
        df.loc[mask, "Chemical Shift (ppm)"], df.loc[mask, "Intensity"], alpha=0.15, color=peak_palette[region]
    )

# Reverse x-axis (NMR convention: high ppm on left)
ax.invert_xaxis()
ax.set_xlim(5.5, -0.5)

# Annotate key peaks directly above with short vertical connectors
max_intensity = spectrum.max()
peak_annotations = [
    (0.0, "TMS · 0.00 ppm", 0.22, peak_palette["TMS"]),
    (1.18, "CH₃ triplet · 1.18 ppm", 0.16, peak_palette["CH₃ triplet"]),
    (2.61, "OH singlet · 2.61 ppm", 0.28, peak_palette["OH singlet"]),
    (3.69, "CH₂ quartet · 3.69 ppm", 0.30, peak_palette["CH₂ quartet"]),
]

for peak_ppm, label, offset_frac, color in peak_annotations:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_intensity = spectrum[peak_idx]
    text_y = peak_intensity + max_intensity * offset_frac
    ax.annotate(
        label,
        xy=(peak_ppm, peak_intensity),
        xytext=(peak_ppm, text_y),
        fontsize=14,
        fontweight="medium",
        ha="center",
        va="bottom",
        color=color,
        arrowprops={"arrowstyle": "-", "color": color, "lw": 1.0},
    )

# Style using seaborn's despine and KDE-style labeling
ax.set_ylabel("Intensity", fontsize=20, labelpad=10)
ax.set_xlabel("Chemical Shift (ppm)", fontsize=20, labelpad=10)
ax.set_title(
    "¹H NMR Spectrum of Ethanol · spectrum-nmr · seaborn · pyplots.ai",
    fontsize=24,
    fontweight="semibold",
    pad=20,
    color="#2c3e50",
)
ax.set_yticks([])
ax.set_ylim(-0.01, max_intensity * 1.45)
ax.tick_params(axis="x", labelsize=16)

# Legend — seaborn-styled with refined frame
legend = ax.legend(
    loc="upper right",
    fontsize=14,
    frameon=True,
    framealpha=0.95,
    edgecolor="#d0d0d0",
    fancybox=True,
    shadow=True,
    title="Peak Assignment",
    title_fontsize=15,
)
legend.get_title().set_fontweight("semibold")

sns.despine(ax=ax, left=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#fafafa")
