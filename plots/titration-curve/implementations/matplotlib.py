"""pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np


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

# Equivalence point (analytically: 25 mL, pH 7.0 for strong acid + strong base)
eq_volume = v_acid * c_acid / c_base
eq_ph = 7.0

# Plot
fig, ax1 = plt.subplots(figsize=(16, 9))
ax2 = ax1.twinx()

ax1.plot(volume_ml, ph, color="#306998", linewidth=3, zorder=3)
ax2.plot(volume_ml, dph_dv, color="#E8875B", linewidth=2, alpha=0.7, zorder=2)

# Equivalence point marker and line
ax1.axvline(x=eq_volume, color="#555555", linestyle="--", linewidth=1.5, alpha=0.6)
ax1.scatter([eq_volume], [eq_ph], color="#D64045", s=250, edgecolors="white", linewidth=1.5, zorder=5)
ax1.annotate(
    f"Equivalence Point\n{eq_volume:.0f} mL, pH {eq_ph:.0f}",
    xy=(eq_volume, eq_ph),
    xytext=(eq_volume + 8, eq_ph - 3),
    fontsize=15,
    color="#333333",
    arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Slow pH change region shading (before the steep rise)
buffer_left = 2
buffer_right = 20
mask = (volume_ml >= buffer_left) & (volume_ml <= buffer_right)
ax1.fill_between(volume_ml[mask], 0, ph[mask], alpha=0.08, color="#306998", zorder=1)
ax1.text(11, 0.6, "Gradual pH change region", fontsize=13, color="#306998", alpha=0.7, ha="center", style="italic")

# Style — primary axis
ax1.set_xlabel("Volume of NaOH added (mL)", fontsize=20)
ax1.set_ylabel("pH", fontsize=20, color="#306998")
ax1.set_ylim(0, 14)
ax1.set_xlim(0, 50)
ax1.tick_params(axis="both", labelsize=16)
ax1.tick_params(axis="y", colors="#306998")
ax1.spines["top"].set_visible(False)
ax1.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Style — secondary axis
ax2.set_ylabel("dpH/dV", fontsize=20, color="#E8875B")
ax2.tick_params(axis="y", labelsize=16, colors="#E8875B")
ax2.spines["top"].set_visible(False)

# Title
ax1.set_title(
    "HCl + NaOH Titration · titration-curve · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
