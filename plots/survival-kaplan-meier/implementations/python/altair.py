""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Clinical trial with two treatment groups
np.random.seed(42)

# Generate survival data for two groups
n_per_group = 80

# Treatment A (better survival)
time_a = np.random.exponential(scale=24, size=n_per_group)
time_a = np.clip(time_a, 1, 36)  # Follow-up period: 36 months
event_a = np.random.binomial(1, 0.65, size=n_per_group)  # 65% event rate

# Treatment B (standard)
time_b = np.random.exponential(scale=16, size=n_per_group)
time_b = np.clip(time_b, 1, 36)
event_b = np.random.binomial(1, 0.75, size=n_per_group)  # 75% event rate

# Combine into dataframe
df = pd.DataFrame(
    {
        "time": np.concatenate([time_a, time_b]),
        "event": np.concatenate([event_a, event_b]),
        "group": ["Treatment A"] * n_per_group + ["Treatment B"] * n_per_group,
    }
)


# Kaplan-Meier estimator function
def kaplan_meier(time, event):
    """Calculate Kaplan-Meier survival estimates with confidence intervals."""
    # Sort by time
    order = np.argsort(time)
    time = time[order]
    event = event[order]

    # Get unique event times
    unique_times = np.unique(time[event == 1])

    # Calculate survival at each time point
    survival = 1.0
    times = [0]
    survivals = [1.0]
    ci_lower = [1.0]
    ci_upper = [1.0]
    var_sum = 0

    for t in unique_times:
        at_risk = np.sum(time >= t)
        events = np.sum((time == t) & (event == 1))

        if at_risk > 0:
            survival *= (at_risk - events) / at_risk
            # Greenwood's formula for variance
            if at_risk > events:
                var_sum += events / (at_risk * (at_risk - events))

        times.append(t)
        survivals.append(survival)

        # 95% confidence interval using log transformation
        se = survival * np.sqrt(var_sum) if var_sum > 0 else 0
        ci_lower.append(max(0, survival - 1.96 * se))
        ci_upper.append(min(1, survival + 1.96 * se))

    # Extend to max time
    max_time = time.max()
    times.append(max_time)
    survivals.append(survival)
    ci_lower.append(ci_lower[-1])
    ci_upper.append(ci_upper[-1])

    return np.array(times), np.array(survivals), np.array(ci_lower), np.array(ci_upper)


# Calculate KM estimates for each group
km_data = []
for group_name in ["Treatment A", "Treatment B"]:
    mask = df["group"] == group_name
    times, survivals, ci_low, ci_high = kaplan_meier(df.loc[mask, "time"].values, df.loc[mask, "event"].values)

    for i in range(len(times)):
        km_data.append(
            {
                "Time (Months)": times[i],
                "Survival Probability": survivals[i],
                "CI Lower": ci_low[i],
                "CI Upper": ci_high[i],
                "Group": group_name,
            }
        )

km_df = pd.DataFrame(km_data)

# Get censored observations for tick marks
censored = df[df["event"] == 0].copy()
censored_marks = []
for _, row in censored.iterrows():
    mask = (km_df["Group"] == row["group"]) & (km_df["Time (Months)"] <= row["time"])
    if mask.any():
        surv_at_censor = km_df.loc[mask, "Survival Probability"].iloc[-1]
        censored_marks.append(
            {"Time (Months)": row["time"], "Survival Probability": surv_at_censor, "Group": row["group"]}
        )

censored_df = pd.DataFrame(censored_marks)

# Define colors
color_scale = alt.Scale(domain=["Treatment A", "Treatment B"], range=["#306998", "#FFD43B"])

# Step line for survival curves (with legend)
survival_line = (
    alt.Chart(km_df)
    .mark_line(interpolate="step-after", strokeWidth=4)
    .encode(
        x=alt.X("Time (Months):Q", scale=alt.Scale(domain=[0, 38]), title="Time (Months)"),
        y=alt.Y("Survival Probability:Q", scale=alt.Scale(domain=[0, 1.05]), title="Survival Probability"),
        color=alt.Color("Group:N", scale=color_scale),
    )
)

# Confidence interval bands
ci_band = (
    alt.Chart(km_df)
    .mark_area(interpolate="step-after", opacity=0.25)
    .encode(
        x=alt.X("Time (Months):Q"),
        y=alt.Y("CI Lower:Q", title=""),
        y2=alt.Y2("CI Upper:Q"),
        color=alt.Color("Group:N", scale=color_scale, legend=None),
    )
)

# Censored observation marks
censor_marks = (
    alt.Chart(censored_df)
    .mark_tick(thickness=3, size=25)
    .encode(
        x=alt.X("Time (Months):Q"),
        y=alt.Y("Survival Probability:Q", title=""),
        color=alt.Color("Group:N", scale=color_scale, legend=None),
    )
)

# Combine layers using + operator and resolve legend
chart = (
    (ci_band + survival_line + censor_marks)
    .resolve_legend(color="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title("survival-kaplan-meier · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=20, labelFontSize=18, symbolStrokeWidth=4)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
