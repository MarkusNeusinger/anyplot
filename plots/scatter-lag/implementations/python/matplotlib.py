""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-04-12
"""

import matplotlib.pyplot as plt
import numpy as np


# Data — synthetic AR(1) process with strong positive autocorrelation
np.random.seed(42)
n_observations = 500
phi = 0.85
noise = np.random.normal(0, 1, n_observations)
series = np.zeros(n_observations)
series[0] = noise[0]
for i in range(1, n_observations):
    series[i] = phi * series[i - 1] + noise[i]

lag = 1
y_t = series[:-lag]
y_t_lag = series[lag:]
time_index = np.arange(len(y_t))

# Correlation
r_value = np.corrcoef(y_t, y_t_lag)[0, 1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

scatter = ax.scatter(
    y_t, y_t_lag, c=time_index, cmap="viridis", s=120, alpha=0.65, edgecolors="white", linewidth=0.5, zorder=2
)

# Diagonal reference line (y = x)
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
margin = (data_max - data_min) * 0.05
ax.plot(
    [data_min - margin, data_max + margin],
    [data_min - margin, data_max + margin],
    color="#AAAAAA",
    linewidth=2,
    linestyle="--",
    alpha=0.6,
    zorder=1,
)

# Colorbar
cbar = fig.colorbar(scatter, ax=ax, pad=0.02, aspect=30)
cbar.set_label("Time Index", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Correlation annotation
ax.text(
    0.04,
    0.96,
    f"r = {r_value:.3f}",
    transform=ax.transAxes,
    fontsize=20,
    verticalalignment="top",
    fontweight="medium",
    color="#333333",
)

# Style
ax.set_xlabel("y(t)", fontsize=20)
ax.set_ylabel(f"y(t + {lag})", fontsize=20)
ax.set_title("AR(1) Autocorrelation · scatter-lag · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
