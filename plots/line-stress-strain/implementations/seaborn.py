""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data — Mild steel tensile test simulation
np.random.seed(42)

youngs_modulus = 200000  # MPa
yield_stress = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_stress / youngs_modulus

# Elastic region
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau and strain hardening (quadratic rise to UTS)
strain_hardening = np.linspace(yield_strain, uts_strain, 200)
t = (strain_hardening - yield_strain) / (uts_strain - yield_strain)
stress_hardening = yield_stress + (uts - yield_stress) * (2 * t - t**2)

# Necking region (UTS to fracture — stress drops)
strain_necking = np.linspace(uts_strain, fracture_strain, 100)
t_neck = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
fracture_stress = 320
stress_necking = uts - (uts - fracture_stress) * t_neck**1.5

# Combine all regions
strain = np.concatenate([strain_elastic, strain_hardening, strain_necking])
stress = np.concatenate([stress_elastic, stress_hardening, stress_necking])

# 0.2% offset yield point
offset = 0.002
offset_line_strain = np.linspace(offset, offset + yield_stress / youngs_modulus + 0.003, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - offset)
offset_line_stress = np.clip(offset_line_stress, 0, yield_stress + 20)

# Find intersection point (0.2% offset yield)
yield_offset_strain = offset + yield_stress / youngs_modulus
yield_offset_stress = yield_stress

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(x=strain, y=stress, ax=ax, linewidth=3.5, color="#306998", legend=False)

# 0.2% offset line
ax.plot(offset_line_strain, offset_line_stress, linestyle="--", linewidth=2, color="#808080", zorder=3)

# Mark critical points
ax.plot(
    yield_offset_strain,
    yield_offset_stress,
    "o",
    markersize=12,
    color="#E07B39",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=5,
)
ax.plot(uts_strain, uts, "o", markersize=12, color="#C0392B", markeredgecolor="white", markeredgewidth=1.5, zorder=5)
ax.plot(
    fracture_strain,
    fracture_stress,
    "X",
    markersize=14,
    color="#2C3E50",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=5,
)

# Annotations for critical points
ax.annotate(
    "Yield Point\n(0.2% offset)",
    xy=(yield_offset_strain, yield_offset_stress),
    xytext=(0.04, yield_offset_stress + 40),
    fontsize=14,
    fontweight="bold",
    color="#E07B39",
    arrowprops={"arrowstyle": "-|>", "color": "#E07B39", "lw": 1.5},
    ha="left",
    va="bottom",
)

ax.annotate(
    f"UTS = {uts} MPa",
    xy=(uts_strain, uts),
    xytext=(uts_strain + 0.03, uts + 30),
    fontsize=14,
    fontweight="bold",
    color="#C0392B",
    arrowprops={"arrowstyle": "-|>", "color": "#C0392B", "lw": 1.5},
    ha="left",
    va="bottom",
)

ax.annotate(
    "Fracture",
    xy=(fracture_strain, fracture_stress),
    xytext=(fracture_strain - 0.01, fracture_stress - 60),
    fontsize=14,
    fontweight="bold",
    color="#2C3E50",
    arrowprops={"arrowstyle": "-|>", "color": "#2C3E50", "lw": 1.5},
    ha="center",
    va="top",
)

# Elastic modulus annotation
mid_elastic_strain = yield_strain * 0.45
mid_elastic_stress = youngs_modulus * mid_elastic_strain
ax.annotate(
    f"E = {youngs_modulus // 1000} GPa",
    xy=(mid_elastic_strain, mid_elastic_stress),
    xytext=(0.03, 80),
    fontsize=13,
    fontstyle="italic",
    color="#306998",
    arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 1.2},
    ha="left",
    va="center",
)

# Region labels (shaded backgrounds)
ax.axvspan(0, yield_strain, alpha=0.06, color="#306998")
ax.axvspan(yield_strain, uts_strain, alpha=0.06, color="#E07B39")
ax.axvspan(uts_strain, fracture_strain, alpha=0.06, color="#C0392B")

ax.text(yield_strain / 2, -28, "Elastic", fontsize=12, ha="center", color="#306998", fontweight="medium")
ax.text(
    (yield_strain + uts_strain) / 2,
    -28,
    "Strain Hardening",
    fontsize=12,
    ha="center",
    color="#E07B39",
    fontweight="medium",
)
ax.text(
    (uts_strain + fracture_strain) / 2, -28, "Necking", fontsize=12, ha="center", color="#C0392B", fontweight="medium"
)

# 0.2% offset label
ax.text(offset + 0.001, -18, "0.2%", fontsize=11, color="#808080", ha="left")

# Style
ax.set_xlabel("Engineering Strain", fontsize=20)
ax.set_ylabel("Engineering Stress (MPa)", fontsize=20)
ax.set_title("Mild Steel Tensile Test · line-stress-strain · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_xlim(-0.01, fracture_strain + 0.03)
ax.set_ylim(-45, uts + 80)

# Legend for critical points
legend_elements = [
    mpatches.Patch(facecolor="#306998", alpha=0.15, label="Elastic region"),
    mpatches.Patch(facecolor="#E07B39", alpha=0.15, label="Strain hardening"),
    mpatches.Patch(facecolor="#C0392B", alpha=0.15, label="Necking"),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#E07B39",
        markeredgecolor="white",
        markersize=10,
        label="Yield point",
    ),
    plt.Line2D(
        [0], [0], marker="o", color="w", markerfacecolor="#C0392B", markeredgecolor="white", markersize=10, label="UTS"
    ),
    plt.Line2D(
        [0],
        [0],
        marker="X",
        color="w",
        markerfacecolor="#2C3E50",
        markeredgecolor="white",
        markersize=10,
        label="Fracture",
    ),
]
ax.legend(handles=legend_elements, fontsize=13, loc="center right", framealpha=0.9, edgecolor="#cccccc")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
