""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
c_acid = 0.1
v_acid = 25.0
c_base = 0.1

volume_ml = np.linspace(0.01, 50, 1000)
ph = np.zeros_like(volume_ml)

for i, v in enumerate(volume_ml):
    moles_acid = c_acid * v_acid / 1000
    moles_base = c_base * v / 1000
    total_volume = (v_acid + v) / 1000

    if moles_base < moles_acid - 1e-10:
        h_plus = (moles_acid - moles_base) / total_volume
        ph[i] = -np.log10(h_plus)
    elif abs(moles_base - moles_acid) < 1e-10:
        ph[i] = 7.0
    else:
        oh_minus = (moles_base - moles_acid) / total_volume
        poh = -np.log10(oh_minus)
        ph[i] = 14.0 - poh

# Derivative (dpH/dV)
dph_dv = np.gradient(ph, volume_ml)

# Equivalence point
eq_volume = v_acid * c_acid / c_base
eq_ph = 7.0

# Cap derivative for readable secondary axis
dph_cap = np.percentile(dph_dv, 99) * 1.3
dph_dv_display = np.clip(dph_dv, 0, dph_cap)

# pH color gradient background
ph_cmap = LinearSegmentedColormap.from_list(
    "ph_gradient", ["#E8443A", "#F5D76E", "#4CAF50", "#306998", "#1A237E"], N=256
)

# Plot
fig, ax1 = plt.subplots(figsize=(16, 9))
ax2 = ax1.twinx()

# Subtle pH color gradient strip along left y-axis
ph_gradient = np.linspace(0, 14, 256).reshape(-1, 1)
ax1.imshow(ph_gradient, aspect="auto", cmap=ph_cmap, alpha=0.05, extent=[0, 50, 0, 14], origin="lower", zorder=0)

# Main titration curve
ax1.plot(volume_ml, ph, color="#306998", linewidth=3.5, zorder=3, solid_capstyle="round")

# Derivative curve — line only with subtle fill near peak
ax2.plot(volume_ml, dph_dv_display, color="#E8875B", linewidth=2, alpha=0.8, zorder=2)
peak_mask = (volume_ml >= 20) & (volume_ml <= 30)
ax2.fill_between(volume_ml[peak_mask], 0, dph_dv_display[peak_mask], color="#E8875B", alpha=0.2, zorder=1)

# Equivalence point marker and vertical line
ax1.axvline(x=eq_volume, color="#888888", linestyle=":", linewidth=1.2, alpha=0.5, zorder=2)
ax1.scatter([eq_volume], [eq_ph], color="#D64045", s=280, edgecolors="white", linewidth=2, zorder=5)
ax1.annotate(
    f"Equivalence Point\n{eq_volume:.0f} mL · pH {eq_ph:.0f}",
    xy=(eq_volume, eq_ph),
    xytext=(eq_volume + 9, eq_ph - 3.5),
    fontsize=15,
    fontweight="medium",
    color="#333333",
    arrowprops={"arrowstyle": "-|>", "color": "#666666", "lw": 1.5, "connectionstyle": "arc3,rad=-0.15"},
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "#FFF8F0", "edgecolor": "#D64045", "alpha": 0.95, "linewidth": 1.2},
)

# Buffer/gradual pH change region shading
buffer_left = 2
buffer_right = 20
mask = (volume_ml >= buffer_left) & (volume_ml <= buffer_right)
ax1.fill_between(volume_ml[mask], 0, ph[mask], alpha=0.18, color="#306998", zorder=1, linewidth=0)
ax1.text(
    11,
    1.4,
    "Gradual pH Change Region",
    fontsize=15,
    color="#306998",
    alpha=0.9,
    ha="center",
    style="italic",
    fontweight="medium",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.75},
)

# Steep rise annotation
ax1.annotate(
    "Steep rise\nnear equivalence",
    xy=(24.5, 6),
    xytext=(10, 11.5),
    fontsize=13,
    color="#555555",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#999999", "lw": 1.2, "connectionstyle": "arc3,rad=0.3"},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.85},
)

# Neutral pH reference line
ax1.axhline(y=7, color="#999999", linestyle="--", linewidth=0.8, alpha=0.35, zorder=1)
ax1.text(49.5, 7.3, "Neutral pH 7", fontsize=11, color="#999999", ha="right", alpha=0.7)

# Style — primary axis
ax1.set_xlabel("Volume of NaOH added (mL)", fontsize=20, labelpad=10)
ax1.set_ylabel("pH", fontsize=20, color="#306998", labelpad=10)
ax1.set_ylim(0, 14)
ax1.set_xlim(0, 50)
ax1.tick_params(axis="both", labelsize=16)
ax1.tick_params(axis="y", colors="#306998")
ax1.spines["top"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.12, linewidth=0.6, color="#306998")
ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax1.tick_params(which="minor", length=3, color="#cccccc")

# Style — secondary axis
ax2.set_ylabel("dpH/dV (rate of pH change)", fontsize=20, color="#E8875B", labelpad=10)
ax2.tick_params(axis="y", labelsize=16, colors="#E8875B")
ax2.spines["top"].set_visible(False)

# Title
ax1.set_title(
    "HCl + NaOH Titration · titration-curve · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
    color="#222222",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
