""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

# Data - Turbine blade fatigue-life (hours) with failures and suspensions
np.random.seed(42)
shape_param = 2.5  # beta (shape)
scale_param = 5000  # eta (scale / characteristic life)
n_failures = 25
n_censored = 5

failure_times = np.sort(stats.weibull_min.rvs(shape_param, scale=scale_param, size=n_failures))
censored_times = np.sort(np.random.uniform(1000, 4500, size=n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_failure = np.concatenate([np.ones(n_failures), np.zeros(n_censored)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_failure = is_failure[sort_idx]

# Median rank plotting positions for failures only (Bernard's approximation)
failure_rank = np.cumsum(is_failure)
n_total = len(all_times)
median_ranks = (failure_rank - 0.3) / (n_total + 0.4)

# Weibull linearization: y = ln(-ln(1 - F))
weibull_y = np.log(-np.log(1 - median_ranks))
log_times = np.log(all_times)

# Single dataframe with status column for legend mapping
df_all = pd.DataFrame(
    {"log_time": log_times, "weibull_y": weibull_y, "status": np.where(is_failure == 1, "Failure", "Censored")}
)

df_failures = df_all[df_all["status"] == "Failure"].copy()

# Fit line through failure points only
slope, intercept, r_value, _, _ = stats.linregress(df_failures["log_time"], df_failures["weibull_y"])

# Weibull parameters from fit: beta = slope, eta = exp(-intercept/slope)
beta_fit = slope
eta_fit = np.exp(-intercept / slope)

# Fitted line data
fit_x = np.linspace(np.log(np.min(all_times) * 0.7), np.log(np.max(all_times) * 1.3), 100)
fit_y = slope * fit_x + intercept
df_fit = pd.DataFrame({"log_time": fit_x, "weibull_y": fit_y})

# 63.2% reference line (characteristic life)
ref_y = np.log(-np.log(1 - 0.632))
log_eta = np.log(eta_fit)

# Y-axis tick positions and labels (cumulative probability)
prob_levels = [0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.99]
y_ticks = [np.log(-np.log(1 - p)) for p in prob_levels]
y_labels = [f"{p * 100:.1f}%" if p == 0.632 else f"{p * 100:.0f}%" for p in prob_levels]

# X-axis tick positions (log scale, labeled as original hours)
x_tick_vals = [np.log(v) for v in [500, 1000, 2000, 3000, 5000, 8000]]
x_tick_labels = ["500", "1,000", "2,000", "3,000", "5,000", "8,000"]

# Color palette - colorblind-safe (blue + amber, shape redundancy)
color_failure = "#0077B6"
color_censored = "#E69F00"
color_fit = "#023E8A"
color_ref = "#6C757D"
color_eta = "#D62828"

# Annotation text
annotation_label = f"\u03b2 = {beta_fit:.2f}\n\u03b7 = {eta_fit:.0f} hrs\nR\u00b2 = {r_value**2:.4f}"

# Crosshair segments at characteristic life intersection
df_h_seg = pd.DataFrame({"x": [log_eta - 0.35], "xend": [log_eta + 0.35], "y": [ref_y], "yend": [ref_y]})
df_v_seg = pd.DataFrame({"x": [log_eta], "xend": [log_eta], "y": [ref_y - 0.25], "yend": [ref_y + 0.25]})

# Plot using single dataframe with mapped aesthetics for automatic legend
plot = (
    ggplot(df_all, aes(x="log_time", y="weibull_y", color="status", shape="status"))  # noqa: F405
    # Fitted regression line (no legend)
    + geom_line(  # noqa: F405
        data=df_fit,
        mapping=aes(x="log_time", y="weibull_y"),  # noqa: F405
        color=color_fit,
        size=1.8,
        alpha=0.65,
        inherit_aes=False,
    )
    # 63.2% horizontal reference
    + geom_hline(  # noqa: F405
        yintercept=ref_y, linetype="dashed", color=color_ref, size=0.7
    )
    # Vertical reference at eta (characteristic life)
    + geom_vline(  # noqa: F405
        xintercept=log_eta, linetype="dotted", color=color_ref, size=0.7
    )
    # Crosshair emphasis at characteristic life intersection
    + geom_segment(  # noqa: F405
        data=df_h_seg,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color=color_eta,
        size=1.8,
        alpha=0.6,
        inherit_aes=False,
    )
    + geom_segment(  # noqa: F405
        data=df_v_seg,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color=color_eta,
        size=1.8,
        alpha=0.6,
        inherit_aes=False,
    )
    # Data points with legend via mapped color + shape
    + geom_point(size=7, alpha=0.9, stroke=1.5)  # noqa: F405
    # Characteristic life intersection marker (diamond)
    + geom_point(  # noqa: F405
        data=pd.DataFrame({"x": [log_eta], "y": [ref_y]}),
        mapping=aes(x="x", y="y"),  # noqa: F405
        color=color_eta,
        fill=color_eta,
        size=9,
        shape=18,
        alpha=0.9,
        inherit_aes=False,
    )
    # Parameter annotations
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"x": [max(fit_x) - 0.6], "y": [min(fit_y) + 0.6], "label": [annotation_label]}),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=14,
        color="#1A1A2E",
        hjust=1,
        fontface="bold",
        inherit_aes=False,
    )
    # Characteristic life label
    + geom_text(  # noqa: F405
        data=pd.DataFrame(
            {
                "x": [log_eta + 0.08],
                "y": [ref_y + 0.22],
                "label": [f"\u03b7 = {eta_fit:.0f} hrs\n63.2% Characteristic Life"],
            }
        ),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=11,
        color=color_eta,
        hjust=0,
        fontface="bold",
        inherit_aes=False,
    )
    # Manual color and shape scales for legend (colorblind-safe)
    + scale_color_manual(  # noqa: F405
        name="Observation", values={"Failure": color_failure, "Censored": color_censored}
    )
    + scale_shape_manual(  # noqa: F405
        name="Observation", values={"Failure": 16, "Censored": 1}
    )
    + scale_x_continuous(  # noqa: F405
        breaks=x_tick_vals, labels=x_tick_labels
    )
    + scale_y_continuous(  # noqa: F405
        breaks=y_ticks, labels=y_labels
    )
    + labs(  # noqa: F405
        x="Time to Failure (hours)",
        y="Cumulative Failure Probability",
        title="probability-weibull \u00b7 letsplot \u00b7 pyplots.ai",
    )
    + ggsize(1600, 900)  # noqa: F405
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#2B2D42"),  # noqa: F405
        axis_title=element_text(size=20, color="#2B2D42", face="bold"),  # noqa: F405
        plot_title=element_text(size=24, color="#1A1A2E", face="bold"),  # noqa: F405
        legend_title=element_text(size=16, face="bold"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_position=[0.15, 0.85],
        panel_grid_major=element_line(color="#DEE2E6", size=0.4, linetype="dashed"),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
