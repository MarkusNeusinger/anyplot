""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
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
fig, ax = plt.subplots(figsize=(12, 12), facecolor="#FAFAFA")
ax.set_facecolor("#F5F5F0")

# Binary colormap using BoundaryNorm for crisp thresholding
cmap = ListedColormap(["#F5F5F0", "#306998"])
norm = BoundaryNorm([0, 0.5, 1], cmap.N)
ax.imshow(recurrence_matrix, cmap=cmap, norm=norm, origin="lower", interpolation="none", aspect="equal")

# Title - correct format with subtitle
fig.suptitle("recurrence-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", y=0.98)
ax.set_title(
    "Lorenz Attractor x-component  |  dim=3, τ=5, ε=percentile(15%)",
    fontsize=13,
    color="#777777",
    style="italic",
    pad=30,
)

# Axis labels
ax.set_xlabel("Time Index", fontsize=20, labelpad=10)
ax.set_ylabel("Time Index", fontsize=20, labelpad=10)

# Tick formatting with FuncFormatter
ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
ax.yaxis.set_major_locator(ticker.MultipleLocator(100))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(50))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(50))
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
ax.tick_params(axis="both", which="major", labelsize=16, length=6, width=1.2, color="#888888")
ax.tick_params(axis="both", which="minor", length=3, width=0.8, color="#BBBBBB")

# Spine styling - thin, muted
for spine in ax.spines.values():
    spine.set_color("#CCCCCC")
    spine.set_linewidth(0.8)

# Annotate key dynamical regions
ax.annotate(
    "periodic\ntransient",
    xy=(50, 50),
    xytext=(50, 160),
    fontsize=12,
    color="#AA4400",
    fontweight="bold",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#AA4400", "lw": 1.5},
)
ax.annotate(
    "chaotic regime",
    xy=(250, 250),
    xytext=(140, 310),
    fontsize=12,
    color="#AA4400",
    fontweight="bold",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#AA4400", "lw": 1.5, "connectionstyle": "arc3,rad=0.2"},
)

# Recurrence rate annotation
rr = np.sum(recurrence_matrix) / recurrence_matrix.size * 100
bbox_props = {"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.9}
ax.text(
    0.98,
    0.02,
    f"RR = {rr:.1f}%",
    transform=ax.transAxes,
    fontsize=14,
    ha="right",
    va="bottom",
    bbox=bbox_props,
    color="#306998",
    fontweight="bold",
)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
