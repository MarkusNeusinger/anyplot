"""pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-11
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy import stats


# Data - turbine blade fatigue-life (hours)
np.random.seed(42)
shape_true, scale_true = 2.5, 8000
n_total = 30
n_failures = 24
n_censored = n_total - n_failures

failure_times = np.sort(stats.weibull_min.rvs(shape_true, scale=scale_true, size=n_failures))
# Add slight deviations to a few points to show diagnostic value
failure_times[2] *= 0.75
failure_times[-3] *= 1.25
censored_times = np.sort(np.random.uniform(2000, 10000, size=n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_censored = np.concatenate([np.zeros(n_failures, dtype=bool), np.ones(n_censored, dtype=bool)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_censored = is_censored[sort_idx]

# Median rank plotting positions for failures only
failure_indices = np.where(~is_censored)[0]
failure_times_sorted = all_times[failure_indices]
ranks = np.arange(1, len(failure_times_sorted) + 1)
median_rank = (ranks - 0.3) / (len(failure_times_sorted) + 0.4)

# Weibull linearized y-axis: ln(-ln(1-F))
weibull_y = np.log(-np.log(1 - median_rank))

# Fit line using least squares on log(time) vs weibull_y
log_times = np.log(failure_times_sorted)
slope, intercept = np.polyfit(log_times, weibull_y, 1)
beta = slope
eta = np.exp(-intercept / beta)

# Censored points plotting positions (use Kaplan-Meier-like adjusted ranks)
censored_indices = np.where(is_censored)[0]
censored_times_vals = all_times[censored_indices]
censored_y_positions = []
for ct in censored_times_vals:
    idx = np.searchsorted(failure_times_sorted, ct, side="right")
    if idx == 0:
        f_val = 0.05
    elif idx >= len(median_rank):
        f_val = median_rank[-1]
    else:
        f_val = median_rank[idx - 1]
    censored_y_positions.append(np.log(-np.log(1 - min(f_val, 0.99))))

# Fit line coordinates
fit_x = np.linspace(np.min(failure_times_sorted) * 0.5, np.max(failure_times_sorted) * 1.5, 200)
fit_y = beta * np.log(fit_x) - beta * np.log(eta)

# Reference line at 63.2% (characteristic life)
y_632 = np.log(-np.log(1 - 0.632))

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")

ax.plot(fit_x, fit_y, color="#306998", linewidth=3, zorder=2, label="Weibull fit")
ax.scatter(
    failure_times_sorted,
    weibull_y,
    s=200,
    color="#306998",
    edgecolors="white",
    linewidth=0.5,
    zorder=3,
    label="Failures",
)
ax.scatter(
    censored_times_vals,
    censored_y_positions,
    s=200,
    facecolors="none",
    edgecolors="#306998",
    linewidth=2.5,
    zorder=3,
    label="Censored",
)
ax.axhline(
    y=y_632, color="#C04E3A", linewidth=2, linestyle="--", alpha=0.7, zorder=1, label="63.2% (characteristic life)"
)

# Annotate parameters
ax.text(
    0.97,
    0.08,
    f"\u03b2 = {beta:.2f}  (shape)\n\u03b7 = {eta:.0f} h  (scale)",
    transform=ax.transAxes,
    fontsize=18,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.95, "linewidth": 1.5},
)

# CDF probability labels on right y-axis
prob_levels = [0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.99]
prob_y = [np.log(-np.log(1 - p)) for p in prob_levels]
ax2 = ax.twinx()
ax2.set_ylim(ax.get_ylim())
ax2.set_yticks(prob_y)
ax2.set_yticklabels([f"{p * 100:.1f}%" for p in prob_levels])
ax2.tick_params(axis="y", labelsize=14, colors="#555555")
ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.set_ylabel("Cumulative Probability", fontsize=16, color="#555555")

# Style
ax.set_xscale("log")
ax.set_xlabel("Time to Failure (hours)", fontsize=20)
ax.set_ylabel("ln(-ln(1-F))", fontsize=20)
ax.set_title("probability-weibull \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=16, loc="upper left", framealpha=0.95, edgecolor="#cccccc", fancybox=True)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color="#888888")
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#888888")
    ax.spines[spine].set_linewidth(0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
