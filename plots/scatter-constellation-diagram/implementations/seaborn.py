""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-17
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

ideal_levels = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(ideal_levels, ideal_levels)
ideal_i = ideal_i.ravel()
ideal_q = ideal_q.ravel()

n_symbols = 1200
symbol_indices = np.random.randint(0, 16, size=n_symbols)

snr_db = 20
snr_linear = 10 ** (snr_db / 10)
noise_std = np.sqrt(5 / snr_linear)

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_signal = np.sqrt(np.mean(ideal_i**2 + ideal_q**2))
evm_pct = np.sqrt(np.mean(error_vectors**2)) / rms_signal * 100

df_received = pd.DataFrame({"I": received_i, "Q": received_q})
df_ideal = pd.DataFrame({"I": ideal_i, "Q": ideal_q})

# Plot
fig, ax = plt.subplots(figsize=(10, 10))

decision_boundaries = [-4, -2, 0, 2, 4]
for b in decision_boundaries:
    ax.axhline(y=b, color="#888888", linestyle="--", linewidth=0.8, alpha=0.4)
    ax.axvline(x=b, color="#888888", linestyle="--", linewidth=0.8, alpha=0.4)

sns.scatterplot(
    data=df_received, x="I", y="Q", color="#306998", alpha=0.35, s=30, edgecolor="none", ax=ax, legend=False
)

sns.scatterplot(
    data=df_ideal,
    x="I",
    y="Q",
    color="#D94F3B",
    s=400,
    marker="X",
    edgecolor="white",
    linewidth=1.2,
    ax=ax,
    legend=False,
    zorder=5,
)

# Style
ax.set_xlabel("In-Phase (I)", fontsize=20)
ax.set_ylabel("Quadrature (Q)", fontsize=20)
ax.set_title("scatter-constellation-diagram · seaborn · pyplots.ai", fontsize=22, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.text(
    0.97,
    0.03,
    f"EVM = {evm_pct:.1f}%",
    transform=ax.transAxes,
    fontsize=18,
    fontweight="medium",
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.9},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
