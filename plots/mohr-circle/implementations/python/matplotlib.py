""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-27
"""

import matplotlib.patches as patches
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np


# Colors — semantic palette (colorblind-safe: blue/red-orange/amber)
CLR_GEOM = "#306998"  # Blue — geometry (circle, center, angle)
CLR_INPUT = "#C1440E"  # Red-orange — input stress state (A, B)
CLR_DERIVED = "#D4A017"  # Amber — derived quantities (σ₁, σ₂, τ_max)

# Data — stress state for a steel beam under combined loading
sigma_x = 80  # Normal stress in x-direction (MPa)
sigma_y = -40  # Normal stress in y-direction (MPa)
tau_xy = 30  # Shear stress on xy-plane (MPa)

# Mohr's circle parameters
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
theta_2p = np.degrees(np.arctan2(tau_xy, sigma_x - center))

# Circle coordinates
theta = np.linspace(0, 2 * np.pi, 360)
circle_sigma = center + radius * np.cos(theta)
circle_tau = radius * np.sin(theta)

# Arrow style for annotations
arrow_kw = {"arrowstyle": "-|>", "mutation_scale": 14, "lw": 1.5}

# Plot
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")

# Axis limits with padding for annotations
pad = radius * 0.5
ax.set_xlim(sigma_2 - pad, sigma_1 + pad)
ax.set_ylim(-tau_max - pad, tau_max + pad)

# Subtle circle fill for visual richness
circle_fill = patches.Circle((center, 0), radius, facecolor=CLR_GEOM, alpha=0.04, edgecolor="none", zorder=1)
ax.add_patch(circle_fill)

# Mohr's circle outline
ax.plot(circle_sigma, circle_tau, color=CLR_GEOM, linewidth=3, zorder=3)

# Reference lines through center
ax.axhline(y=0, color="#555555", linewidth=1, zorder=1)
ax.axvline(x=center, color="#555555", linewidth=1, linestyle="--", alpha=0.4, zorder=1)

# Line connecting stress points A and B
ax.plot([sigma_x, sigma_y], [tau_xy, -tau_xy], color=CLR_INPUT, linewidth=1.5, linestyle="--", alpha=0.5, zorder=2)

# Stress points A(σx, τxy) and B(σy, −τxy)
ax.scatter([sigma_x, sigma_y], [tau_xy, -tau_xy], color=CLR_INPUT, s=200, edgecolors="white", linewidth=1.5, zorder=5)
ax.annotate(
    f"A ({sigma_x}, {tau_xy})",
    xy=(sigma_x, tau_xy),
    xytext=(sigma_x + 12, tau_xy + 16),
    fontsize=16,
    color=CLR_INPUT,
    fontweight="bold",
    arrowprops={**arrow_kw, "color": CLR_INPUT},
)
ax.annotate(
    f"B ({sigma_y}, {-tau_xy})",
    xy=(sigma_y, -tau_xy),
    xytext=(sigma_y - 12, -tau_xy - 16),
    fontsize=16,
    color=CLR_INPUT,
    fontweight="bold",
    ha="right",
    arrowprops={**arrow_kw, "color": CLR_INPUT},
)

# Principal stresses σ₁ and σ₂
ax.scatter(
    [sigma_1, sigma_2], [0, 0], color=CLR_DERIVED, s=220, edgecolors="white", linewidth=1.5, zorder=5, marker="D"
)
ax.annotate(
    f"σ₁ = {sigma_1:.1f} MPa",
    xy=(sigma_1, 0),
    xytext=(sigma_1 + 5, -16),
    fontsize=16,
    color=CLR_DERIVED,
    fontweight="bold",
)
ax.annotate(
    f"σ₂ = {sigma_2:.1f} MPa",
    xy=(sigma_2, 0),
    xytext=(sigma_2 - 5, 12),
    fontsize=16,
    color=CLR_DERIVED,
    fontweight="bold",
    ha="right",
)

# Maximum shear stress τ_max at top and bottom
ax.scatter(
    [center, center],
    [tau_max, -tau_max],
    color=CLR_DERIVED,
    s=220,
    edgecolors="white",
    linewidth=1.5,
    zorder=5,
    marker="D",
)
ax.annotate(
    f"τ_max = {tau_max:.1f} MPa",
    xy=(center, tau_max),
    xytext=(center + 18, tau_max + 12),
    fontsize=16,
    color=CLR_DERIVED,
    fontweight="bold",
    arrowprops={**arrow_kw, "color": CLR_DERIVED},
)
ax.annotate(
    f"−τ_max = −{tau_max:.1f} MPa",
    xy=(center, -tau_max),
    xytext=(center + 18, -tau_max - 12),
    fontsize=16,
    color=CLR_DERIVED,
    fontweight="bold",
    arrowprops={**arrow_kw, "color": CLR_DERIVED},
)

# Principal angle 2θp arc
arc_radius = radius * 0.35
arc = patches.Arc(
    (center, 0),
    2 * arc_radius,
    2 * arc_radius,
    angle=0,
    theta1=0,
    theta2=theta_2p,
    color=CLR_GEOM,
    linewidth=2.5,
    zorder=4,
)
ax.add_patch(arc)

# Small arrowhead at arc tip
arc_tip_angle = np.radians(theta_2p)
ax.annotate(
    "",
    xy=(center + arc_radius * np.cos(arc_tip_angle), arc_radius * np.sin(arc_tip_angle)),
    xytext=(center + arc_radius * np.cos(arc_tip_angle - 0.08), arc_radius * np.sin(arc_tip_angle - 0.08)),
    arrowprops={"arrowstyle": "-|>", "color": CLR_GEOM, "lw": 2, "mutation_scale": 16},
    zorder=4,
)

arc_mid = np.radians(theta_2p / 2)
ax.annotate(
    f"2θp = {theta_2p:.1f}°",
    xy=(center + arc_radius * np.cos(arc_mid), arc_radius * np.sin(arc_mid)),
    xytext=(center + arc_radius * 1.8, arc_radius * 2.8),
    fontsize=16,
    color=CLR_GEOM,
    fontweight="bold",
    arrowprops={**arrow_kw, "color": CLR_GEOM},
)

# Center marker — positioned to avoid crowding with 2θp annotation
ax.plot(center, 0, marker="+", color=CLR_GEOM, markersize=15, markeredgewidth=2.5, zorder=5)
center_txt = ax.annotate(
    f"C ({center:.0f}, 0)",
    xy=(center, 0),
    xytext=(center - 8, -16),
    fontsize=16,
    color=CLR_GEOM,
    ha="right",
    fontweight="bold",
)
center_txt.set_path_effects([patheffects.withStroke(linewidth=3, foreground="white"), patheffects.Normal()])

# Style
ax.set_xlabel("Normal Stress σ (MPa)", fontsize=20)
ax.set_ylabel("Shear Stress τ (MPa)", fontsize=20)
ax.set_title("mohr-circle · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.15, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
