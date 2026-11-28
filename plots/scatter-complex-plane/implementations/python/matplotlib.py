"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-28
"""

import sys


sys.path.pop(0)  # prevent this file from shadowing the matplotlib package

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Arc


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REAL = "Real axis"  # role: real
IMAGINARY = "Imaginary axis"  # role: imaginary
LABEL = "Point"  # role: label
CATEGORY = "Category"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
n_roots = 5
roots = np.exp(2j * np.pi * np.arange(n_roots) / n_roots)
arbitrary = np.array([1.6 + 0.7j, -0.4 + 1.5j])
z_all = np.concatenate([roots, arbitrary])
df = pd.DataFrame(
    {
        REAL: z_all.real,
        IMAGINARY: z_all.imag,
        LABEL: ["1", "ω", "ω²", "ω³", "ω⁴", "z₁", "z₂"],
        CATEGORY: ["5th roots of unity (ω = e^(2πi/5))"] * n_roots + ["Arbitrary complex numbers"] * len(arbitrary),
    }
)

# Plot — square canvas required so the unit circle appears circular
groups = list(dict.fromkeys(df[CATEGORY]))
marker_cycle = ["o", "D", "s", "^", "v", "P", "X", "*"]
group_color = {g: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, g in enumerate(groups)}
group_marker = {g: marker_cycle[i % len(marker_cycle)] for i, g in enumerate(groups)}
all_points = df[REAL].to_numpy() + 1j * df[IMAGINARY].to_numpy()
all_colors = [group_color[g] for g in df[CATEGORY]]
all_markers = [group_marker[g] for g in df[CATEGORY]]
all_labels = df[LABEL].tolist()
extent = max(df[REAL].abs().max(), df[IMAGINARY].abs().max(), 1.0) * 1.5

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Unit circle — dashed geometric reference
theta = np.linspace(0, 2 * np.pi, 400)
ax.plot(np.cos(theta), np.sin(theta), color=INK_MUTED, linewidth=1.5, linestyle="--", alpha=0.7, zorder=1)

# Real and imaginary axes through the origin
ax.axhline(0, color=INK_SOFT, linewidth=0.9, alpha=0.6, zorder=1)
ax.axvline(0, color=INK_SOFT, linewidth=0.9, alpha=0.6, zorder=1)

# Subtle grid for both axes
ax.xaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK, zorder=0)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK, zorder=0)

# Arrows from origin to each complex number
for z, color in zip(all_points, all_colors, strict=False):
    ax.annotate(
        "",
        xy=(z.real, z.imag),
        xytext=(0.0, 0.0),
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8, "mutation_scale": 18, "shrinkA": 0, "shrinkB": 7},
        zorder=3,
    )

# Angle arcs — dotted arcs from positive real axis to each vector, showing the argument
for z, color in zip(all_points, all_colors, strict=False):
    angle_deg = np.degrees(np.angle(z))  # in [-180, 180]
    if abs(angle_deg) > 0.5:
        arc = Arc(
            (0, 0),
            0.38,
            0.38,
            angle=0,
            theta1=min(0.0, angle_deg),
            theta2=max(0.0, angle_deg),
            color=color,
            linewidth=0.9,
            linestyle=":",
            alpha=0.45,
            zorder=2,
        )
        ax.add_patch(arc)

# Scatter points
for z, color, marker in zip(all_points, all_colors, all_markers, strict=False):
    ax.scatter(z.real, z.imag, s=130, color=color, marker=marker, edgecolors=PAGE_BG, linewidth=1.2, zorder=5)

# Labels — name, rectangular form (a+bi), and polar form (|z|∠θ°), offset outward from origin
for z, label in zip(all_points, all_labels, strict=False):
    re, im = z.real, z.imag
    mag = abs(z) + 1e-12
    angle_deg = np.degrees(np.angle(z)) % 360

    if abs(im) < 1e-10:
        coord = f"{re:.2f}"
    elif im >= 0:
        coord = f"{re:.2f}+{im:.2f}i"
    else:
        coord = f"{re:.2f}{im:.2f}i"

    polar = f"{abs(z):.2f}∠{angle_deg:.1f}°"

    ux, uy = re / mag, im / mag
    ha = "left" if ux > 0.35 else "right" if ux < -0.35 else "center"
    va = "bottom" if uy > 0.35 else "top" if uy < -0.35 else "center"

    ax.annotate(
        f"{label}\n{coord}\n{polar}",
        xy=(re, im),
        xytext=(ux * 14, uy * 14),
        textcoords="offset points",
        fontsize=9,
        color=INK,
        ha=ha,
        va=va,
        bbox={"facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.88, "pad": 3},
        zorder=6,
    )

# Style
title = "scatter-complex-plane · python · matplotlib · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(REAL, fontsize=10, color=INK)
ax.set_ylabel(IMAGINARY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_xlim(-extent, extent)
ax.set_ylim(-extent, extent)

# Legend
legend_elements = [
    Line2D(
        [0],
        [0],
        marker=group_marker[g],
        linestyle="none",
        markerfacecolor=group_color[g],
        markeredgecolor=PAGE_BG,
        markersize=9,
        label=g,
    )
    for g in groups
] + [Line2D([0], [0], color=INK_MUTED, linewidth=1.5, linestyle="--", label="Unit circle  |z| = 1")]
leg = ax.legend(handles=legend_elements, fontsize=8, loc="lower left", framealpha=0.9)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
