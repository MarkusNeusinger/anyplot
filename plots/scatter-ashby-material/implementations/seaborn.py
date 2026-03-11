""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.spatial import ConvexHull


# Data — density (kg/m³) vs Young's modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {
        "density": (2700, 8900),
        "modulus": (45, 400),
        "n": 25,
        "materials": [
            (2700, 70),
            (4500, 115),
            (7800, 200),
            (7200, 210),
            (8900, 130),
            (8500, 120),
            (7900, 193),
            (4400, 110),
            (2800, 73),
            (7100, 195),
        ],
    },
    "Polymers": {
        "density": (900, 1500),
        "modulus": (0.2, 4.0),
        "n": 20,
        "materials": [
            (950, 0.8),
            (1050, 2.5),
            (1200, 3.0),
            (1400, 3.5),
            (1140, 2.4),
            (900, 1.3),
            (1300, 2.8),
            (1070, 2.0),
        ],
    },
    "Ceramics": {
        "density": (2200, 6000),
        "modulus": (70, 450),
        "n": 18,
        "materials": [
            (3980, 380),
            (2200, 70),
            (3200, 310),
            (5700, 200),
            (2500, 90),
            (3900, 350),
            (5000, 170),
            (2650, 95),
        ],
    },
    "Composites": {
        "density": (1400, 2200),
        "modulus": (15, 200),
        "n": 15,
        "materials": [
            (1600, 140),
            (1900, 45),
            (1500, 180),
            (2000, 30),
            (1550, 70),
            (1800, 50),
            (1450, 120),
            (1700, 60),
        ],
    },
    "Elastomers": {
        "density": (900, 1300),
        "modulus": (0.002, 0.1),
        "n": 12,
        "materials": [
            (920, 0.005),
            (1100, 0.01),
            (1200, 0.05),
            (1000, 0.003),
            (1050, 0.02),
            (960, 0.008),
            (1150, 0.04),
            (1250, 0.08),
        ],
    },
    "Foams": {
        "density": (25, 300),
        "modulus": (0.001, 0.3),
        "n": 14,
        "materials": [
            (30, 0.001),
            (60, 0.01),
            (120, 0.05),
            (200, 0.2),
            (50, 0.005),
            (100, 0.03),
            (250, 0.25),
            (150, 0.08),
        ],
    },
    "Natural Materials": {
        "density": (150, 1300),
        "modulus": (0.1, 20),
        "n": 12,
        "materials": [(500, 12), (700, 14), (400, 8), (200, 1.0), (600, 10), (1200, 18), (350, 5), (800, 15)],
    },
}

rows = []
for family, props in families.items():
    for d, m in props["materials"]:
        rows.append({"family": family, "density": d, "modulus": m})
    extra_n = props["n"] - len(props["materials"])
    if extra_n > 0:
        log_d_min, log_d_max = np.log10(props["density"][0]), np.log10(props["density"][1])
        log_m_min, log_m_max = np.log10(props["modulus"][0]), np.log10(props["modulus"][1])
        extra_d = 10 ** np.random.uniform(log_d_min, log_d_max, extra_n)
        extra_m = 10 ** np.random.uniform(log_m_min, log_m_max, extra_n)
        for d, m in zip(extra_d, extra_m, strict=True):
            rows.append({"family": family, "density": d, "modulus": m})

df = pd.DataFrame(rows)

# Plot
palette = {
    "Metals": "#306998",
    "Polymers": "#E07A3A",
    "Ceramics": "#D94F4F",
    "Composites": "#5BA065",
    "Elastomers": "#9B6DB7",
    "Foams": "#C4A03C",
    "Natural Materials": "#6AADBD",
}

fig, ax = plt.subplots(figsize=(16, 9))

# Draw convex hull envelopes for each family
for family in df["family"].unique():
    subset = df[df["family"] == family]
    log_d = np.log10(subset["density"].values)
    log_m = np.log10(subset["modulus"].values)
    color = palette[family]

    if len(subset) >= 3:
        points = np.column_stack([log_d, log_m])
        try:
            hull = ConvexHull(points)
            hull_pts = points[hull.vertices]
            hull_pts = np.vstack([hull_pts, hull_pts[0]])
            ax.fill(10 ** hull_pts[:, 0], 10 ** hull_pts[:, 1], alpha=0.15, color=color, zorder=1)
            ax.plot(10 ** hull_pts[:, 0], 10 ** hull_pts[:, 1], color=color, alpha=0.4, linewidth=1.5, zorder=2)
        except Exception:
            pass

    centroid_d = 10 ** np.mean(log_d)
    centroid_m = 10 ** np.mean(log_m)
    ax.text(
        centroid_d,
        centroid_m,
        family,
        fontsize=13,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        zorder=5,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.7, "edgecolor": "none"},
    )

sns.scatterplot(
    data=df,
    x="density",
    y="modulus",
    hue="family",
    palette=palette,
    s=120,
    alpha=0.8,
    edgecolor="white",
    linewidth=0.5,
    ax=ax,
    legend=False,
    zorder=3,
)

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Density (kg/m³)", fontsize=20)
ax.set_ylabel("Young's Modulus (GPa)", fontsize=20)
ax.set_title("scatter-ashby-material · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, which="major", alpha=0.15, linewidth=0.8)
ax.grid(True, which="minor", alpha=0.08, linewidth=0.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
