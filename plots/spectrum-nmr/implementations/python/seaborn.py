""" anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-03
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order, first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

peak_palette = {"CH₂ quartet": IMPRINT[0], "OH singlet": IMPRINT[1], "CH₃ triplet": IMPRINT[2], "TMS": IMPRINT[3]}

# Seaborn theme — warm off-white / near-black surfaces, serif font
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
        "font.family": "serif",
    },
)

# Data — synthetic 1H NMR spectrum of ethanol (Lorentzian peak shapes)
np.random.seed(42)
ppm = np.linspace(-0.5, 5.5, 6000)
width = 0.012

spectrum = np.zeros_like(ppm)

# TMS reference at 0 ppm
w_tms = 0.01
spectrum += 0.4 * w_tms**2 / ((ppm - 0.0) ** 2 + w_tms**2)

# CH3 triplet at 1.18 ppm (1:2:1 ratio, J = 0.07 ppm)
j_ch3 = 0.07
spectrum += 0.5 * width**2 / ((ppm - (1.18 - j_ch3)) ** 2 + width**2)
spectrum += 1.0 * width**2 / ((ppm - 1.18) ** 2 + width**2)
spectrum += 0.5 * width**2 / ((ppm - (1.18 + j_ch3)) ** 2 + width**2)

# CH2 quartet at 3.69 ppm (1:3:3:1 ratio, J = 0.07 ppm)
j_ch2 = 0.07
spectrum += 0.25 * width**2 / ((ppm - (3.69 - 1.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.75 * width**2 / ((ppm - (3.69 - 0.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.75 * width**2 / ((ppm - (3.69 + 0.5 * j_ch2)) ** 2 + width**2)
spectrum += 0.25 * width**2 / ((ppm - (3.69 + 1.5 * j_ch2)) ** 2 + width**2)

# OH singlet at 2.61 ppm (slightly broad due to proton exchange)
w_oh = 0.025
spectrum += 0.35 * w_oh**2 / ((ppm - 2.61) ** 2 + w_oh**2)

spectrum += np.random.normal(0, 0.003, len(ppm))
spectrum = np.clip(spectrum, 0, None)

# DataFrame with region labels (vectorized with np.select)
df = pd.DataFrame({"Chemical Shift (ppm)": ppm, "Intensity": spectrum})
conditions = [
    (ppm >= 3.5) & (ppm <= 3.9),
    (ppm >= 2.4) & (ppm <= 2.8),
    (ppm >= 1.0) & (ppm <= 1.4),
    (ppm >= -0.1) & (ppm <= 0.1),
]
choices = ["CH₂ quartet", "OH singlet", "CH₃ triplet", "TMS"]
df["Region"] = np.select(conditions, choices, default="Baseline")

# Plot — 3200×1800 px canvas (figsize=(8,4.5) × dpi=400)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Baseline (thin, muted — plotted separately)
sns.lineplot(
    data=df[df["Region"] == "Baseline"],
    x="Chemical Shift (ppm)",
    y="Intensity",
    color=INK_SOFT,
    linewidth=0.6,
    ax=ax,
    legend=False,
)

# Signal peaks — single hue-based lineplot (idiomatic seaborn)
hue_order = ["CH₂ quartet", "OH singlet", "CH₃ triplet", "TMS"]
sns.lineplot(
    data=df[df["Region"] != "Baseline"],
    x="Chemical Shift (ppm)",
    y="Intensity",
    hue="Region",
    hue_order=hue_order,
    palette=peak_palette,
    linewidth=2.2,
    ax=ax,
)

# Rug marks at peak centers (distinctive seaborn feature)
sns.rugplot(
    data=pd.DataFrame({"Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69]}),
    x="Chemical Shift (ppm)",
    height=0.04,
    linewidth=1.8,
    color=INK_SOFT,
    ax=ax,
)

# Semi-transparent fill under each peak region
for region in hue_order:
    mask = df["Region"] == region
    ax.fill_between(
        df.loc[mask, "Chemical Shift (ppm)"], df.loc[mask, "Intensity"], alpha=0.12, color=peak_palette[region]
    )

# NMR convention: high ppm on left
ax.invert_xaxis()
ax.set_xlim(5.5, -0.5)

# Peak annotations with color-matched connectors
max_intensity = spectrum.max()
peak_annotations = [
    (0.0, "TMS · 0.00 ppm", 0.26, peak_palette["TMS"]),
    (1.18, "CH₃ · 1.18 ppm", 0.18, peak_palette["CH₃ triplet"]),
    (2.61, "OH · 2.61 ppm", 0.32, peak_palette["OH singlet"]),
    (3.69, "CH₂ · 3.69 ppm", 0.30, peak_palette["CH₂ quartet"]),
]
for peak_ppm, label, offset_frac, color in peak_annotations:
    peak_idx = np.argmin(np.abs(ppm - peak_ppm))
    peak_intensity = spectrum[peak_idx]
    text_y = peak_intensity + max_intensity * offset_frac
    ax.annotate(
        label,
        xy=(peak_ppm, peak_intensity),
        xytext=(peak_ppm, text_y),
        fontsize=8,
        fontweight="medium",
        ha="center",
        va="bottom",
        color=color,
        arrowprops={"arrowstyle": "-", "color": color, "lw": 0.8},
    )

# Style
title = "¹H NMR Spectrum of Ethanol · spectrum-nmr · python · seaborn · anyplot.ai"
title_n = len(title)
title_fs = max(8, round(12 * 67 / title_n)) if title_n > 67 else 12

ax.set_title(title, fontsize=title_fs, fontweight="semibold", pad=10, color=INK)
ax.set_xlabel("Chemical Shift (ppm)", fontsize=10, color=INK)
ax.set_ylabel("Intensity", fontsize=10, color=INK)
ax.set_yticks([])
ax.set_ylim(-0.02, max_intensity * 1.55)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)

# Legend
legend = ax.legend(
    loc="upper right",
    fontsize=8,
    frameon=True,
    framealpha=0.92,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
    title="Peak Assignment",
    title_fontsize=8,
)
legend.get_title().set_fontweight("semibold")
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

sns.despine(ax=ax, left=True)

# Save — bbox_inches omitted so canvas stays exactly figsize × dpi = 3200 × 1800 px
fig.subplots_adjust(top=0.88, bottom=0.13, left=0.06, right=0.97)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
