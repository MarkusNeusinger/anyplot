""" pyplots.ai
band-basic: Basic Band Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: 94/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: 7-day temperature forecast from 200-member ensemble weather model
np.random.seed(42)
n_points = 80
n_ensemble = 200
days = np.linspace(0, 7, n_points)

# Base forecast: diurnal temperature cycle with gradual warming trend
base = 15 + 6 * np.sin(2 * np.pi * days - np.pi / 2) + 0.4 * days

# Ensemble members diverge via cumulative random drift (uncertainty grows with horizon)
drifts = np.cumsum(np.random.normal(0, 0.08, (n_ensemble, n_points)), axis=1)
all_temps = base + drifts

df = pd.DataFrame({"Forecast Day": np.tile(days, n_ensemble), "Temperature (°C)": all_temps.ravel()})

# Plot: sns.lineplot natively computes mean + 95% prediction interval from ensemble
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.15,
        "grid.linewidth": 0.6,
        "grid.linestyle": "--",
    },
)
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="Forecast Day",
    y="Temperature (°C)",
    estimator="mean",
    errorbar=("pi", 95),
    color="#306998",
    linewidth=3,
    err_kws={"alpha": 0.3},
    ax=ax,
)

# Contrasting center line for clear visual hierarchy
ax.lines[0].set_color("#FFD43B")
ax.lines[0].set_zorder(10)

# Legend: label line and band explicitly
ax.lines[0].set_label("Ensemble Mean")
ax.collections[0].set_label("95% Prediction Interval")
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, edgecolor="none")

# Typography
ax.set_xlabel("Forecast Horizon (days)", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("band-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
