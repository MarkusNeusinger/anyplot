""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
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

# Quadrant labels for hue-based coloring
quadrant_labels = []
for idx in symbol_indices:
    qi, qq = ideal_i[idx], ideal_q[idx]
    if qi > 0 and qq > 0:
        quadrant_labels.append("Q1 (+I, +Q)")
    elif qi < 0 and qq > 0:
        quadrant_labels.append("Q2 (−I, +Q)")
    elif qi < 0 and qq < 0:
        quadrant_labels.append("Q3 (−I, −Q)")
    else:
        quadrant_labels.append("Q4 (+I, −Q)")

df_received = pd.DataFrame({"In-Phase (I)": received_i, "Quadrature (Q)": received_q, "Quadrant": quadrant_labels})
df_ideal = pd.DataFrame({"In-Phase (I)": ideal_i, "Quadrature (Q)": ideal_q})

# Style — leverage seaborn's theming and context scaling
sns.set_context("talk", font_scale=1.1)
sns.set_style("whitegrid", {"grid.alpha": 0.15, "grid.linestyle": ":"})
quad_palette = sns.color_palette("colorblind", 4)

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# Decision boundary grid
decision_boundaries = [-4, -2, 0, 2, 4]
for b in decision_boundaries:
    ax.axhline(y=b, color="#999999", linestyle="--", linewidth=0.7, alpha=0.35)
    ax.axvline(x=b, color="#999999", linestyle="--", linewidth=0.7, alpha=0.35)

# Density contours per quadrant — distinctive seaborn feature (kdeplot)
for i, quad in enumerate(["Q1 (+I, +Q)", "Q2 (−I, +Q)", "Q3 (−I, −Q)", "Q4 (+I, −Q)"]):
    subset = df_received[df_received["Quadrant"] == quad]
    sns.kdeplot(
        data=subset,
        x="In-Phase (I)",
        y="Quadrature (Q)",
        levels=3,
        color=quad_palette[i],
        alpha=0.35,
        linewidths=1.0,
        ax=ax,
    )

# Received symbols with hue — seaborn handles palette mapping
sns.scatterplot(
    data=df_received,
    x="In-Phase (I)",
    y="Quadrature (Q)",
    hue="Quadrant",
    hue_order=["Q1 (+I, +Q)", "Q2 (−I, +Q)", "Q3 (−I, −Q)", "Q4 (+I, −Q)"],
    palette=quad_palette,
    alpha=0.45,
    s=35,
    edgecolor="none",
    ax=ax,
    legend=True,
)

# Ideal constellation markers
sns.scatterplot(
    data=df_ideal,
    x="In-Phase (I)",
    y="Quadrature (Q)",
    color="#222222",
    s=450,
    marker="X",
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
    legend=False,
    zorder=5,
)

# Style refinements
ax.set_title("scatter-constellation-diagram · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=18)
ax.set_xlabel("In-Phase (I)", fontsize=20)
ax.set_ylabel("Quadrature (Q)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend — seaborn-generated, refined positioning
legend = ax.legend(
    title="Quadrant",
    title_fontsize=16,
    fontsize=14,
    loc="upper left",
    framealpha=0.9,
    edgecolor="#CCCCCC",
    markerscale=2.0,
)

# EVM annotation
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
