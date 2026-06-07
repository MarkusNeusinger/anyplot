""" anyplot.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-07
"""

import os
import sys

import numpy as np
import pandas as pd


# Work around naming conflict between plotnine.py script and plotnine package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

from plotnine import (  # noqa: E402
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
    scale_x_log10,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — canonical hybrid-v3 order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
FIT_COLOR = IMPRINT_PALETTE[2]  # blue — Weibull regression line & band
CHAR_COLOR = IMPRINT_PALETTE[4]  # matte red — characteristic life focal point

# Data — turbine blade fatigue-life: 25 failures + 7 censored
np.random.seed(42)
n_failures = 25
n_censored = 7

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

df = pd.DataFrame({"time": all_times, "weibull_y": weibull_y, "status": np.where(is_failure, "Failure", "Censored")})

# Weibull regression on ln(time) vs ln(-ln(1-F))
failures_df = df[df["status"] == "Failure"].dropna()
log_times = np.log(failures_df["time"].values)
slope, intercept, r_value, _, _ = stats.linregress(log_times, failures_df["weibull_y"].values)
beta = slope
eta = np.exp(-intercept / beta)

# Fitted line and 95% prediction band (in raw time units for scale_x_log10)
log_time_range = np.linspace(np.log(all_times.min() * 0.7), np.log(all_times.max() * 1.3), 200)
fitted_y = beta * log_time_range + intercept

n_fit = len(failures_df)
x_mean = log_times.mean()
x_ss = ((log_times - x_mean) ** 2).sum()
residuals = failures_df["weibull_y"].values - (beta * log_times + intercept)
mse = (residuals**2).sum() / (n_fit - 2)
se_pred = np.sqrt(mse * (1 + 1 / n_fit + (log_time_range - x_mean) ** 2 / x_ss))
t_crit = stats.t.ppf(0.975, n_fit - 2)

fit_df = pd.DataFrame(
    {
        "time": np.exp(log_time_range),
        "weibull_y": fitted_y,
        "ymin": fitted_y - t_crit * se_pred,
        "ymax": fitted_y + t_crit * se_pred,
    }
)

# Y-axis: Weibull probability scale (linearised CDF)
prob_levels = np.array([0.01, 0.05, 0.10, 0.20, 0.40, 0.632, 0.80, 0.90, 0.99])
weibull_ticks = np.log(-np.log(1 - prob_levels))
prob_labels = [f"{p * 100:.1f}%".replace(".0%", "%") for p in prob_levels]

# X-axis breaks (raw time, scale_x_log10 handles the transform)
x_tick_values = [1000, 2000, 3000, 5000, 7000, 10000]
x_labels = [f"{v:,}" for v in x_tick_values]

# Reference values
ref_y = np.log(-np.log(1 - 0.632))  # ≈ 0: characteristic life on Weibull y-scale

# Scatter dataframes (raw time units)
failures_plot = failures_df[["time", "weibull_y"]].assign(Status="Failure")
censored_plot = df[df["status"] == "Censored"][["time"]].assign(weibull_y=weibull_ticks[0] + 0.18, Status="Censored")
scatter_df = pd.concat([failures_plot, censored_plot], ignore_index=True)

highlight_df = pd.DataFrame({"time": [eta], "weibull_y": [ref_y]})

# Annotation positions in data space (time units for x; Weibull-y for y)
annot_time = eta * 1.30
annot_y = ref_y + 0.62

plot = (
    ggplot()
    # 95% prediction band
    + geom_ribbon(fit_df, aes(x="time", ymin="ymin", ymax="ymax"), fill=FIT_COLOR, alpha=0.12)
    # Weibull regression line
    + geom_line(fit_df, aes(x="time", y="weibull_y"), color=FIT_COLOR, size=0.9, alpha=0.85)
    # 63.2% horizontal reference (dashed guide)
    + geom_segment(
        aes(x=x_tick_values[0] * 0.75, xend=eta, y=ref_y, yend=ref_y),
        linetype="dashed",
        color=INK_MUTED,
        size=0.35,
        alpha=0.65,
    )
    # Vertical drop guide to x-axis
    + geom_segment(
        aes(x=eta, xend=eta, y=weibull_ticks[0] - 0.1, yend=ref_y),
        linetype="dashed",
        color=INK_MUTED,
        size=0.35,
        alpha=0.65,
    )
    # Failure and censored data points
    + geom_point(
        scatter_df, aes(x="time", y="weibull_y", color="Status", shape="Status"), size=2.8, alpha=0.82, stroke=0.3
    )
    # Characteristic life diamond marker
    + geom_point(
        highlight_df,
        aes(x="time", y="weibull_y"),
        color=CHAR_COLOR,
        fill=CHAR_COLOR,
        size=4.5,
        shape="D",
        alpha=0.95,
        show_legend=False,
    )
    # Eta annotation label
    + annotate(
        "text",
        x=annot_time,
        y=annot_y,
        label=f"η = {eta:,.0f} hrs (63.2%)",
        size=3.0,
        ha="left",
        color=CHAR_COLOR,
        fontweight="bold",
        fontstyle="italic",
    )
    # Thin connector from annotation to diamond
    + geom_segment(
        aes(x=annot_time * 0.98, xend=eta * 1.02, y=annot_y - 0.10, yend=ref_y + 0.05),
        color=CHAR_COLOR,
        size=0.28,
        alpha=0.50,
    )
    # Weibull parameters summary (upper-left)
    + annotate(
        "text",
        x=x_tick_values[0] * 1.06,
        y=weibull_ticks[-2] + 0.22,
        label=f"β = {beta:.2f}  ·  η = {eta:,.0f} hrs  ·  R² = {r_value**2:.3f}",
        size=3.0,
        ha="left",
        va="top",
        color=FIT_COLOR,
        fontweight="bold",
    )
    # Scales — Imprint palette: failures=green (first), censored=lavender (second)
    + scale_color_manual(
        values={"Failure": IMPRINT_PALETTE[0], "Censored": IMPRINT_PALETTE[1]},
        name="Observation",
        limits=["Failure", "Censored"],
    )
    + scale_shape_manual(values={"Failure": "o", "Censored": "^"}, name="Observation", limits=["Failure", "Censored"])
    + scale_fill_manual(
        values={"Failure": IMPRINT_PALETTE[0], "Censored": IMPRINT_PALETTE[1]},
        name="Observation",
        limits=["Failure", "Censored"],
    )
    # scale_x_log10: idiomatic plotnine/ggplot2 log axis (no manual ln transform needed)
    + scale_x_log10(breaks=x_tick_values, labels=x_labels)
    + scale_y_continuous(breaks=weibull_ticks.tolist(), labels=prob_labels)
    + guides(color=guide_legend(override_aes={"size": 3.5, "alpha": 1}))
    + labs(
        x="Time to Failure (hours)",
        y="Cumulative Failure Probability",
        title="probability-weibull · plotnine · anyplot.ai",
        caption="Turbine blade fatigue-life — 25 failures, 7 censored observations",
    )
    + theme_minimal(base_family="sans-serif")
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 4}),
        plot_caption=element_text(size=7.5, color=INK_MUTED, fontstyle="italic", ha="center"),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 8}),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 8}),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        panel_grid_major_x=element_line(color=INK, size=0.2, alpha=0.12),
        panel_grid_major_y=element_line(color=INK, size=0.2, alpha=0.12),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_rect(fill="none", color="none"),
        axis_ticks=element_line(color=INK_SOFT, size=0.2),
        plot_margin=0.04,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
