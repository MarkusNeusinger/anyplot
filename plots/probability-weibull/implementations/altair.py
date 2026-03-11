""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: altair 6.0.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-11
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

# Build dataframe with actual time values (x-axis will use log scale)
df = pd.DataFrame(
    {
        "time": all_times,
        "log_time": log_times,
        "weibull_y": weibull_y,
        "status": np.where(is_failure == 1, "Failure", "Censored"),
    }
)

# Fitted line data - use actual time values
fit_log_x = np.linspace(np.log(all_times.min() * 0.7), np.log(all_times.max() * 1.3), 200)
fit_y = slope * fit_log_x + intercept
fit_time = np.exp(fit_log_x)
df_fit = pd.DataFrame({"time": fit_time, "weibull_y": fit_y})

# Reference line at 63.2% (characteristic life)
ref_y = np.log(-np.log(1 - 0.632))

# Tighter Y-axis range based on actual data spread
data_y_min = weibull_y[failure_mask].min()
data_y_max = weibull_y[failure_mask].max()
y_padding = (data_y_max - data_y_min) * 0.2
y_min = data_y_min - y_padding
y_max = data_y_max + y_padding

# X-axis domain (actual time values, log-scaled)
x_min = all_times.min() * 0.7
x_max = all_times.max() * 1.3

# Color palette
clr_failure = "#306998"
clr_censored = "#E8792B"
clr_fit = "#555555"
clr_ref = "#999999"
clr_bg = "#FAFBFC"

# Weibull probability labels for y-axis
prob_levels = np.array([0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.95, 0.99])
weibull_ticks = np.log(-np.log(1 - prob_levels))
prob_labels = ["1%", "5%", "10%", "20%", "50%", "63.2%", "90%", "95%", "99%"]
# Filter to only ticks within our y-axis range
mask_ticks = (weibull_ticks >= y_min) & (weibull_ticks <= y_max)
visible_ticks = weibull_ticks[mask_ticks]
visible_labels = [prob_labels[i] for i in range(len(prob_labels)) if mask_ticks[i]]

# Build Vega expression to map tick values to probability labels
label_cases = " : ".join(
    f"abs(datum.value - {val:.4f}) < 0.01 ? '{lbl}'" for val, lbl in zip(visible_ticks, visible_labels, strict=True)
)
y_label_expr = f"{label_cases} : ''"

# Shared axis encodings
x_enc = alt.X(
    "time:Q",
    scale=alt.Scale(type="log", domain=[x_min, x_max], nice=False),
    title="Time to Failure (hours)",
    axis=alt.Axis(format="~s"),
)
y_enc = alt.Y(
    "weibull_y:Q",
    scale=alt.Scale(domain=[y_min, y_max]),
    title="Cumulative Failure Probability",
    axis=alt.Axis(values=visible_ticks.tolist(), labelExpr=y_label_expr),
)
tooltip_enc = [
    alt.Tooltip("time:Q", title="Time (hrs)", format=",.0f"),
    alt.Tooltip("status:N", title="Status"),
    alt.Tooltip("weibull_y:Q", title="Weibull Y", format=".2f"),
]

# Failure points (filled circles)
failures_chart = (
    alt.Chart(df[df["status"] == "Failure"])
    .mark_point(size=220, filled=True, color=clr_failure, strokeWidth=1.5, stroke="white")
    .encode(x=x_enc, y=y_enc, tooltip=tooltip_enc)
)

# Censored points (open triangles) - reuse shared axis encodings
censored_chart = (
    alt.Chart(df[df["status"] == "Censored"])
    .mark_point(size=220, filled=False, shape="triangle-up", color=clr_censored, strokeWidth=2.5)
    .encode(x=x_enc, y=y_enc, tooltip=tooltip_enc)
)

# Legend layer using color+shape encoding on all data
legend_points = (
    alt.Chart(df)
    .mark_point(size=220, strokeWidth=2)
    .encode(
        x=alt.X("time:Q"),
        y=alt.Y("weibull_y:Q"),
        color=alt.Color(
            "status:N",
            scale=alt.Scale(domain=["Failure", "Censored"], range=[clr_failure, clr_censored]),
            legend=alt.Legend(title="Observation Type", symbolSize=200, labelFontSize=16, titleFontSize=18),
        ),
        shape=alt.Shape(
            "status:N", scale=alt.Scale(domain=["Failure", "Censored"], range=["circle", "triangle-up"]), legend=None
        ),
        opacity=alt.value(0),
    )
)

# Fitted line
fit_line = (
    alt.Chart(df_fit)
    .mark_line(strokeWidth=2.5, color=clr_fit, strokeDash=[10, 5])
    .encode(x=alt.X("time:Q", scale=alt.Scale(type="log")), y=alt.Y("weibull_y:Q"))
)

# Reference line at 63.2%
df_ref = pd.DataFrame({"weibull_y": [ref_y, ref_y], "time": [x_min, x_max]})

ref_line = (
    alt.Chart(df_ref)
    .mark_line(strokeWidth=1.5, color=clr_ref, strokeDash=[4, 4])
    .encode(x=alt.X("time:Q", scale=alt.Scale(type="log")), y=alt.Y("weibull_y:Q"))
)

# Annotation for parameters - positioned with generous whitespace
df_annotation = pd.DataFrame(
    {
        "time": [all_times.max() * 0.85],
        "weibull_y": [y_min + (y_max - y_min) * 0.10],
        "text": [f"\u03b2 = {beta_est:.2f}   \u03b7 = {eta_est:.0f} hrs"],
    }
)

param_text = (
    alt.Chart(df_annotation)
    .mark_text(fontSize=21, align="right", fontWeight="bold", color="#2C3E50")
    .encode(x=alt.X("time:Q", scale=alt.Scale(type="log")), y=alt.Y("weibull_y:Q"), text="text:N")
)

# 63.2% label
df_ref_label = pd.DataFrame(
    {"time": [x_min * 1.05], "weibull_y": [ref_y + 0.12], "text": ["63.2% Characteristic Life"]}
)

ref_label = (
    alt.Chart(df_ref_label)
    .mark_text(fontSize=16, align="left", color="#777777", fontStyle="italic")
    .encode(x=alt.X("time:Q", scale=alt.Scale(type="log")), y=alt.Y("weibull_y:Q"), text="text:N")
)

# Interactive selection highlight (added to failure layer only to avoid duplicate signal)
highlight = alt.selection_point(name="hover", on="pointerover", fields=["status"], empty=False)

failures_interactive = failures_chart.add_params(highlight).encode(
    size=alt.condition(highlight, alt.value(350), alt.value(220))
)

# Combine all layers
chart = (
    (ref_line + fit_line + failures_interactive + censored_chart + legend_points + param_text + ref_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "probability-weibull \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#2C3E50",
            subtitle="Turbine Blade Fatigue-Life Analysis  \u2014  Weibull Distribution Fit",
            subtitleFontSize=18,
            subtitleColor="#777777",
            subtitlePadding=8,
            anchor="start",
            offset=16,
        ),
    )
    .configure_axisX(
        labelFontSize=18,
        titleFontSize=22,
        grid=False,
        domainColor="#AAAAAA",
        tickColor="#AAAAAA",
        labelColor="#555555",
        titleColor="#333333",
        titlePadding=12,
    )
    .configure_axisY(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.2,
        gridDash=[3, 3],
        gridColor="#BBBBBB",
        domainColor="#AAAAAA",
        tickColor="#AAAAAA",
        labelColor="#555555",
        titleColor="#333333",
        titlePadding=12,
    )
    .configure_view(strokeWidth=0, fill=clr_bg)
    .configure_legend(
        orient="top-right",
        padding=18,
        cornerRadius=8,
        strokeColor="#CCCCCC",
        fillColor="white",
        labelFontSize=16,
        titleFontSize=18,
    )
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
