""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-27
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Colorblind-safe palette via seaborn (teal replaces green to avoid red-green pair)
element_names = ["Stress State (A, B)", "Principal Stress (\u03c3\u2081, \u03c3\u2082)", "Max Shear (\u03c4max)"]
element_palette = dict(zip(element_names, sns.color_palette(["#C0392B", "#2CA5A5", "#E67E22"]), strict=True))
element_markers = {
    "Stress State (A, B)": "o",
    "Principal Stress (\u03c3\u2081, \u03c3\u2082)": "D",
    "Max Shear (\u03c4max)": "s",
}

# Data - stress state for a beam under combined loading
sigma_x = 80
sigma_y = -40
tau_xy = 30

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

# All key points in a single DataFrame for seaborn semantic mapping
points_df = pd.DataFrame(
    {
        "sigma": [sigma_x, sigma_y, sigma_1, sigma_2, center, center],
        "tau": [tau_xy, -tau_xy, 0, 0, tau_max, -tau_max],
        "Element": [
            "Stress State (A, B)",
            "Stress State (A, B)",
            "Principal Stress (\u03c3\u2081, \u03c3\u2082)",
            "Principal Stress (\u03c3\u2081, \u03c3\u2082)",
            "Max Shear (\u03c4max)",
            "Max Shear (\u03c4max)",
        ],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# Mohr's circle with subtle fill
ax.plot(circle_sigma, circle_tau, color="#306998", linewidth=3, zorder=3)
ax.fill(circle_sigma, circle_tau, color="#306998", alpha=0.04, zorder=1)

# Reference lines through center
ax.axhline(y=0, color="#555555", linewidth=1.2, zorder=2)
ax.axvline(x=center, color="#aaaaaa", linewidth=1, linestyle="--", alpha=0.5, zorder=2)

# Diameter line connecting A and B
ax.plot([sigma_x, sigma_y], [tau_xy, -tau_xy], color="#C0392B", linewidth=1.8, linestyle="--", alpha=0.5, zorder=3)

# All categorized points via seaborn scatterplot with hue + style semantic mapping
sns.scatterplot(
    data=points_df,
    x="sigma",
    y="tau",
    hue="Element",
    style="Element",
    markers=element_markers,
    palette=element_palette,
    s=300,
    edgecolor="white",
    linewidth=2,
    zorder=5,
    ax=ax,
    legend=False,
)

# Center point
ax.scatter([center], [0], s=180, color="#306998", edgecolors="white", linewidth=2, zorder=5)

# --- Annotations with graduated visual hierarchy ---

# Input stress state info (data storytelling context)
info_text = f"\u03c3x = {sigma_x} MPa\n\u03c3y = {sigma_y} MPa\n\u03c4xy = {tau_xy} MPa"
ax.text(
    0.98,
    0.98,
    info_text,
    transform=ax.transAxes,
    fontsize=13,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f8f9fa", "edgecolor": "#cccccc", "alpha": 0.85},
    family="monospace",
    linespacing=1.5,
)

# Center label (tertiary emphasis)
ax.annotate(
    f"C ({center:.0f}, 0)",
    xy=(center, 0),
    xytext=(center - 8, -radius * 0.28),
    fontsize=13,
    color="#306998",
    ha="right",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.2},
    zorder=6,
)

# Stress point A (secondary emphasis)
ax.annotate(
    f"A ({sigma_x}, {tau_xy})",
    xy=(sigma_x, tau_xy),
    xytext=(sigma_x + 12, tau_xy + 22),
    fontsize=15,
    fontweight="bold",
    color="#C0392B",
    ha="left",
    arrowprops={"arrowstyle": "->", "color": "#C0392B", "lw": 1.5},
    zorder=6,
)

# Stress point B (secondary emphasis)
ax.annotate(
    f"B ({sigma_y}, {-tau_xy})",
    xy=(sigma_y, -tau_xy),
    xytext=(sigma_y + 18, -tau_xy - 20),
    fontsize=15,
    fontweight="bold",
    color="#C0392B",
    ha="left",
    arrowprops={"arrowstyle": "->", "color": "#C0392B", "lw": 1.5},
    zorder=6,
)

# Principal stresses (PRIMARY emphasis - boxed, larger font, prominent arrows)
ax.annotate(
    f"\u03c3\u2081 = {sigma_1:.1f} MPa",
    xy=(sigma_1, 0),
    xytext=(center + radius * 0.45, -radius * 0.48),
    fontsize=16,
    fontweight="bold",
    color="#2CA5A5",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#2CA5A5", "lw": 2, "mutation_scale": 15},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#2CA5A5", "alpha": 0.85},
    zorder=6,
)

ax.annotate(
    f"\u03c3\u2082 = {sigma_2:.1f} MPa",
    xy=(sigma_2, 0),
    xytext=(center - radius * 0.45, -radius * 0.48),
    fontsize=16,
    fontweight="bold",
    color="#2CA5A5",
    ha="center",
    arrowprops={"arrowstyle": "-|>", "color": "#2CA5A5", "lw": 2, "mutation_scale": 15},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#2CA5A5", "alpha": 0.85},
    zorder=6,
)

# Max shear stress (secondary emphasis)
ax.annotate(
    f"\u03c4max = {tau_max:.1f} MPa",
    xy=(center, tau_max),
    xytext=(center + radius * 0.6, tau_max + 8),
    fontsize=14,
    fontweight="bold",
    color="#E67E22",
    arrowprops={"arrowstyle": "->", "color": "#E67E22", "lw": 1.5},
    zorder=6,
)

# 2θp angle arc
arc_angles = np.linspace(0, np.radians(two_theta_p), 50)
arc_r = radius * 0.3
arc_x = center + arc_r * np.cos(arc_angles)
arc_y = arc_r * np.sin(arc_angles)
ax.plot(arc_x, arc_y, color="#8E44AD", linewidth=2.5, zorder=4)

mid_angle = np.radians(two_theta_p / 2)
ax.text(
    center + arc_r * 1.45 * np.cos(mid_angle),
    arc_r * 1.45 * np.sin(mid_angle),
    f"2\u03b8p = {two_theta_p:.1f}\u00b0",
    fontsize=14,
    fontweight="bold",
    color="#8E44AD",
    ha="left",
    va="bottom",
)

# Legend
legend_handles = [
    Line2D([0], [0], color="#306998", linewidth=3, label="Mohr's Circle"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#C0392B",
        markersize=12,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Stress State (A, B)",
    ),
    Line2D(
        [0],
        [0],
        marker="D",
        color="w",
        markerfacecolor="#2CA5A5",
        markersize=12,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Principal Stress (\u03c3\u2081, \u03c3\u2082)",
    ),
    Line2D(
        [0],
        [0],
        marker="s",
        color="w",
        markerfacecolor="#E67E22",
        markersize=12,
        markeredgecolor="white",
        markeredgewidth=1.5,
        label="Max Shear (\u03c4max)",
    ),
    Line2D([0], [0], color="#8E44AD", linewidth=2.5, label="Principal Angle (2\u03b8p)"),
]
ax.legend(handles=legend_handles, fontsize=14, loc="lower left", framealpha=0.9, edgecolor="#cccccc")

# Axis labels and title
ax.set_xlabel("Normal Stress \u03c3 (MPa)", fontsize=20)
ax.set_ylabel("Shear Stress \u03c4 (MPa)", fontsize=20)
ax.set_title("mohr-circle \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")

# Seaborn visual refinement: despine + y-axis only grid
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.xaxis.grid(False)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", pad_inches=0.2)
