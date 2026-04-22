""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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

# Log-transform columns for seaborn KDE (works in linear space)
df["log_density"] = np.log10(df["density"])
df["log_modulus"] = np.log10(df["modulus"])

# Seaborn styling
sns.set_context("talk", font_scale=1.1)
sns.set_style("white")

# Colorblind-safe palette
palette = {
    "Metals": "#306998",
    "Polymers": "#E07A3A",
    "Ceramics": "#D94F4F",
    "Composites": "#2A9D8F",
    "Elastomers": "#9B6DB7",
    "Foams": "#C4A03C",
    "Natural Materials": "#6AADBD",
}

fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn's kdeplot to draw family envelopes — distinctive seaborn feature
# KDE operates in log-space, then we relabel axes to show original values
sns.kdeplot(
    data=df,
    x="log_density",
    y="log_modulus",
    hue="family",
    palette=palette,
    levels=2,
    thresh=0.3,
    fill=True,
    alpha=0.12,
    linewidths=0,
    ax=ax,
    legend=False,
    zorder=1,
    common_norm=False,
)

# Scatter using seaborn with hue and style mapping
sns.scatterplot(
    data=df,
    x="log_density",
    y="log_modulus",
    hue="family",
    palette=palette,
    style="family",
    s=80,
    alpha=0.7,
    edgecolor="white",
    linewidth=0.5,
    ax=ax,
    legend=False,
    zorder=3,
)

# Performance index guide lines (E/ρ = const) — characteristic of Ashby charts
log_d_range = np.linspace(np.log10(10), np.log10(20000), 200)
guide_indices = [(1e-3, "E/ρ = 0.001"), (1e-1, "E/ρ = 0.1"), (1e1, "E/ρ = 10")]
for ratio, label in guide_indices:
    log_m_line = np.log10(ratio) + log_d_range
    mask = (log_m_line >= np.log10(5e-4)) & (log_m_line <= np.log10(1000))
    ax.plot(log_d_range[mask], log_m_line[mask], color="#BBBBBB", linewidth=0.7, linestyle="--", alpha=0.45, zorder=0)
    vis_d = log_d_range[mask]
    vis_m = log_m_line[mask]
    if len(vis_d) > 10:
        idx = int(len(vis_d) * 0.12)
        ax.text(
            vis_d[idx],
            vis_m[idx] + 0.12,
            label,
            fontsize=10,
            color="#AAAAAA",
            fontstyle="italic",
            rotation=30,
            ha="center",
            va="bottom",
            zorder=0,
        )

# Highlight the lightweight-stiff "sweet spot" direction for data storytelling
ax.annotate(
    "Lightweight\n& Stiff ↗",
    xy=(np.log10(200), np.log10(80)),
    fontsize=12,
    fontstyle="italic",
    color="#666666",
    ha="center",
    va="center",
    zorder=4,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.7, "edgecolor": "#CCCCCC", "linewidth": 0.5},
)

# Family labels — offset positions to reduce crowding in upper-right
label_offsets = {
    "Metals": (0.3, 0.35),
    "Ceramics": (-0.4, 0.35),
    "Composites": (-0.35, -0.35),
    "Polymers": (0.2, 0.0),
    "Elastomers": (0.0, 0.0),
    "Foams": (0.0, 0.0),
    "Natural Materials": (-0.2, 0.2),
}

for family in df["family"].unique():
    subset = df[df["family"] == family]
    color = palette[family]

    centroid_log_d = subset["log_density"].mean()
    centroid_log_m = subset["log_modulus"].mean()

    offset = label_offsets.get(family, (0, 0))
    label_log_d = centroid_log_d + offset[0]
    label_log_m = centroid_log_m + offset[1]

    ax.annotate(
        family,
        xy=(centroid_log_d, centroid_log_m),
        xytext=(label_log_d, label_log_m),
        fontsize=14,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        zorder=5,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9, "edgecolor": color, "linewidth": 0.5},
        arrowprops={"arrowstyle": "-", "color": color, "alpha": 0.5, "linewidth": 0.8} if offset != (0, 0) else None,
    )

# Custom tick labels to show real density/modulus values on log-transformed axes
density_ticks = [10, 100, 1000, 10000]
modulus_ticks = [0.001, 0.01, 0.1, 1, 10, 100]
ax.set_xticks([np.log10(v) for v in density_ticks])
ax.set_xticklabels([str(v) for v in density_ticks])
ax.set_yticks([np.log10(v) for v in modulus_ticks])
ax.set_yticklabels([str(v) for v in modulus_ticks])

# Axis styling — y-axis only grid for cleaner look
ax.set_xlabel("Density (kg/m³)", fontsize=20)
ax.set_ylabel("Young's Modulus (GPa)", fontsize=20)
ax.set_title("scatter-ashby-material · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=15)
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.6, color="#CCCCCC")
ax.xaxis.grid(False)

sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
