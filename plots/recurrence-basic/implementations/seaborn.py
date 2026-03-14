"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


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

# Plot
fig, ax = plt.subplots(figsize=(10, 10))
sns.heatmap(
    recurrence_matrix, cmap=["#FFFFFF", "#306998"], cbar=False, square=True, xticklabels=False, yticklabels=False, ax=ax
)

# Style
time_indices = np.linspace(int(t_eval[0]), int(t_eval[0]) + n_embedded - 1, 6, dtype=int)
tick_positions = np.linspace(0, n_embedded - 1, 6)
ax.set_xticks(tick_positions)
ax.set_xticklabels(time_indices, fontsize=16)
ax.set_yticks(tick_positions)
ax.set_yticklabels(time_indices, fontsize=16)
ax.set_xlabel("Time Index", fontsize=20)
ax.set_ylabel("Time Index", fontsize=20)
ax.set_title("Lorenz Attractor · recurrence-basic · seaborn · pyplots.ai", fontsize=22, fontweight="medium", pad=16)
ax.spines["top"].set_visible(True)
ax.spines["right"].set_visible(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
