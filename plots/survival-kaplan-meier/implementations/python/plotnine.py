""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_point,
    geom_ribbon,
    geom_step,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)


# Generate survival data for two treatment groups
def generate_survival_data(n, hazard_rate, group_name):
    """Generate time-to-event data with censoring."""
    # Exponential distribution for survival times
    times = np.random.exponential(1 / hazard_rate, n)
    # Random censoring (30% of observations)
    censor_times = np.random.uniform(0, np.percentile(times, 80), n)
    censored = times > censor_times
    observed_times = np.where(censored, censor_times, times)
    events = (~censored).astype(int)
    return pd.DataFrame({"time": observed_times, "event": events, "group": group_name})


# Create two groups with different hazard rates
group_a = generate_survival_data(80, hazard_rate=0.02, group_name="Treatment A")
group_b = generate_survival_data(80, hazard_rate=0.035, group_name="Treatment B")
data = pd.concat([group_a, group_b], ignore_index=True)


# Compute Kaplan-Meier survival estimates
def kaplan_meier(df):
    """Calculate Kaplan-Meier survival estimates with confidence intervals."""
    df = df.sort_values("time").reset_index(drop=True)
    n = len(df)
    times = [0]
    survival = [1.0]
    ci_lower = [1.0]
    ci_upper = [1.0]
    var_sum = 0  # For Greenwood's formula

    at_risk = n
    current_survival = 1.0

    # Process each unique event time
    unique_times = df[df["event"] == 1]["time"].unique()
    unique_times.sort()

    for t in unique_times:
        # Number at risk just before time t
        at_risk = (df["time"] >= t).sum()
        # Number of events at time t
        events = ((df["time"] == t) & (df["event"] == 1)).sum()

        if at_risk > 0:
            # Survival probability at this step
            current_survival *= (at_risk - events) / at_risk
            # Greenwood's formula for variance
            if at_risk > events:
                var_sum += events / (at_risk * (at_risk - events))

            times.append(t)
            survival.append(current_survival)

            # 95% confidence interval (log transformation)
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

    # Extend to max time
    max_time = df["time"].max()
    times.append(max_time)
    survival.append(survival[-1])
    ci_lower.append(ci_lower[-1])
    ci_upper.append(ci_upper[-1])

    return pd.DataFrame(
        {"time": times, "survival": survival, "ci_lower": np.clip(ci_lower, 0, 1), "ci_upper": np.clip(ci_upper, 0, 1)}
    )


# Calculate KM estimates for each group
km_a = kaplan_meier(data[data["group"] == "Treatment A"])
km_a["group"] = "Treatment A"

km_b = kaplan_meier(data[data["group"] == "Treatment B"])
km_b["group"] = "Treatment B"

km_data = pd.concat([km_a, km_b], ignore_index=True)

# Get censored observations for tick marks
censored = data[data["event"] == 0].copy()
# Add survival probability at censoring time for each censored observation
censored_marks = []
for _, row in censored.iterrows():
    group = row["group"]
    t = row["time"]
    km_group = km_a if group == "Treatment A" else km_b
    # Find survival at this time
    surv = km_group[km_group["time"] <= t]["survival"].iloc[-1]
    censored_marks.append({"time": t, "survival": surv, "group": group})

censored_df = pd.DataFrame(censored_marks)

# Define colors (Python Blue and a complementary color)
colors = {"Treatment A": "#306998", "Treatment B": "#FFD43B"}

# Create the plot
plot = (
    ggplot()
    # Confidence interval ribbons
    + geom_ribbon(km_data, aes(x="time", ymin="ci_lower", ymax="ci_upper", fill="group"), alpha=0.2)
    # Survival step curves
    + geom_step(km_data, aes(x="time", y="survival", color="group"), size=1.5)
    # Censored observation marks (vertical ticks)
    + geom_point(censored_df, aes(x="time", y="survival", color="group"), shape="|", size=4, stroke=1.5)
    # Colors
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    # Axis scales
    + scale_y_continuous(limits=(0, 1.05), breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"])
    + scale_x_continuous(limits=(0, None))
    # Labels
    + labs(
        title="survival-kaplan-meier · plotnine · pyplots.ai",
        x="Time (months)",
        y="Survival Probability",
        color="Treatment Group",
        fill="Treatment Group",
    )
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position=(0.85, 0.85),
        panel_grid_minor=element_line(alpha=0.2),
        panel_grid_major=element_line(alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
