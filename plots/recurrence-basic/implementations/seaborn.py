"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: seaborn 0.13.2 | Python 3.14.3
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


# Seaborn styling — leverage seaborn's theming system with custom palette
sns.set_theme(style="white", context="talk", font_scale=1.1)
custom_palette = sns.color_palette(["#F7F7F2", "#306998"])
sns.set_palette(custom_palette)

# Data - Lorenz attractor x-component
sol = solve_ivp(
    lambda t, s: [10.0 * (s[1] - s[0]), s[0] * (28.0 - s[2]) - s[1], s[0] * s[1] - 8.0 / 3.0 * s[2]],
    [0, 50],
    [1.0, 1.0, 1.0],
    max_step=0.05,
    dense_output=True,
)
t_eval = np.linspace(5, 50, 500)
x_series = sol.sol(t_eval)[0]

# Time-delay embedding (Takens' theorem)
embedding_dim = 3
delay = 5
n_embedded = len(x_series) - (embedding_dim - 1) * delay
embedded = np.column_stack([x_series[i * delay : i * delay + n_embedded] for i in range(embedding_dim)])

# Recurrence matrix (binary)
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.15 * np.max(distance_matrix)
recurrence_matrix = (distance_matrix <= threshold).astype(int)

# Build continuous distance heatmap using seaborn's sequential palette
# Normalize distances for the color-mapped background layer
norm_distances = distance_matrix / np.max(distance_matrix)

# Plot — square format for recurrence matrix (12x12 → 3600x3600 at 300dpi)
fig, ax = plt.subplots(figsize=(12, 12))

# Layer 1: Distance-based heatmap as subtle background using seaborn's cubehelix palette
bg_cmap = sns.cubehelix_palette(start=2.2, rot=0.1, light=0.97, dark=0.85, as_cmap=True)
sns.heatmap(
    norm_distances,
    cmap=bg_cmap,
    cbar=False,
    square=True,
    xticklabels=False,
    yticklabels=False,
    linewidths=0,
    ax=ax,
    zorder=1,
)

# Layer 2: Binary recurrence overlay using seaborn's light_palette
recurrence_cmap = sns.light_palette("#306998", as_cmap=True)
masked_recurrence = np.ma.masked_where(recurrence_matrix == 0, recurrence_matrix.astype(float))
ax.pcolormesh(masked_recurrence, cmap=recurrence_cmap, vmin=0, vmax=1, zorder=2)

# Spine removal — seaborn convention
sns.despine(ax=ax, left=True, bottom=True)

# Custom tick labels at meaningful positions
n_ticks = 6
tick_positions = np.linspace(0, n_embedded - 1, n_ticks)
tick_labels = [f"{int(v)}" for v in np.linspace(0, n_embedded - 1, n_ticks)]
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels, fontsize=16)
ax.set_yticks(tick_positions)
ax.set_yticklabels(tick_labels, fontsize=16, rotation=0)

# Labels and title
ax.set_xlabel("Time Index (embedding steps)", fontsize=20, labelpad=12)
ax.set_ylabel("Time Index (embedding steps)", fontsize=20, labelpad=12)
ax.set_title("Lorenz Attractor · recurrence-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

# Recurrence rate as a marginal distribution using seaborn's lineplot
# Create a small inset showing recurrence density along the time axis
recurrence_rate = recurrence_matrix.sum(axis=1) / n_embedded
ax_inset = fig.add_axes([0.17, 0.52, 0.18, 0.12])
rate_df = pd.DataFrame({"Time": np.arange(n_embedded), "Recurrence Rate": recurrence_rate})
sns.lineplot(data=rate_df, x="Time", y="Recurrence Rate", color="#306998", linewidth=1.5, ax=ax_inset)
ax_inset.fill_between(rate_df["Time"], rate_df["Recurrence Rate"], alpha=0.3, color="#306998")
ax_inset.set_title("Recurrence Rate", fontsize=10, color="#444444")
ax_inset.set_xlabel("")
ax_inset.set_ylabel("")
ax_inset.tick_params(labelsize=8)
sns.despine(ax=ax_inset)
ax_inset.set_facecolor("#FAFAF5")
ax_inset.patch.set_alpha(0.92)

# Storytelling — annotate key structural features (repositioned to avoid overlap)
# Diagonal lines = deterministic dynamics — place text in lower-right white space
ax.annotate(
    "Diagonal lines\n= determinism",
    xy=(350, 380),
    xytext=(430, 465),
    fontsize=14,
    color="#306998",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.8},
    ha="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
)

# Block clusters = regime recurrence
ax.annotate(
    "Block clusters\n= recurring regimes",
    xy=(70, 70),
    xytext=(200, 18),
    fontsize=14,
    color="#8B4513",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#8B4513", "lw": 1.8},
    ha="center",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
)

# Add a subtle note about the embedding
fig.text(
    0.5,
    0.015,
    "3D time-delay embedding (τ=5) · Euclidean distance · ε = 15% of max distance",
    ha="center",
    fontsize=13,
    color="#666666",
    style="italic",
)

fig.subplots_adjust(bottom=0.1, left=0.12, right=0.95, top=0.94)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
