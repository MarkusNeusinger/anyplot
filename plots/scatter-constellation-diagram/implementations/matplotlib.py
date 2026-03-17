"""pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-17
"""

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

evm_values = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_evm = np.sqrt(np.mean(evm_values**2)) / np.sqrt(signal_power) * 100

# Plot
fig, ax = plt.subplots(figsize=(10, 10))

ax.scatter(received_i, received_q, s=18, alpha=0.35, color="#306998", edgecolors="none", zorder=2)

ax.scatter(
    ideal_i,
    ideal_q,
    s=280,
    marker="X",
    color="#C0392B",
    edgecolors="white",
    linewidth=0.8,
    zorder=3,
    label="Ideal symbols",
)

# Decision boundaries
for boundary in [-2, 0, 2]:
    ax.axhline(boundary, color="#888888", linestyle="--", linewidth=0.8, alpha=0.4)
    ax.axvline(boundary, color="#888888", linestyle="--", linewidth=0.8, alpha=0.4)

# Style
ax.set_xlabel("In-Phase (I)", fontsize=20)
ax.set_ylabel("Quadrature (Q)", fontsize=20)
ax.set_title("scatter-constellation-diagram · matplotlib · pyplots.ai", fontsize=22, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")

ax.axhline(0, color="#CCCCCC", linewidth=0.5, zorder=0)
ax.axvline(0, color="#CCCCCC", linewidth=0.5, zorder=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.legend(fontsize=16, loc="upper left")

ax.text(
    0.97,
    0.03,
    f"EVM = {rms_evm:.1f}%",
    transform=ax.transAxes,
    fontsize=18,
    fontweight="bold",
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.9},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
