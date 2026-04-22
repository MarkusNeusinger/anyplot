""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_point,
    geom_ribbon,
    geom_step,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Simulated clinical trial survival data for two treatment groups
np.random.seed(42)

n_per_group = 80


def generate_survival_data(n, hazard_rate, group_name):
    """Generate survival data with exponential distribution."""
    times = np.random.exponential(scale=1 / hazard_rate, size=n)
    times = np.clip(times, 0, 36)  # Max follow-up 36 months
    censored = times >= 36
    times[censored] = 36
    event = (~censored).astype(int)
    # Add random censoring (20% of non-terminal events)
    random_censor = np.random.random(n) < 0.2
    event[random_censor] = 0
    return pd.DataFrame({"time": times, "event": event, "group": group_name})


# Treatment group (lower hazard = better survival)
treatment = generate_survival_data(n_per_group, hazard_rate=0.04, group_name="Treatment")
# Control group (higher hazard = worse survival)
control = generate_survival_data(n_per_group, hazard_rate=0.08, group_name="Control")
df = pd.concat([treatment, control], ignore_index=True)


# Kaplan-Meier estimator function
def kaplan_meier(time, event):
    """Compute Kaplan-Meier survival curve with confidence intervals."""
    df_km = pd.DataFrame({"time": time, "event": event}).sort_values("time")
    unique_times = np.sort(df_km["time"].unique())
    n_at_risk = len(df_km)
    survival = 1.0
    results = [{"time": 0, "survival": 1.0, "ci_lower": 1.0, "ci_upper": 1.0, "n_at_risk": n_at_risk}]
    var_sum = 0

    for t in unique_times:
        at_time = df_km[df_km["time"] == t]
        d = at_time["event"].sum()  # Number of events
        n = n_at_risk  # Number at risk
        if n > 0 and d > 0:
            survival *= 1 - d / n
            var_sum += d / (n * (n - d)) if n > d else 0
        # Greenwood's formula for variance
        se = survival * np.sqrt(var_sum) if var_sum > 0 else 0
        ci_lower = max(0, survival - 1.96 * se)
        ci_upper = min(1, survival + 1.96 * se)
        results.append({"time": t, "survival": survival, "ci_lower": ci_lower, "ci_upper": ci_upper, "n_at_risk": n})
        n_at_risk -= len(at_time)

    return pd.DataFrame(results)


# Compute Kaplan-Meier for each group
km_treatment = kaplan_meier(treatment["time"], treatment["event"])
km_treatment["group"] = "Treatment"
km_control = kaplan_meier(control["time"], control["event"])
km_control["group"] = "Control"
km_data = pd.concat([km_treatment, km_control], ignore_index=True)

# Find censored observations for tick marks
censored_treatment = treatment[treatment["event"] == 0].copy()
censored_control = control[control["event"] == 0].copy()


def get_survival_at_time(km_df, t):
    """Get survival probability at a given time."""
    km_df = km_df.sort_values("time")
    idx = km_df[km_df["time"] <= t].index
    if len(idx) == 0:
        return 1.0
    return km_df.loc[idx[-1], "survival"]


censored_treatment["survival"] = censored_treatment["time"].apply(lambda t: get_survival_at_time(km_treatment, t))
censored_treatment["group"] = "Treatment"
censored_control["survival"] = censored_control["time"].apply(lambda t: get_survival_at_time(km_control, t))
censored_control["group"] = "Control"
censored_data = pd.concat([censored_treatment, censored_control], ignore_index=True)

# Colors
colors = ["#306998", "#DC2626"]  # Python Blue for Treatment, Red for Control

# Plot
plot = (
    ggplot()
    # Confidence interval ribbons
    + geom_ribbon(aes(x="time", ymin="ci_lower", ymax="ci_upper", fill="group"), data=km_data, alpha=0.2)
    # Step functions for survival curves
    + geom_step(aes(x="time", y="survival", color="group"), data=km_data, size=1.5)
    # Censored observation tick marks
    + geom_point(
        aes(x="time", y="survival", color="group"),
        data=censored_data,
        shape=3,  # Plus sign for censoring ticks
        size=4,
        stroke=2,
    )
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(
        x="Time (months)",
        y="Survival Probability",
        title="survival-kaplan-meier · letsplot · pyplots.ai",
        color="Group",
        fill="Group",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
