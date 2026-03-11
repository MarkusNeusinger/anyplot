"""pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data
np.random.seed(42)
n_failures = 25
n_censored = 7
n_total = n_failures + n_censored

failure_times = np.sort(stats.weibull_min.rvs(c=2.8, scale=5000, size=n_failures))
censored_times = np.sort(stats.uniform.rvs(loc=1000, scale=5000, size=n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_failure = np.array([True] * n_failures + [False] * n_censored)

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_failure = is_failure[sort_idx]

failure_order = np.cumsum(is_failure)
median_rank = np.where(is_failure, (failure_order - 0.3) / (n_failures + 0.4), np.nan)

weibull_y = np.where(is_failure, np.log(-np.log(1 - median_rank)), np.nan)

df = pd.DataFrame(
    {
        "time": all_times,
        "median_rank": median_rank,
        "weibull_y": weibull_y,
        "log_time": np.log(all_times),
        "status": np.where(is_failure, "Failure", "Censored"),
    }
)

# Fit Weibull line using only failure data
failures_df = df[df["status"] == "Failure"].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(failures_df["log_time"], failures_df["weibull_y"])
beta = slope
eta = np.exp(-intercept / beta)

# Fitted line data
log_time_range = np.linspace(np.log(df["time"].min() * 0.7), np.log(df["time"].max() * 1.3), 200)
fitted_y = beta * log_time_range + intercept
fit_df = pd.DataFrame({"log_time": log_time_range, "weibull_y": fitted_y, "time": np.exp(log_time_range)})

# Weibull y-axis: reference probabilities and their transformed values
prob_levels = np.array([0.01, 0.05, 0.10, 0.20, 0.40, 0.632, 0.80, 0.90, 0.99])
weibull_ticks = np.log(-np.log(1 - prob_levels))
prob_labels = [f"{p * 100:.1f}%" for p in prob_levels]
prob_labels = [lbl.replace(".0%", "%") for lbl in prob_labels]

# X-axis tick values
x_tick_values = [1000, 2000, 3000, 5000, 7000, 10000]
log_x_ticks = [np.log(v) for v in x_tick_values]
x_labels = [str(v) for v in x_tick_values]

# Reference line at 63.2%
ref_y = np.log(-np.log(1 - 0.632))

# Censored points y-position (place near bottom for visibility)
censored_df = df[df["status"] == "Censored"].copy()
censored_y_pos = weibull_ticks[0] + 0.3
censored_df = censored_df.assign(weibull_y=censored_y_pos)

# Plot
plot = (
    ggplot()
    + geom_line(fit_df, aes(x="log_time", y="weibull_y"), color="#306998", size=1.5, alpha=0.8)
    + geom_hline(yintercept=ref_y, linetype="dashed", color="#888888", size=0.8, alpha=0.6)
    + geom_point(
        failures_df, aes(x="log_time", y="weibull_y"), color="#306998", fill="#306998", size=4, shape="o", alpha=0.9
    )
    + geom_point(
        censored_df, aes(x="log_time", y="weibull_y"), color="#E06C3A", fill="white", size=4, shape="^", stroke=1.2
    )
    + annotate(
        "text",
        x=log_x_ticks[-1],
        y=ref_y + 0.15,
        label="63.2% (Characteristic Life)",
        size=11,
        ha="right",
        color="#888888",
    )
    + annotate(
        "text",
        x=log_x_ticks[0] + 0.1,
        y=weibull_ticks[-2] + 0.3,
        label=f"β = {beta:.2f}\nη = {eta:.0f} hrs\nR² = {r_value**2:.3f}",
        size=12,
        ha="left",
        va="top",
        color="#306998",
    )
    + annotate(
        "text",
        x=censored_df["log_time"].values[0] if len(censored_df) > 0 else log_x_ticks[0],
        y=censored_y_pos - 0.35,
        label="▲ Censored observations",
        size=10,
        ha="left",
        color="#E06C3A",
    )
    + scale_x_continuous(breaks=log_x_ticks, labels=x_labels)
    + scale_y_continuous(breaks=weibull_ticks.tolist(), labels=prob_labels)
    + labs(
        x="Time to Failure (hours)",
        y="Cumulative Failure Probability",
        title="probability-weibull · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(alpha=0.2, size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
