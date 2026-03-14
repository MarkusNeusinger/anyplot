"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


# Seaborn styling — leverage seaborn's theming system
sns.set_theme(style="white", context="talk", font_scale=1.1)

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

# Build a custom sequential colormap for visual richness
cmap = sns.light_palette("#306998", as_cmap=True)

# Plot — square format for recurrence matrix (12x12 → 3600x3600 at 300dpi)
fig, ax = plt.subplots(figsize=(12, 12))

# Use sns.heatmap with seaborn's palette utilities
sns.heatmap(
    recurrence_matrix,
    cmap=["#F7F7F2", "#306998"],
    cbar=False,
    square=True,
    xticklabels=False,
    yticklabels=False,
    linewidths=0,
    ax=ax,
)

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

# Storytelling — annotate key structural features
# Diagonal lines = deterministic dynamics
ax.annotate(
    "Diagonal lines\n= determinism",
    xy=(280, 310),
    xytext=(380, 420),
    fontsize=14,
    color="#306998",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 1.5},
    ha="center",
)

# Block clusters = regime recurrence
ax.annotate(
    "Block clusters\n= recurring regimes",
    xy=(70, 70),
    xytext=(180, 30),
    fontsize=14,
    color="#8B4513",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#8B4513", "lw": 1.5},
    ha="center",
    va="center",
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

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
