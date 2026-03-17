""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-17
"""

import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - 16-QAM constellation
np.random.seed(42)

ideal_levels = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(ideal_levels, ideal_levels)
ideal_i = ideal_i.ravel()
ideal_q = ideal_q.ravel()

n_symbols = 1200
symbol_indices = np.random.randint(0, 16, n_symbols)

snr_db = 20
snr_linear = 10 ** (snr_db / 10)
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / snr_linear)

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_evm = np.sqrt(np.mean(error_vectors**2)) / np.sqrt(signal_power) * 100

# Plot
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_facecolor("#F8F9FA")

# Decision boundary regions - subtle alternating shading
for row in range(4):
    for col in range(4):
        x0 = [-5, -2, 0, 2][col]
        x1 = [-2, 0, 2, 5][col]
        y0 = [-5, -2, 0, 2][row]
        y1 = [-2, 0, 2, 5][row]
        if (row + col) % 2 == 0:
            ax.fill_between([x0, x1], y0, y1, color="#EBEDEF", zorder=0)

# Decision boundaries
for boundary in [-2, 0, 2]:
    ax.axhline(boundary, color="#BDC3C7", linestyle="--", linewidth=0.9, alpha=0.6, zorder=1)
    ax.axvline(boundary, color="#BDC3C7", linestyle="--", linewidth=0.9, alpha=0.6, zorder=1)

# Received symbols - use inferno for better visibility on light background
norm = mcolors.PowerNorm(gamma=0.7, vmin=error_vectors.min(), vmax=error_vectors.max())
scatter = ax.scatter(
    received_i, received_q, c=error_vectors, cmap="inferno", norm=norm, s=32, alpha=0.65, edgecolors="none", zorder=2
)

# Colorbar
cbar = fig.colorbar(scatter, ax=ax, shrink=0.68, pad=0.02, aspect=28)
cbar.set_label("Error Magnitude", fontsize=18, labelpad=10)
cbar.ax.tick_params(labelsize=14)
cbar.outline.set_edgecolor("#BDC3C7")
cbar.outline.set_linewidth(0.8)

# Ideal constellation points with path effects for glow
ax.scatter(
    ideal_i,
    ideal_q,
    s=350,
    marker="X",
    color="#E74C3C",
    edgecolors="white",
    linewidth=1.5,
    zorder=4,
    label="Ideal symbols",
    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
)

# Concentric rings around ideal points to show decision regions
for ii, iq in zip(ideal_i, ideal_q, strict=True):
    circle = plt.Circle((ii, iq), 0.5, fill=False, color="#E74C3C", linewidth=0.4, alpha=0.25, zorder=1)
    ax.add_patch(circle)

# Style
ax.set_xlabel("In-Phase (I)", fontsize=20, labelpad=8)
ax.set_ylabel("Quadrature (Q)", fontsize=20, labelpad=8)
ax.set_title("scatter-constellation-diagram · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")

for spine in ax.spines.values():
    spine.set_edgecolor("#BDC3C7")
    spine.set_linewidth(0.6)

ax.legend(fontsize=16, loc="upper left", framealpha=0.95, edgecolor="#BDC3C7", fancybox=True, shadow=True)

# EVM annotation
ax.text(
    0.97,
    0.03,
    f"EVM = {rms_evm:.1f}%",
    transform=ax.transAxes,
    fontsize=20,
    fontweight="bold",
    ha="right",
    va="bottom",
    color="#2C3E50",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#2C3E50", "linewidth": 1.5, "alpha": 0.95},
)

# SNR annotation
ax.text(
    0.97,
    0.09,
    f"SNR = {snr_db} dB  |  {n_symbols} symbols",
    transform=ax.transAxes,
    fontsize=14,
    ha="right",
    va="bottom",
    color="#7F8C8D",
    fontstyle="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
