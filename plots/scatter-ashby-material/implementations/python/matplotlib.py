""" anyplot.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-03
"""

import os

import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import ConvexHull


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — Density (kg/m³) vs Young's Modulus (GPa) for engineering materials
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

family_names = list(families.keys())
family_colors = {name: IMPRINT_PALETTE[i] for i, name in enumerate(family_names)}

# Label offsets (log10 coords) to reduce upper-right crowding
label_offsets = {"Metals": (0.30, -0.35), "Ceramics": (-0.25, 0.22), "Composites": (-0.30, -0.15)}

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for family_name, data in families.items():
    density = np.array(data["density"], dtype=float)
    modulus = np.array(data["modulus"], dtype=float)
    color = family_colors[family_name]

    ax.scatter(density, modulus, s=80, alpha=0.7, color=color, edgecolors=PAGE_BG, linewidth=0.5, zorder=4)

    # Smooth Bezier convex hull envelope using matplotlib Path/PathPatch
    log_pts = np.column_stack([np.log10(density), np.log10(modulus)])
    rng = np.random.RandomState(hash(family_name) % 2**31)
    log_pts_jittered = log_pts + rng.randn(*log_pts.shape) * 0.01

    try:
        hull = ConvexHull(log_pts_jittered)
        hull_verts = np.vstack([log_pts_jittered[hull.vertices], log_pts_jittered[hull.vertices[0]]])
        centroid = np.mean(hull_verts[:-1], axis=0)
        directions = hull_verts - centroid
        norms = np.linalg.norm(directions, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        hull_verts = hull_verts + directions / norms * 0.08
        n_verts = len(hull_verts) - 1
        codes = [mpath.Path.MOVETO]
        pts = [hull_verts[0]]
        for i in range(n_verts):
            p0, p1 = hull_verts[i], hull_verts[(i + 1) % n_verts]
            pts.extend([p0 + (p1 - p0) * 0.33, p0 + (p1 - p0) * 0.67, p1])
            codes.extend([mpath.Path.CURVE4, mpath.Path.CURVE4, mpath.Path.CURVE4])
        codes.append(mpath.Path.CLOSEPOLY)
        pts.append(pts[0])
        pts_arr = np.array(pts)
        pts_data = np.column_stack([10 ** pts_arr[:, 0], 10 ** pts_arr[:, 1]])
        path = mpath.Path(pts_data, codes)
        ax.add_patch(mpatches.PathPatch(path, facecolor=color, edgecolor="none", alpha=0.15, zorder=2))
        ax.add_patch(mpatches.PathPatch(path, facecolor="none", edgecolor=color, alpha=0.5, linewidth=1.2, zorder=3))
    except Exception:
        pass

    # Family label at geometric center with optional offset to reduce crowding
    cx_log = np.mean(np.log10(density))
    cy_log = np.mean(np.log10(modulus))
    dx, dy = label_offsets.get(family_name, (0, 0))
    ax.text(
        10 ** (cx_log + dx),
        10 ** (cy_log + dy),
        family_name,
        fontsize=8,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        zorder=5,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
    )

# Guide lines for constant E/rho (lightweight stiffness index)
guide_density = np.logspace(1, 5, 100)
for c_val, label_text in [(0.01, r"$E/\rho = 10$ kPa$\cdot$m$^3$/kg"), (1.0, r"$E/\rho = 1$ GPa$\cdot$m$^3$/Mg")]:
    guide_modulus = c_val * guide_density / 1000
    mask = (guide_modulus >= 5e-4) & (guide_modulus <= 600)
    ax.plot(
        guide_density[mask], guide_modulus[mask], color=INK_MUTED, linewidth=0.8, linestyle="--", alpha=0.6, zorder=1
    )
    valid_idx = np.where(mask)[0]
    if len(valid_idx) > 0:
        mid = valid_idx[len(valid_idx) // 3]
        ax.text(
            guide_density[mid],
            guide_modulus[mid] * 1.5,
            label_text,
            fontsize=7,
            color=INK_MUTED,
            rotation=30,
            ha="center",
            va="bottom",
        )

# Style
title = "scatter-ashby-material · python · matplotlib · anyplot.ai"
title_len = len(title)
title_fs = max(8, round(12 * 67 / title_len)) if title_len > 67 else 12

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(10, 30000)
ax.set_ylim(5e-4, 600)
ax.set_xlabel("Density (kg/m$^3$)", fontsize=10, color=INK, labelpad=6)
ax.set_ylabel("Young's Modulus (GPa)", fontsize=10, color=INK, labelpad=6)
ax.set_title(title, fontsize=title_fs, fontweight="medium", color=INK, pad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.grid(True, which="major", alpha=0.15, linewidth=0.6, color=INK, zorder=0)
ax.grid(True, which="minor", alpha=0.08, linewidth=0.4, color=INK, zorder=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
