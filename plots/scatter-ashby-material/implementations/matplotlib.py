""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull


# Data - Density (kg/m^3) vs Young's Modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {
        "density": [2700, 4500, 7850, 8900, 7200, 8000, 11340, 1740, 7870, 8940, 2810, 7140, 8500, 4620, 7300],
        "modulus": [69, 116, 200, 117, 170, 193, 16, 45, 210, 130, 71, 105, 100, 110, 190],
    },
    "Polymers": {
        "density": [950, 1050, 1200, 1140, 1380, 910, 1420, 1040, 1300, 1170, 980, 1090, 1250, 1060, 1350],
        "modulus": [0.9, 2.5, 3.5, 2.8, 3.0, 1.3, 2.9, 2.0, 4.0, 3.2, 0.7, 1.8, 3.8, 2.2, 3.3],
    },
    "Ceramics": {
        "density": [3980, 3200, 2200, 3900, 5680, 2650, 3150, 5900, 2400, 3500, 3100, 4000, 2500, 3700, 2800],
        "modulus": [380, 440, 70, 350, 200, 73, 310, 210, 65, 400, 300, 360, 60, 320, 90],
    },
    "Composites": {
        "density": [1600, 1550, 2000, 1800, 1450, 1700, 1900, 1500, 1650, 1850, 1520, 1750, 1400, 1620, 1950],
        "modulus": [140, 70, 45, 80, 180, 60, 50, 200, 120, 55, 90, 65, 160, 100, 40],
    },
    "Elastomers": {
        "density": [920, 1100, 1250, 1500, 1050, 1150, 1300, 1000, 1200, 1400, 960, 1080, 1350, 1450, 1180],
        "modulus": [0.005, 0.01, 0.05, 0.03, 0.008, 0.02, 0.04, 0.003, 0.015, 0.035, 0.004, 0.012, 0.045, 0.025, 0.007],
    },
    "Foams": {
        "density": [30, 60, 120, 200, 50, 80, 150, 40, 100, 180, 35, 70, 130, 90, 160],
        "modulus": [0.001, 0.01, 0.05, 0.2, 0.005, 0.02, 0.1, 0.003, 0.03, 0.15, 0.002, 0.015, 0.06, 0.025, 0.12],
    },
    "Natural\nMaterials": {
        "density": [600, 700, 500, 1200, 800, 450, 650, 1500, 550, 750, 900, 480, 680, 1100, 850],
        "modulus": [12, 14, 8, 20, 10, 6, 11, 25, 9, 13, 16, 7, 12.5, 18, 15],
    },
}

family_colors = {
    "Metals": "#306998",
    "Polymers": "#E07B39",
    "Ceramics": "#C0392B",
    "Composites": "#5BA58B",
    "Elastomers": "#8B6BAE",
    "Foams": "#7FADA0",
    "Natural\nMaterials": "#BFA24E",
}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

for family_name, data in families.items():
    density = np.array(data["density"], dtype=float)
    modulus = np.array(data["modulus"], dtype=float)
    color = family_colors[family_name]

    # Scatter points
    ax.scatter(density, modulus, s=120, alpha=0.7, color=color, edgecolors="white", linewidth=0.8, zorder=4)

    # Convex hull envelope in log space
    log_pts = np.column_stack([np.log10(density), np.log10(modulus)])

    # Add slight jitter to handle collinear points
    jitter = np.random.RandomState(hash(family_name) % 2**31).randn(*log_pts.shape) * 0.01
    log_pts_jittered = log_pts + jitter

    try:
        hull = ConvexHull(log_pts_jittered)
        hull_indices = np.append(hull.vertices, hull.vertices[0])
        hull_density = 10 ** log_pts[hull_indices, 0]
        hull_modulus = 10 ** log_pts[hull_indices, 1]
        ax.fill(hull_density, hull_modulus, alpha=0.15, color=color, zorder=2)
        ax.plot(hull_density, hull_modulus, color=color, alpha=0.4, linewidth=1.5, zorder=3)
    except Exception:
        pass

    # Label at geometric center
    center_x = 10 ** np.mean(np.log10(density))
    center_y = 10 ** np.mean(np.log10(modulus))
    ax.text(
        center_x,
        center_y,
        family_name,
        fontsize=13,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        zorder=5,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#FAFAFA", "edgecolor": "none", "alpha": 0.85},
    )

# Guide line for constant E/rho (lightweight stiffness index)
guide_density = np.logspace(1, 5, 100)
for c_val, label_text in [(0.01, r"$E/\rho = 10$ kPa$\cdot$m$^3$/kg"), (1, r"$E/\rho = 1$ GPa$\cdot$m$^3$/Mg")]:
    guide_modulus = c_val * guide_density / 1000
    mask = (guide_modulus >= 5e-4) & (guide_modulus <= 600)
    ax.plot(
        guide_density[mask], guide_modulus[mask], color="#999999", linewidth=1.0, linestyle="--", alpha=0.5, zorder=1
    )
    valid_idx = np.where(mask)[0]
    if len(valid_idx) > 0:
        mid = valid_idx[len(valid_idx) // 3]
        ax.text(
            guide_density[mid],
            guide_modulus[mid] * 1.3,
            label_text,
            fontsize=10,
            color="#999999",
            rotation=28,
            ha="center",
            va="bottom",
        )

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(10, 30000)
ax.set_ylim(5e-4, 600)
ax.set_xlabel("Density (kg/m$^3$)", fontsize=20, color="#333333", labelpad=10)
ax.set_ylabel("Young's Modulus (GPa)", fontsize=20, color="#333333", labelpad=10)
ax.set_title(
    "scatter-ashby-material \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="bold",
    color="#222222",
    pad=16,
)
ax.tick_params(axis="both", labelsize=16, colors="#555555")

for spine in ax.spines.values():
    spine.set_visible(False)

ax.grid(True, which="major", alpha=0.2, linewidth=0.8, color="#CCCCCC", zorder=0)
ax.grid(True, which="minor", alpha=0.1, linewidth=0.5, color="#DDDDDD", zorder=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#FAFAFA")
