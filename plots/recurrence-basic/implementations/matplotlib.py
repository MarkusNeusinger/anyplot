""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


# Data - Lorenz attractor x-component
sol = solve_ivp(
    lambda t, s: [10.0 * (s[1] - s[0]), s[0] * (28.0 - s[2]) - s[1], s[0] * s[1] - (8.0 / 3.0) * s[2]],
    [0, 50],
    [1.0, 1.0, 1.0],
    t_eval=np.linspace(0, 50, 5000),
    max_step=0.01,
)
signal = sol.y[0][::10]  # 500 points from x-component

# Time-delay embedding (Takens' theorem)
embedding_dim = 3
delay = 5
n_embedded = len(signal) - (embedding_dim - 1) * delay
embedded = np.column_stack([signal[i * delay : i * delay + n_embedded] for i in range(embedding_dim)])

# Distance matrix and recurrence
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = np.percentile(distance_matrix, 15)
recurrence_matrix = (distance_matrix <= threshold).astype(int)

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

cmap = LinearSegmentedColormap.from_list("recurrence", ["#FFFFFF", "#306998"])
ax.imshow(recurrence_matrix, cmap=cmap, origin="lower", interpolation="none", aspect="equal")

# Style
ax.set_xlabel("Time Index", fontsize=20)
ax.set_ylabel("Time Index", fontsize=20)
ax.set_title("Lorenz Attractor · recurrence-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
