""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


# Data — turbine blade fatigue-life (hours)
np.random.seed(42)

shape_true = 2.5
scale_true = 8000
n_failures = 25
n_censored = 7
n_total = n_failures + n_censored

failure_times = np.sort(stats.weibull_min.rvs(shape_true, scale=scale_true, size=n_failures))
censor_times = np.sort(np.random.uniform(2000, 10000, size=n_censored))

all_times = np.concatenate([failure_times, censor_times])
is_censored = np.concatenate([np.zeros(n_failures, dtype=bool), np.ones(n_censored, dtype=bool)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_censored = is_censored[sort_idx]

# Median rank plotting positions for failures only
failure_rank = np.cumsum(~is_censored)
median_rank = (failure_rank - 0.3) / (n_total + 0.4)

# Weibull linearized y-axis: ln(-ln(1-F))
weibull_y = np.log(-np.log(1 - median_rank))
log_times = np.log(all_times)

# Fit line using only failure points
failure_mask = ~is_censored
slope, intercept, r_value, _, _ = stats.linregress(log_times[failure_mask], weibull_y[failure_mask])

beta = slope
eta = np.exp(-intercept / slope)

# Fit line data
x_fit = np.linspace(np.log(1000), np.log(20000), 200)
y_fit = slope * x_fit + intercept

# Build DataFrame
df = pd.DataFrame(
    {
        "log_time": log_times,
        "weibull_y": weibull_y,
        "censored": is_censored,
        "label": np.where(is_censored, "Censored (suspended)", "Failure"),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

palette = {"Failure": "#306998", "Censored (suspended)": "#D4782F"}
markers = {"Failure": "o", "Censored (suspended)": "D"}

for label, marker in markers.items():
    subset = df[df["label"] == label]
    facecolor = palette[label] if label == "Failure" else "none"
    ax.scatter(
        subset["log_time"],
        subset["weibull_y"],
        s=180,
        marker=marker,
        facecolors=facecolor,
        edgecolors=palette[label],
        linewidths=2,
        label=label,
        zorder=5,
    )

ax.plot(x_fit, y_fit, color="#C04040", linewidth=2.5, linestyle="--", label="Weibull fit", zorder=4)

# Reference line at 63.2% (characteristic life)
y_632 = np.log(-np.log(1 - 0.632))
ax.axhline(y=y_632, color="#888888", linewidth=1.5, linestyle=":", alpha=0.7, zorder=3)
ax.text(np.log(1200), y_632 + 0.12, "63.2% (characteristic life)", fontsize=14, color="#666666")

# Annotate parameters
ax.text(
    0.97,
    0.08,
    f"β = {beta:.2f}  (shape)\nη = {eta:.0f} h  (scale)\nR² = {r_value**2:.4f}",
    transform=ax.transAxes,
    fontsize=15,
    fontfamily="monospace",
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.9},
)

# Style — custom tick labels showing real time values on x-axis
time_ticks = [1000, 2000, 3000, 5000, 8000, 12000, 18000]
ax.set_xticks([np.log(t) for t in time_ticks])
ax.set_xticklabels([f"{t:,}" for t in time_ticks])

# Custom y-axis tick labels showing cumulative probability
prob_ticks = [0.01, 0.05, 0.10, 0.20, 0.40, 0.632, 0.80, 0.90, 0.95, 0.99]
y_tick_vals = [np.log(-np.log(1 - p)) for p in prob_ticks]
ax.set_yticks(y_tick_vals)
ax.set_yticklabels([f"{p * 100:.1f}%" if p != 0.632 else "63.2%" for p in prob_ticks])

ax.set_xlim(np.log(800), np.log(22000))
ax.set_ylim(np.log(-np.log(1 - 0.005)), np.log(-np.log(1 - 0.995)))

ax.set_xlabel("Time to Failure (hours)", fontsize=20)
ax.set_ylabel("Cumulative Failure Probability", fontsize=20)
ax.set_title(
    "Turbine Blade Fatigue Life · probability-weibull · seaborn · pyplots.ai", fontsize=24, fontweight="medium"
)
ax.tick_params(axis="both", labelsize=14)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.15, linewidth=0.8)

ax.legend(fontsize=16, frameon=False, loc="upper left")

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
