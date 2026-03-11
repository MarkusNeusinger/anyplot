""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: altair 6.0.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-11
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats


# Data - Turbine blade fatigue-life (hours)
np.random.seed(42)
n_failures = 25
n_censored = 5
shape_true = 2.5
scale_true = 5000

failure_times = np.sort(stats.weibull_min.rvs(shape_true, scale=scale_true, size=n_failures))
censored_times = np.sort(np.random.uniform(1000, 4500, size=n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_failure = np.concatenate([np.ones(n_failures), np.zeros(n_censored)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_failure = is_failure[sort_idx]

# Median rank plotting positions for failures only
failure_ranks = np.cumsum(is_failure)
n_total = n_failures + n_censored
median_rank = (failure_ranks - 0.3) / (n_total + 0.4)

# Weibull y-axis transform: ln(-ln(1 - F))
weibull_y = np.log(-np.log(1 - median_rank))

# Log-transform x for linear regression on failures
log_times = np.log(all_times)

failure_mask = is_failure == 1
slope, intercept, _, _, _ = stats.linregress(log_times[failure_mask], weibull_y[failure_mask])
beta_est = slope
eta_est = np.exp(-intercept / slope)

# Build dataframe
df = pd.DataFrame(
    {
        "time": all_times,
        "log_time": log_times,
        "weibull_y": weibull_y,
        "status": np.where(is_failure == 1, "Failure", "Censored"),
    }
)

# Fitted line data
fit_x = np.linspace(np.log(all_times.min() * 0.7), np.log(all_times.max() * 1.3), 200)
fit_y = slope * fit_x + intercept
df_fit = pd.DataFrame({"log_time": fit_x, "weibull_y": fit_y})

# Reference line at 63.2% (characteristic life)
ref_y = np.log(-np.log(1 - 0.632))

# Y-axis range
y_min = np.log(-np.log(1 - 0.005))
y_max = np.log(-np.log(1 - 0.995))

# Plot - Failure points (filled)
failures_chart = (
    alt.Chart(df[df["status"] == "Failure"])
    .mark_point(size=200, filled=True, color="#306998", strokeWidth=1.5, stroke="white")
    .encode(
        x=alt.X("log_time:Q", scale=alt.Scale(nice=False), title="ln(Time to Failure) [hours]"),
        y=alt.Y("weibull_y:Q", scale=alt.Scale(domain=[y_min, y_max]), title="ln(-ln(1-F)) [Weibull Scale]"),
        tooltip=[
            alt.Tooltip("time:Q", title="Time (hrs)", format=".0f"),
            alt.Tooltip("weibull_y:Q", title="Weibull Y", format=".2f"),
        ],
    )
)

# Censored points (hollow)
censored_chart = (
    alt.Chart(df[df["status"] == "Censored"])
    .mark_point(size=200, filled=False, color="#306998", strokeWidth=2.5)
    .encode(
        x=alt.X("log_time:Q"),
        y=alt.Y("weibull_y:Q"),
        tooltip=[alt.Tooltip("time:Q", title="Time (hrs)", format=".0f"), alt.Tooltip("status:N", title="Status")],
    )
)

# Fitted line
fit_line = (
    alt.Chart(df_fit)
    .mark_line(strokeWidth=2.5, color="#E8792B", strokeDash=[8, 4])
    .encode(x=alt.X("log_time:Q"), y=alt.Y("weibull_y:Q"))
)

# Reference line at 63.2%
df_ref = pd.DataFrame(
    {"weibull_y": [ref_y, ref_y], "log_time": [np.log(all_times.min() * 0.7), np.log(all_times.max() * 1.3)]}
)

ref_line = (
    alt.Chart(df_ref)
    .mark_line(strokeWidth=1.5, color="#999999", strokeDash=[4, 4])
    .encode(x=alt.X("log_time:Q"), y=alt.Y("weibull_y:Q"))
)

# Annotation for parameters
df_annotation = pd.DataFrame(
    {
        "log_time": [np.log(all_times.max() * 0.85)],
        "weibull_y": [y_min + (y_max - y_min) * 0.15],
        "text": [f"\u03b2 = {beta_est:.2f},  \u03b7 = {eta_est:.0f} hrs"],
    }
)

param_text = (
    alt.Chart(df_annotation)
    .mark_text(fontSize=20, align="right", fontWeight="bold", color="#333333")
    .encode(x=alt.X("log_time:Q"), y=alt.Y("weibull_y:Q"), text="text:N")
)

# 63.2% label
df_ref_label = pd.DataFrame(
    {"log_time": [np.log(all_times.min() * 0.75)], "weibull_y": [ref_y + 0.15], "text": ["63.2% (Characteristic Life)"]}
)

ref_label = (
    alt.Chart(df_ref_label)
    .mark_text(fontSize=16, align="left", color="#777777")
    .encode(x=alt.X("log_time:Q"), y=alt.Y("weibull_y:Q"), text="text:N")
)

# Combine
chart = (
    (ref_line + fit_line + failures_chart + censored_chart + param_text + ref_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("probability-weibull \u00b7 altair \u00b7 pyplots.ai", fontSize=28, fontWeight=500),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.2)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
