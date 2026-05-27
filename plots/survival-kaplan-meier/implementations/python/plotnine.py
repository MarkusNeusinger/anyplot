""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_ribbon,
    geom_step,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD"]

# Data generation
np.random.seed(42)


# Generate survival data for two treatment groups
def generate_times_and_events(n, hazard_rate):
    times = np.random.exponential(1 / hazard_rate, n)
    censor_times = np.random.uniform(0, np.percentile(times, 80), n)
    censored = times > censor_times
    observed_times = np.where(censored, censor_times, times)
    events = (~censored).astype(int)
    return observed_times, events


times_a, events_a = generate_times_and_events(80, 0.02)
times_b, events_b = generate_times_and_events(80, 0.035)

data = pd.concat(
    [
        pd.DataFrame({"time": times_a, "event": events_a, "group": "Treatment A"}),
        pd.DataFrame({"time": times_b, "event": events_b, "group": "Treatment B"}),
    ],
    ignore_index=True,
)


# Kaplan-Meier estimation
def compute_km(df):
    df = df.sort_values("time").reset_index(drop=True)
    n = len(df)
    times = [0]
    survival = [1.0]
    ci_lower = [1.0]
    ci_upper = [1.0]
    var_sum = 0

    at_risk = n
    current_survival = 1.0
    unique_times = df[df["event"] == 1]["time"].unique()
    unique_times.sort()

    for t in unique_times:
        at_risk = (df["time"] >= t).sum()
        events = ((df["time"] == t) & (df["event"] == 1)).sum()

        if at_risk > 0:
            current_survival *= (at_risk - events) / at_risk
            if at_risk > events:
                var_sum += events / (at_risk * (at_risk - events))

            times.append(t)
            survival.append(current_survival)

            if current_survival > 0 and var_sum > 0:
                se = current_survival * np.sqrt(var_sum)
                z = 1.96
                log_surv = np.log(current_survival)
                log_se = se / current_survival
                ci_lower.append(np.exp(log_surv - z * log_se))
                ci_upper.append(np.exp(log_surv + z * log_se))
            else:
                ci_lower.append(current_survival)
                ci_upper.append(current_survival)

    max_time = df["time"].max()
    times.append(max_time)
    survival.append(survival[-1])
    ci_lower.append(ci_lower[-1])
    ci_upper.append(ci_upper[-1])

    return pd.DataFrame(
        {"time": times, "survival": survival, "ci_lower": np.clip(ci_lower, 0, 1), "ci_upper": np.clip(ci_upper, 0, 1)}
    )


km_a = compute_km(data[data["group"] == "Treatment A"])
km_a["group"] = "Treatment A"

km_b = compute_km(data[data["group"] == "Treatment B"])
km_b["group"] = "Treatment B"

km_data = pd.concat([km_a, km_b], ignore_index=True)

# Get censored observations for tick marks
censored = data[data["event"] == 0].copy()
censored_marks = []
for _, row in censored.iterrows():
    group = row["group"]
    t = row["time"]
    km_group = km_a if group == "Treatment A" else km_b
    surv = km_group[km_group["time"] <= t]["survival"].iloc[-1]
    censored_marks.append({"time": t, "survival": surv, "group": group})

censored_df = pd.DataFrame(censored_marks)


# Compute median survival times for annotations
def get_median_survival(km_group):
    surv_below_half = km_group[km_group["survival"] <= 0.5]
    if len(surv_below_half) > 0:
        return surv_below_half.iloc[0]["time"]
    return None


median_a = get_median_survival(km_a)
median_b = get_median_survival(km_b)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
    panel_grid_minor=element_blank(),
    axis_ticks_y=element_line(color=INK_SOFT, size=0.3),
    axis_ticks_x=element_blank(),
    panel_border=element_blank(),
    axis_line_y=element_line(color=INK_SOFT, size=0.4),
    axis_line_x=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    plot_title=element_text(color=INK, size=24, face="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position=(0.70, 0.25),
    legend_box_just="left",
    figure_size=(16, 9),
)

plot = (
    ggplot()
    + geom_ribbon(km_data, aes(x="time", ymin="ci_lower", ymax="ci_upper", fill="group"), alpha=0.15)
    + geom_step(km_data, aes(x="time", y="survival", color="group"), size=1.5)
    + geom_point(censored_df, aes(x="time", y="survival", color="group"), shape="|", size=4)
)

if median_a is not None:
    plot = plot + geom_vline(xintercept=median_a, linetype="dashed", color=IMPRINT[0], alpha=0.4, size=0.8)

if median_b is not None:
    plot = plot + geom_vline(xintercept=median_b, linetype="dashed", color=IMPRINT[1], alpha=0.4, size=0.8)

plot = (
    plot
    + scale_color_manual(values=IMPRINT)
    + scale_fill_manual(values=IMPRINT)
    + scale_y_continuous(limits=(0, 1.05), breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"])
    + scale_x_continuous(limits=(0, None))
    + labs(
        title="survival-kaplan-meier · plotnine · anyplot.ai",
        x="Time (months)",
        y="Survival Probability",
        color="Treatment Group",
        fill="Treatment Group",
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
