""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Strain hardening (quadratic rise to UTS)
strain_hardening = np.linspace(yield_strain, uts_strain, 200)
t = (strain_hardening - yield_strain) / (uts_strain - yield_strain)
stress_hardening = yield_stress + (uts - yield_stress) * (2 * t - t**2)

# Necking region (UTS to fracture — stress drops)
strain_necking = np.linspace(uts_strain, fracture_strain, 100)
t_neck = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
fracture_stress = 320
stress_necking = uts - (uts - fracture_stress) * t_neck**1.5

# Build DataFrame with region labels for seaborn hue-based plotting
df_elastic = pd.DataFrame({"strain": strain_elastic, "stress": stress_elastic, "region": "Elastic"})
df_hardening = pd.DataFrame({"strain": strain_hardening, "stress": stress_hardening, "region": "Strain Hardening"})
df_necking = pd.DataFrame({"strain": strain_necking, "stress": stress_necking, "region": "Necking"})
df = pd.concat([df_elastic, df_hardening, df_necking], ignore_index=True)

# 0.2% offset yield point
offset = 0.002
offset_line_strain = np.linspace(offset, offset + yield_stress / youngs_modulus + 0.003, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - offset)
offset_line_stress = np.clip(offset_line_stress, 0, yield_stress + 20)

yield_offset_strain = offset + yield_stress / youngs_modulus
yield_offset_stress = yield_stress

# Define seaborn palette and style
region_palette = {"Elastic": "#306998", "Strain Hardening": "#E07B39", "Necking": "#C0392B"}
sns.set_style("whitegrid", {"grid.linestyle": "-", "grid.alpha": 0.15, "grid.linewidth": 0.8})
sns.set_context(
    "talk",
    rc={
        "axes.titlesize": 24,
        "axes.labelsize": 20,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 13,
        "font.weight": "medium",
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Plot stress-strain curve using seaborn lineplot with hue for regions
sns.lineplot(
    data=df, x="strain", y="stress", hue="region", palette=region_palette, linewidth=3.5, ax=ax, legend=True, sort=False
)

# 0.2% offset line
ax.plot(offset_line_strain, offset_line_stress, linestyle="--", linewidth=2, color="#808080", zorder=3)

# Mark critical points using seaborn scatterplot for consistent styling
critical_points = pd.DataFrame(
    {
        "strain": [yield_offset_strain, uts_strain, fracture_strain],
        "stress": [yield_offset_stress, uts, fracture_stress],
        "point": ["Yield Point", "UTS", "Fracture"],
    }
)
point_palette = {"Yield Point": "#E07B39", "UTS": "#C0392B", "Fracture": "#2C3E50"}
point_markers = {"Yield Point": "o", "UTS": "o", "Fracture": "X"}
sns.scatterplot(
    data=critical_points,
    x="strain",
    y="stress",
    hue="point",
    style="point",
    palette=point_palette,
    markers=point_markers,
    s=200,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
    zorder=5,
    legend=True,
)

# Annotations for critical points — yield moved right to reduce left-side clutter
ax.annotate(
    "Yield Point\n(0.2% offset)",
    xy=(yield_offset_strain, yield_offset_stress),
    xytext=(0.06, yield_offset_stress - 30),
    fontsize=14,
    fontweight="bold",
    color="#E07B39",
    arrowprops={"arrowstyle": "-|>", "color": "#E07B39", "lw": 1.5},
    ha="left",
    va="top",
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

# Elastic modulus annotation — positioned to the right to avoid left-side clutter
ax.annotate(
    f"E = {youngs_modulus // 1000} GPa",
    xy=(yield_strain * 0.5, youngs_modulus * yield_strain * 0.5),
    xytext=(0.05, 60),
    fontsize=13,
    fontstyle="italic",
    color="#306998",
    arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 1.2},
    ha="left",
    va="center",
)

# Region shading using axvspan
region_shading = [
    (0, yield_strain, "#306998"),
    (yield_strain, uts_strain, "#E07B39"),
    (uts_strain, fracture_strain, "#C0392B"),
]
for x0, x1, color in region_shading:
    ax.axvspan(x0, x1, alpha=0.06, color=color, zorder=0)

# Style using seaborn's despine
sns.despine(ax=ax)
ax.xaxis.grid(False)
ax.set_xlabel("Engineering Strain")
ax.set_ylabel("Engineering Stress (MPa)")
ax.set_title("line-stress-strain · seaborn · pyplots.ai", fontweight="medium")
ax.set_xlim(-0.01, fracture_strain + 0.03)
ax.set_ylim(-10, uts + 80)

# Consolidate legend: combine region lines and critical point markers
handles, labels = ax.get_legend_handles_labels()
# Reorder: regions first, then critical points
ax.legend(handles=handles, labels=labels, fontsize=13, loc="center right", framealpha=0.9, edgecolor="#cccccc")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
