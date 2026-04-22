""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-04-12
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - synthetic AR(1) process with strong positive autocorrelation
np.random.seed(42)
n = 500
phi = 0.85
noise = np.random.normal(0, 1, n)

values = np.zeros(n)
values[0] = noise[0]
for t in range(1, n):
    values[t] = phi * values[t - 1] + noise[t]

# Lag plot data (lag = 1)
lag = 1
y_t = values[:-lag]
y_t_lag = values[lag:]
time_index = np.arange(len(y_t))

df = pd.DataFrame({"y(t)": y_t, "y(t + 1)": y_t_lag, "Time Index": time_index})

r = np.corrcoef(y_t, y_t_lag)[0, 1]

# Plot
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#888888", "axes.linewidth": 0.8},
)

fig, ax = plt.subplots(figsize=(16, 9))

sns.scatterplot(
    data=df,
    x="y(t)",
    y="y(t + 1)",
    hue="Time Index",
    palette="viridis",
    s=35,
    alpha=0.45,
    edgecolor="white",
    linewidth=0.4,
    legend=False,
    ax=ax,
    zorder=3,
)

# Diagonal reference line (y = x)
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
margin = (data_max - data_min) * 0.05
ax.plot(
    [data_min - margin, data_max + margin],
    [data_min - margin, data_max + margin],
    color="#c44e52",
    linewidth=2,
    linestyle="--",
    alpha=0.6,
    zorder=2,
)

# Colorbar for temporal structure
norm = plt.Normalize(df["Time Index"].min(), df["Time Index"].max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
cbar = plt.colorbar(sm, ax=ax, pad=0.02, aspect=30)
cbar.set_label("Time Index", fontsize=18, color="#444444")
cbar.ax.tick_params(labelsize=14)

# Correlation coefficient
ax.annotate(
    f"r = {r:.2f}",
    xy=(0.03, 0.96),
    xycoords="axes fraction",
    fontsize=18,
    fontweight="bold",
    color="#444444",
    ha="left",
    va="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Style
ax.set_title("scatter-lag · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#333333", pad=16)
ax.set_xlabel("y(t)", fontsize=20, color="#444444")
ax.set_ylabel("y(t + 1)", fontsize=20, color="#444444")
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.grid(True, alpha=0.15, linewidth=0.6)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
