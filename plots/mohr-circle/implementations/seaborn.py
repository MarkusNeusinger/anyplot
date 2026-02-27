""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-02-27
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

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

# Stress points as DataFrame for seaborn
stress_df = pd.DataFrame({"sigma": [sigma_x, sigma_y], "tau": [tau_xy, -tau_xy], "point": ["A", "B"]})

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# Mohr's circle
ax.plot(circle_sigma, circle_tau, color="#306998", linewidth=3, zorder=3)
ax.fill(circle_sigma, circle_tau, color="#306998", alpha=0.05, zorder=1)

# Reference lines
ax.axhline(y=0, color="#555555", linewidth=1.2, zorder=2)
ax.axvline(x=center, color="#aaaaaa", linewidth=1, linestyle="--", alpha=0.5, zorder=2)

# Diameter line connecting A and B
ax.plot([sigma_x, sigma_y], [tau_xy, -tau_xy], color="#C0392B", linewidth=2, linestyle="--", alpha=0.6, zorder=3)

# Stress points A and B
sns.scatterplot(
    data=stress_df,
    x="sigma",
    y="tau",
    color="#C0392B",
    s=300,
    edgecolor="white",
    linewidth=2,
    zorder=5,
    ax=ax,
    legend=False,
)

# Principal stresses on the horizontal axis
ax.scatter([sigma_1, sigma_2], [0, 0], s=300, color="#27AE60", edgecolors="white", linewidth=2, zorder=5, marker="D")

# Maximum shear stress points at top and bottom of circle
ax.scatter(
    [center, center], [tau_max, -tau_max], s=300, color="#E67E22", edgecolors="white", linewidth=2, zorder=5, marker="s"
)

# Center point
ax.scatter([center], [0], s=200, color="#306998", edgecolors="white", linewidth=2, zorder=5)
ax.annotate(
    f"C ({center:.0f}, 0)",
    xy=(center, 0),
    xytext=(center - 5, -radius * 0.25),
    fontsize=14,
    color="#306998",
    ha="right",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.5},
    zorder=6,
)

# Annotate stress point A
ax.annotate(
    f"A ({sigma_x}, {tau_xy})",
    xy=(sigma_x, tau_xy),
    xytext=(sigma_x - 15, tau_xy + 18),
    fontsize=15,
    fontweight="bold",
    color="#C0392B",
    ha="right",
    arrowprops={"arrowstyle": "->", "color": "#C0392B", "lw": 1.5},
    zorder=6,
)

# Annotate stress point B
ax.annotate(
    f"B ({sigma_y}, {-tau_xy})",
    xy=(sigma_y, -tau_xy),
    xytext=(sigma_y + 20, -tau_xy - 22),
    fontsize=15,
    fontweight="bold",
    color="#C0392B",
    arrowprops={"arrowstyle": "->", "color": "#C0392B", "lw": 1.5},
    zorder=6,
)

# Annotate principal stresses
ax.annotate(
    f"\u03c3\u2081 = {sigma_1:.1f} MPa",
    xy=(sigma_1, 0),
    xytext=(sigma_1 - 20, radius * 0.5),
    fontsize=15,
    fontweight="bold",
    color="#27AE60",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#27AE60", "lw": 1.5},
    zorder=6,
)

ax.annotate(
    f"\u03c3\u2082 = {sigma_2:.1f} MPa",
    xy=(sigma_2, 0),
    xytext=(sigma_2 + 20, radius * 0.35),
    fontsize=15,
    fontweight="bold",
    color="#27AE60",
    arrowprops={"arrowstyle": "->", "color": "#27AE60", "lw": 1.5},
    zorder=6,
)

# Annotate maximum shear stress
ax.annotate(
    f"\u03c4max = {tau_max:.1f} MPa",
    xy=(center, tau_max),
    xytext=(center + radius * 0.55, tau_max - 5),
    fontsize=15,
    fontweight="bold",
    color="#E67E22",
    arrowprops={"arrowstyle": "->", "color": "#E67E22", "lw": 1.5},
    zorder=6,
)

# Draw 2theta_p angle arc from horizontal to point A direction
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
    fontsize=15,
    fontweight="bold",
    color="#8E44AD",
    ha="left",
    va="bottom",
)

# Legend
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=3, label="Mohr's Circle"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#C0392B", markersize=12, label="Stress States (A, B)"),
    Line2D(
        [0],
        [0],
        marker="D",
        color="w",
        markerfacecolor="#27AE60",
        markersize=12,
        label="Principal Stresses (\u03c3\u2081, \u03c3\u2082)",
    ),
    Line2D(
        [0], [0], marker="s", color="w", markerfacecolor="#E67E22", markersize=12, label="Max Shear Stress (\u03c4max)"
    ),
    Line2D([0], [0], color="#8E44AD", linewidth=2.5, label="Principal Angle (2\u03b8p)"),
]
ax.legend(handles=legend_elements, fontsize=14, loc="lower left", framealpha=0.9, edgecolor="#cccccc")

# Style
ax.set_xlabel("Normal Stress \u03c3 (MPa)", fontsize=20)
ax.set_ylabel("Shear Stress \u03c4 (MPa)", fontsize=20)
ax.set_title("mohr-circle \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.2, linewidth=0.8)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
