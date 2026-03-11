""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_shape_manual,
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

# Fitted line data with confidence band
log_time_range = np.linspace(np.log(df["time"].min() * 0.7), np.log(df["time"].max() * 1.3), 200)
fitted_y = beta * log_time_range + intercept

# Confidence band via prediction interval
n_fit = len(failures_df)
x_mean = failures_df["log_time"].mean()
x_ss = ((failures_df["log_time"] - x_mean) ** 2).sum()
residuals = failures_df["weibull_y"] - (beta * failures_df["log_time"] + intercept)
mse = (residuals**2).sum() / (n_fit - 2)
se_pred = np.sqrt(mse * (1 + 1 / n_fit + (log_time_range - x_mean) ** 2 / x_ss))
t_crit = stats.t.ppf(0.975, n_fit - 2)

fit_df = pd.DataFrame(
    {
        "log_time": log_time_range,
        "weibull_y": fitted_y,
        "ymin": fitted_y - t_crit * se_pred,
        "ymax": fitted_y + t_crit * se_pred,
        "time": np.exp(log_time_range),
    }
)

# Weibull y-axis: reference probabilities and their transformed values
prob_levels = np.array([0.01, 0.05, 0.10, 0.20, 0.40, 0.632, 0.80, 0.90, 0.99])
weibull_ticks = np.log(-np.log(1 - prob_levels))
prob_labels = [f"{p * 100:.1f}%" for p in prob_levels]
prob_labels = [lbl.replace(".0%", "%") for lbl in prob_labels]

# X-axis tick values (log-spaced)
x_tick_values = [1000, 2000, 3000, 5000, 7000, 10000]
log_x_ticks = [np.log(v) for v in x_tick_values]
x_labels = [f"{v:,}" for v in x_tick_values]

# Reference line at 63.2%
ref_y = np.log(-np.log(1 - 0.632))

# Characteristic life intersection point
char_life_x = np.log(eta)

# Prepare scatter data with aes-mapped legend
failures_plot = failures_df[["log_time", "weibull_y"]].copy()
failures_plot["Status"] = "Failure"
failures_plot["point_size"] = "data"

censored_plot = df[df["status"] == "Censored"][["log_time"]].copy()
censored_y_pos = weibull_ticks[0] + 0.15
censored_plot["weibull_y"] = censored_y_pos
censored_plot["Status"] = "Censored"
censored_plot["point_size"] = "data"

scatter_df = pd.concat([failures_plot, censored_plot], ignore_index=True)

# Highlight marker dataframe
highlight_df = pd.DataFrame(
    {"log_time": [char_life_x], "weibull_y": [ref_y], "Status": ["Highlight"], "point_size": ["highlight"]}
)

# Position annotation well above and right of the data cluster
annot_x = char_life_x + 0.35
annot_y = ref_y + 0.85

# Plot
plot = (
    ggplot()
    # Confidence band
    + geom_ribbon(fit_df, aes(x="log_time", ymin="ymin", ymax="ymax"), fill="#306998", alpha=0.10)
    # Fitted line
    + geom_line(fit_df, aes(x="log_time", y="weibull_y"), color="#306998", size=2.0, alpha=0.85)
    # 63.2% horizontal reference line
    + geom_segment(
        aes(x=log_x_ticks[0] - 0.1, xend=char_life_x, y=ref_y, yend=ref_y),
        linetype="dashed",
        color="#999999",
        size=0.6,
        alpha=0.6,
    )
    # Vertical drop from characteristic life to x-axis
    + geom_segment(
        aes(x=char_life_x, xend=char_life_x, y=weibull_ticks[0], yend=ref_y),
        linetype="dashed",
        color="#999999",
        size=0.6,
        alpha=0.6,
    )
    # Data points with aes-mapped legend
    + geom_point(
        scatter_df, aes(x="log_time", y="weibull_y", color="Status", shape="Status"), size=5, alpha=0.88, stroke=0.6
    )
    # Characteristic life intersection marker
    + geom_point(
        highlight_df,
        aes(x="log_time", y="weibull_y"),
        color="#C44E52",
        fill="#C44E52",
        size=8,
        shape="D",
        alpha=0.95,
        show_legend=False,
    )
    # Annotation: characteristic life — positioned well above data cluster
    + annotate(
        "text",
        x=annot_x,
        y=annot_y,
        label=f"\u03b7 = {eta:,.0f} hrs (63.2%)",
        size=12,
        ha="left",
        color="#C44E52",
        fontweight="bold",
        fontstyle="italic",
    )
    # Annotation connector: thin line from annotation down to diamond
    + geom_segment(
        aes(x=annot_x - 0.02, xend=char_life_x + 0.03, y=annot_y - 0.12, yend=ref_y + 0.06),
        color="#C44E52",
        size=0.4,
        alpha=0.5,
    )
    # Parameter annotation — upper left with background context
    + annotate(
        "text",
        x=log_x_ticks[0] + 0.05,
        y=weibull_ticks[-2] + 0.35,
        label=f"\u03b2 = {beta:.2f}  \u00b7  \u03b7 = {eta:,.0f} hrs  \u00b7  R\u00b2 = {r_value**2:.3f}",
        size=13,
        ha="left",
        va="top",
        color="#2B5B84",
        fontweight="bold",
    )
    # Subtitle annotation for context
    + annotate(
        "text",
        x=(log_x_ticks[0] + log_x_ticks[-1]) / 2,
        y=weibull_ticks[-1] + 0.65,
        label="Turbine blade fatigue-life analysis  \u2014  25 failures, 7 censored observations",
        size=11,
        ha="center",
        color="#777777",
        fontstyle="italic",
    )
    # Scales with aes mapping for legend
    + scale_color_manual(
        values={"Failure": "#306998", "Censored": "#E06C3A"}, name="Observation", limits=["Failure", "Censored"]
    )
    + scale_shape_manual(values={"Failure": "o", "Censored": "^"}, name="Observation", limits=["Failure", "Censored"])
    + scale_fill_manual(
        values={"Failure": "#306998", "Censored": "#E06C3A"}, name="Observation", limits=["Failure", "Censored"]
    )
    + scale_x_continuous(breaks=log_x_ticks, labels=x_labels)
    + scale_y_continuous(breaks=weibull_ticks.tolist(), labels=prob_labels)
    + guides(color=guide_legend(override_aes={"size": 6, "alpha": 1}))
    + labs(
        x="Time to Failure (hours)",
        y="Cumulative Failure Probability",
        title="probability-weibull \u00b7 plotnine \u00b7 pyplots.ai",
    )
    + theme_minimal(base_family="sans-serif")
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#2B2B2B", margin={"b": 4}),
        axis_title_x=element_text(size=20, color="#3A3A3A", margin={"t": 14}),
        axis_title_y=element_text(size=20, color="#3A3A3A", margin={"r": 14}),
        axis_text_x=element_text(size=16, color="#555555"),
        axis_text_y=element_text(size=16, color="#555555"),
        panel_grid_major_x=element_line(color="#E8E8E8", size=0.3, alpha=0.5),
        panel_grid_major_y=element_line(color="#DCDCDC", size=0.35, alpha=0.6),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FAFBFC", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        legend_title=element_text(size=16, weight="bold", color="#3A3A3A"),
        legend_text=element_text(size=14, color="#555555"),
        legend_position="right",
        legend_background=element_rect(fill="#FFFFFF", color="#E0E0E0", size=0.3),
        legend_key=element_rect(fill="none", color="none"),
        axis_ticks=element_line(color="#CCCCCC", size=0.3),
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
