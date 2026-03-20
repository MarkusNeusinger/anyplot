""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
r_min, r_max = 2.5, 4.0
num_r = 2000
transient = 200
iterations = 100

r_values = np.linspace(r_min, r_max, num_r)
r_plot = np.empty(num_r * iterations)
x_plot = np.empty(num_r * iterations)

for i, r in enumerate(r_values):
    x = 0.5
    for _ in range(transient):
        x = r * x * (1 - x)
    for j in range(iterations):
        x = r * x * (1 - x)
        r_plot[i * iterations + j] = r
        x_plot[i * iterations + j] = x

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.scatter(r_plot, x_plot, s=0.05, c="#306998", alpha=0.35, linewidths=0, rasterized=True)

# Annotations for key bifurcation points
bifurcation_points = [(3.0, "Period-2", -12), (3.449, "Period-4", -50), (3.544, "Period-8", 12)]
for r_bif, label, x_offset in bifurcation_points:
    ax.axvline(r_bif, color="#B0B0B0", linewidth=0.8, linestyle="--", alpha=0.4)
    ha = "right" if x_offset < 0 else "left"
    ax.annotate(
        f"{label}  r ≈ {r_bif}",
        xy=(r_bif, 0.97),
        xycoords=("data", "axes fraction"),
        xytext=(x_offset, 0),
        textcoords="offset points",
        fontsize=12,
        color="#555555",
        ha=ha,
        va="top",
    )

# Style
ax.set_xlabel("Growth Rate (r)", fontsize=20)
ax.set_ylabel("Steady-State Population (x)", fontsize=20)
ax.set_title("bifurcation-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(r_min, r_max)
ax.set_ylim(0, 1)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
