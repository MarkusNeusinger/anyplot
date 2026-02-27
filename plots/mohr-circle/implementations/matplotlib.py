"""pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-02-27
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


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

# Plot
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")

# Axis limits with padding for annotations
pad = radius * 0.45
ax.set_xlim(sigma_2 - pad, sigma_1 + pad)
ax.set_ylim(-tau_max - pad, tau_max + pad)

# Mohr's circle
ax.plot(circle_sigma, circle_tau, color="#306998", linewidth=3, zorder=3)

# Reference lines through center
ax.axhline(y=0, color="#555555", linewidth=1, zorder=1)
ax.axvline(x=center, color="#555555", linewidth=1, linestyle="--", alpha=0.4, zorder=1)

# Line connecting stress points A and B
ax.plot([sigma_x, sigma_y], [tau_xy, -tau_xy], color="#C1440E", linewidth=1.5, linestyle="--", alpha=0.5, zorder=2)

# Stress points A(σx, τxy) and B(σy, −τxy)
ax.scatter([sigma_x, sigma_y], [tau_xy, -tau_xy], color="#C1440E", s=200, edgecolors="white", linewidth=1.5, zorder=5)
ax.annotate(
    f"A ({sigma_x}, {tau_xy})",
    xy=(sigma_x, tau_xy),
    xytext=(sigma_x + 10, tau_xy + 14),
    fontsize=16,
    color="#C1440E",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#C1440E", "lw": 1.5},
)
ax.annotate(
    f"B ({sigma_y}, {-tau_xy})",
    xy=(sigma_y, -tau_xy),
    xytext=(sigma_y - 10, -tau_xy - 14),
    fontsize=16,
    color="#C1440E",
    fontweight="bold",
    ha="right",
    arrowprops={"arrowstyle": "->", "color": "#C1440E", "lw": 1.5},
)

# Principal stresses σ₁ and σ₂
ax.scatter([sigma_1, sigma_2], [0, 0], color="#2E8B57", s=200, edgecolors="white", linewidth=1.5, zorder=5)
ax.annotate(
    f"σ₁ = {sigma_1:.1f} MPa",
    xy=(sigma_1, 0),
    xytext=(sigma_1 + 3, -14),
    fontsize=16,
    color="#2E8B57",
    fontweight="bold",
)
ax.annotate(
    f"σ₂ = {sigma_2:.1f} MPa",
    xy=(sigma_2, 0),
    xytext=(sigma_2 - 3, 10),
    fontsize=16,
    color="#2E8B57",
    fontweight="bold",
    ha="right",
)

# Maximum shear stress τ_max at top and bottom
ax.scatter([center, center], [tau_max, -tau_max], color="#2E8B57", s=200, edgecolors="white", linewidth=1.5, zorder=5)
ax.annotate(
    f"τ_max = {tau_max:.1f} MPa",
    xy=(center, tau_max),
    xytext=(center + 15, tau_max + 10),
    fontsize=16,
    color="#2E8B57",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#2E8B57", "lw": 1.5},
)
ax.annotate(
    f"−τ_max = −{tau_max:.1f} MPa",
    xy=(center, -tau_max),
    xytext=(center + 15, -tau_max - 10),
    fontsize=16,
    color="#2E8B57",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#2E8B57", "lw": 1.5},
)

# Principal angle 2θp arc
arc_radius = radius * 0.3
arc = patches.Arc(
    (center, 0),
    2 * arc_radius,
    2 * arc_radius,
    angle=0,
    theta1=0,
    theta2=theta_2p,
    color="#306998",
    linewidth=2.5,
    zorder=4,
)
ax.add_patch(arc)

arc_mid = np.radians(theta_2p / 2)
ax.annotate(
    f"2θp = {theta_2p:.1f}°",
    xy=(center + arc_radius * np.cos(arc_mid), arc_radius * np.sin(arc_mid)),
    xytext=(center + arc_radius * 2.2, arc_radius * 0.5),
    fontsize=16,
    color="#306998",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.5},
)

# Center marker
ax.plot(center, 0, marker="+", color="#306998", markersize=15, markeredgewidth=2.5, zorder=5)
ax.annotate(f"C ({center:.0f}, 0)", xy=(center, 0), xytext=(center - 5, -10), fontsize=14, color="#306998", ha="right")

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
