""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data — Mild steel tensile test (realistic stress-strain behavior)
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_stress = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_stress / youngs_modulus

# Elastic region
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau (Lüders band, mild steel specific)
strain_plateau = np.linspace(yield_strain, 0.02, 30)
stress_plateau = np.full_like(strain_plateau, yield_stress) + np.random.normal(0, 1, len(strain_plateau))

# Strain hardening region
strain_hardening = np.linspace(0.02, uts_strain, 120)
t = (strain_hardening - 0.02) / (uts_strain - 0.02)
stress_hardening = yield_stress + (uts - yield_stress) * (1 - (1 - t) ** 2.5)

# Necking region (stress drops after UTS)
strain_necking = np.linspace(uts_strain, fracture_strain, 60)
t_neck = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
stress_necking = uts - (uts - 300) * t_neck**1.5

# Combine all regions
strain = np.concatenate([strain_elastic, strain_plateau, strain_hardening, strain_necking])
stress = np.concatenate([stress_elastic, stress_plateau, stress_hardening, stress_necking])

# 0.2% offset yield point
offset = 0.002
offset_line_strain = np.linspace(offset, offset + yield_stress / youngs_modulus + 0.003, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - offset)
offset_yield_strain = offset + yield_stress / youngs_modulus
offset_yield_stress = yield_stress

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.fill_between(strain, stress, alpha=0.04, color="#306998", zorder=2)
ax.plot(
    strain,
    stress,
    linewidth=3,
    color="#306998",
    zorder=5,
    path_effects=[pe.Stroke(linewidth=5, foreground="white"), pe.Normal()],
)

# 0.2% offset line
ax.plot(
    offset_line_strain,
    offset_line_stress,
    linewidth=2,
    color="#888888",
    linestyle="--",
    zorder=4,
    label="0.2% Offset Line",
)

# Mark critical points
ax.plot(
    offset_yield_strain,
    offset_yield_stress,
    "o",
    markersize=12,
    color="#7B4EA3",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=6,
)
ax.annotate(
    "Yield Point\n(0.2% Offset)",
    xy=(offset_yield_strain, offset_yield_stress),
    xytext=(0.04, yield_stress + 40),
    fontsize=14,
    color="#7B4EA3",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#7B4EA3", "lw": 1.5},
)

ax.plot(uts_strain, uts, "o", markersize=12, color="#D62728", markeredgecolor="white", markeredgewidth=1.5, zorder=6)
ax.annotate(
    "UTS",
    xy=(uts_strain, uts),
    xytext=(uts_strain + 0.02, uts + 20),
    fontsize=14,
    color="#D62728",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#D62728", "lw": 1.5},
)

fracture_stress = stress_necking[-1]
ax.plot(
    fracture_strain,
    fracture_stress,
    "X",
    markersize=14,
    color="#8C564B",
    markeredgecolor="white",
    markeredgewidth=1.5,
    zorder=6,
)
ax.annotate(
    "Fracture",
    xy=(fracture_strain, fracture_stress),
    xytext=(fracture_strain - 0.01, fracture_stress - 50),
    fontsize=14,
    color="#8C564B",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#8C564B", "lw": 1.5},
)

# Region shading with subtle color-coded backgrounds
region_colors = ["#306998", "#7B4EA3", "#306998", "#8C564B"]
region_bounds = [(0, yield_strain), (yield_strain, 0.02), (0.02, uts_strain), (uts_strain, fracture_strain)]
region_labels = ["Elastic", "Yield\nPlateau", "Strain Hardening", "Necking"]
region_alphas = [0.08, 0.06, 0.05, 0.05]

for (x0, x1), color, alpha in zip(region_bounds, region_colors, region_alphas, strict=False):
    ax.axvspan(x0, x1, alpha=alpha, color=color, zorder=1)

# Region labels — position above x-axis, avoiding the cramped elastic zone
ax.annotate(
    "Elastic",
    xy=(yield_strain / 2, 125),
    xytext=(0.025, 60),
    fontsize=14,
    color="#306998",
    fontstyle="italic",
    fontweight="semibold",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.0, "connectionstyle": "arc3,rad=0.2"},
)
ax.text(0.011, 50, "Yield\nPlateau", fontsize=11, ha="center", color="#7B4EA3", fontstyle="italic", alpha=0.9)
ax.text(0.12, 30, "Strain Hardening", fontsize=14, ha="center", color="#306998", fontstyle="italic", alpha=0.9)
ax.text(0.29, 30, "Necking", fontsize=14, ha="center", color="#8C564B", fontstyle="italic", alpha=0.9)

# Elastic modulus annotation
mid_elastic = len(strain_elastic) // 3
ax.annotate(
    f"E = {youngs_modulus:,} MPa",
    xy=(strain_elastic[mid_elastic], stress_elastic[mid_elastic]),
    xytext=(0.03, 150),
    fontsize=14,
    color="#444444",
    fontweight="semibold",
    arrowprops={"arrowstyle": "->", "color": "#444444", "lw": 1.2},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.8},
)

# Style
ax.set_xlabel("Engineering Strain (mm/mm)", fontsize=20)
ax.set_ylabel("Engineering Stress (MPa)", fontsize=20)
ax.set_title("line-stress-strain · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=28)
ax.text(
    0.5,
    1.015,
    "Mild Steel Tensile Test — E = 210 GPa, σᵧ = 250 MPa, UTS = 400 MPa",
    transform=ax.transAxes,
    fontsize=14,
    ha="center",
    color="#666666",
    fontstyle="italic",
)
ax.tick_params(axis="both", labelsize=16)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_linewidth(0.8)
    ax.spines[spine].set_color("#333333")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color="#888888")
ax.set_xlim(-0.01, 0.40)
ax.set_ylim(-10, 470)
ax.legend(fontsize=16, loc="center right", framealpha=0.9, edgecolor="#cccccc")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
