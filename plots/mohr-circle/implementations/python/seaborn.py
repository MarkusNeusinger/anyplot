""" anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_CIRCLE = IMPRINT_PALETTE[0]  # brand green — Mohr's circle boundary
COLOR_STATE = IMPRINT_PALETTE[1]  # lavender — stress state points A, B
COLOR_SIGMA = IMPRINT_PALETTE[2]  # blue — principal stresses σ₁, σ₂
COLOR_SHEAR = IMPRINT_PALETTE[3]  # ochre — max shear τmax
COLOR_ANGLE = IMPRINT_PALETTE[4]  # matte red — principal angle 2θp arc

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
STATE_LABEL = "Stress State (A, B)"
PRINCIPAL_LABEL = "Principal Stress (σ₁, σ₂)"
SHEAR_LABEL = "Max Shear (τmax)"
ELEMENT_MARKERS = {STATE_LABEL: "o", PRINCIPAL_LABEL: "D", SHEAR_LABEL: "s"}
ELEMENT_COLORS = {STATE_LABEL: COLOR_STATE, PRINCIPAL_LABEL: COLOR_SIGMA, SHEAR_LABEL: COLOR_SHEAR}

# Column constants
SIGMA_X = "σx (MPa)"  # role: sigma_x
SIGMA_Y = "σy (MPa)"  # role: sigma_y
TAU_XY = "τxy (MPa)"  # role: tau_xy
NORMAL = "Normal Stress σ (MPa)"  # role: extra
SHEAR = "Shear Stress τ (MPa)"  # role: extra
ELEMENT = "Element"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("stress.csv")
# Stress state for a shaft under combined torsion and bending
df = pd.DataFrame({SIGMA_X: [70], SIGMA_Y: [-50], TAU_XY: [35]})

# Plot
sigma_x = df[SIGMA_X].iloc[0]
sigma_y = df[SIGMA_Y].iloc[0]
tau_xy = df[TAU_XY].iloc[0]

# Mohr's circle parameters
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
two_theta_p = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Circle coordinates
theta = np.linspace(0, 2 * np.pi, 360)
circle_sigma = center + radius * np.cos(theta)
circle_tau = radius * np.sin(theta)

# Key points table for seaborn semantic mapping
points_df = pd.DataFrame(
    {
        NORMAL: [sigma_x, sigma_y, sigma_1, sigma_2, center, center],
        SHEAR: [tau_xy, -tau_xy, 0, 0, tau_max, -tau_max],
        ELEMENT: [STATE_LABEL, STATE_LABEL, PRINCIPAL_LABEL, PRINCIPAL_LABEL, SHEAR_LABEL, SHEAR_LABEL],
    }
)

# Figure — square canvas for equal-aspect Mohr's circle (2400×2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Mohr's circle with subtle fill
ax.plot(circle_sigma, circle_tau, color=COLOR_CIRCLE, linewidth=2.5, zorder=3)
ax.fill(circle_sigma, circle_tau, color=COLOR_CIRCLE, alpha=0.05, zorder=1)

# Reference lines through center
ax.axhline(y=0, color=INK_SOFT, linewidth=1.0, zorder=2)
ax.axvline(x=center, color=INK_MUTED, linewidth=0.8, linestyle="--", alpha=0.6, zorder=2)

# Diameter line connecting A and B
ax.plot([sigma_x, sigma_y], [tau_xy, -tau_xy], color=COLOR_STATE, linewidth=1.5, linestyle="--", alpha=0.5, zorder=3)

# Key points via seaborn scatterplot with hue + style semantic mapping
sns.scatterplot(
    data=points_df,
    x=NORMAL,
    y=SHEAR,
    hue=ELEMENT,
    style=ELEMENT,
    markers=ELEMENT_MARKERS,
    palette=ELEMENT_COLORS,
    s=220,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    zorder=5,
    ax=ax,
    legend=False,
)

# Center point
ax.scatter([center], [0], s=100, color=INK_SOFT, edgecolors=PAGE_BG, linewidth=1.5, zorder=5)

# Annotations — graduated visual hierarchy matching the spec requirements

# Input stress state info box (tertiary — small, monospace)
info_text = f"σx = {sigma_x} MPa\nσy = {sigma_y} MPa\nτxy = {tau_xy} MPa"
ax.text(
    0.98,
    0.98,
    info_text,
    transform=ax.transAxes,
    fontsize=8,
    verticalalignment="top",
    horizontalalignment="right",
    family="monospace",
    color=INK_SOFT,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_MUTED, "alpha": 0.9},
    linespacing=1.5,
)

# Center label (tertiary)
ax.annotate(
    f"C ({center:.0f}, 0)",
    xy=(center, 0),
    xytext=(center - 6, -radius * 0.26),
    fontsize=8,
    color=INK_SOFT,
    ha="right",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.0},
    zorder=6,
)

# Stress point A (secondary)
ax.annotate(
    f"A ({sigma_x}, {tau_xy})",
    xy=(sigma_x, tau_xy),
    xytext=(sigma_x + 10, tau_xy + 18),
    fontsize=8,
    fontweight="bold",
    color=COLOR_STATE,
    ha="left",
    arrowprops={"arrowstyle": "->", "color": COLOR_STATE, "lw": 1.3},
    zorder=6,
)

# Stress point B (secondary)
ax.annotate(
    f"B ({sigma_y}, {-tau_xy})",
    xy=(sigma_y, -tau_xy),
    xytext=(sigma_y - 6, -tau_xy - 14),
    fontsize=8,
    fontweight="bold",
    color=COLOR_STATE,
    ha="right",
    arrowprops={"arrowstyle": "->", "color": COLOR_STATE, "lw": 1.3},
    zorder=6,
)

# Principal stresses (primary — boxed, bold, prominent arrows)
ax.annotate(
    f"σ₁ = {sigma_1:.1f} MPa",
    xy=(sigma_1, 0),
    xytext=(center + radius * 0.42, -radius * 0.46),
    fontsize=8,
    fontweight="bold",
    color=COLOR_SIGMA,
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": COLOR_SIGMA, "lw": 1.5, "mutation_scale": 12},
    bbox={"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": COLOR_SIGMA, "alpha": 0.92},
    zorder=6,
)

ax.annotate(
    f"σ₂ = {sigma_2:.1f} MPa",
    xy=(sigma_2, 0),
    xytext=(center - radius * 0.42, -radius * 0.46),
    fontsize=8,
    fontweight="bold",
    color=COLOR_SIGMA,
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": COLOR_SIGMA, "lw": 1.5, "mutation_scale": 12},
    bbox={"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": COLOR_SIGMA, "alpha": 0.92},
    zorder=6,
)

# Max shear stress (secondary)
ax.annotate(
    f"τmax = {tau_max:.1f} MPa",
    xy=(center, tau_max),
    xytext=(center - radius * 0.3, tau_max + 12),
    ha="right",
    fontsize=8,
    fontweight="bold",
    color=COLOR_SHEAR,
    arrowprops={"arrowstyle": "->", "color": COLOR_SHEAR, "lw": 1.3},
    zorder=6,
)

# 2θp angle arc (from positive x-axis to the stress state point A direction)
arc_angles = np.linspace(0, np.radians(two_theta_p), 50)
arc_r = radius * 0.3
arc_x = center + arc_r * np.cos(arc_angles)
arc_y = arc_r * np.sin(arc_angles)
ax.plot(arc_x, arc_y, color=COLOR_ANGLE, linewidth=2.0, zorder=4)

mid_angle = np.radians(two_theta_p / 2)
ax.text(
    center + arc_r * 1.5 * np.cos(mid_angle),
    arc_r * 1.5 * np.sin(mid_angle),
    f"2θp = {two_theta_p:.1f}°",
    fontsize=8,
    fontweight="bold",
    color=COLOR_ANGLE,
    ha="left",
    va="bottom",
)

# Legend
legend_handles = [
    Line2D([0], [0], color=COLOR_CIRCLE, linewidth=2.5, label="Mohr's Circle"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=COLOR_STATE,
        markersize=8,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.2,
        label=STATE_LABEL,
    ),
    Line2D(
        [0],
        [0],
        marker="D",
        color="none",
        markerfacecolor=COLOR_SIGMA,
        markersize=8,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.2,
        label=PRINCIPAL_LABEL,
    ),
    Line2D(
        [0],
        [0],
        marker="s",
        color="none",
        markerfacecolor=COLOR_SHEAR,
        markersize=8,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.2,
        label=SHEAR_LABEL,
    ),
    Line2D([0], [0], color=COLOR_ANGLE, linewidth=2.0, label="Principal Angle (2θp)"),
]
ax.legend(
    handles=legend_handles,
    fontsize=8,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.1),
    ncol=3,
    framealpha=0.9,
    edgecolor=INK_SOFT,
)

# Style
title = "mohr-circle · python · seaborn · anyplot.ai"
ax.set_xlabel(NORMAL, fontsize=10, color=INK)
ax.set_ylabel(SHEAR, fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_aspect("equal")
ax.set_xlim(center - radius * 1.4, center + radius * 1.4)
ax.set_ylim(-radius * 1.2, radius * 1.2)

# Grid — both axes for this engineering coordinate diagram
ax.yaxis.grid(True, alpha=0.12, linewidth=0.7, color=INK)
ax.xaxis.grid(True, alpha=0.12, linewidth=0.7, color=INK)
sns.despine(ax=ax)

plt.tight_layout()
# Save — no bbox_inches to preserve exact 2400×2400 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
