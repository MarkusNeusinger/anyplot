""" pyplots.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure


# Data - Simulated clinical trial with two treatment groups
np.random.seed(42)

# Treatment group (new drug) - better survival
n_treatment = 80
treatment_times = np.random.exponential(scale=24, size=n_treatment)  # months
treatment_times = np.clip(treatment_times, 0.5, 36)  # max 36 months follow-up
treatment_censored = np.random.binomial(1, 0.35, n_treatment)  # 35% censored
treatment_events = 1 - treatment_censored

# Control group (standard care) - worse survival
n_control = 80
control_times = np.random.exponential(scale=16, size=n_control)  # months
control_times = np.clip(control_times, 0.5, 36)
control_censored = np.random.binomial(1, 0.3, n_control)  # 30% censored
control_events = 1 - control_censored


# Kaplan-Meier estimator function
def kaplan_meier(times, events):
    """Calculate Kaplan-Meier survival curve with confidence intervals."""
    # Sort by time
    order = np.argsort(times)
    times = times[order]
    events = events[order]

    # Get unique event times
    unique_times = np.unique(times[events == 1])

    survival = [1.0]
    time_points = [0.0]
    var_sum = 0
    ci_lower = [1.0]
    ci_upper = [1.0]
    censored_times = []
    censored_survival = []

    for t in unique_times:
        # Number at risk just before time t
        at_risk = np.sum(times >= t)
        # Number of events at time t
        d = np.sum((times == t) & (events == 1))

        if at_risk > 0:
            survival_prob = 1 - d / at_risk
            survival.append(survival[-1] * survival_prob)
            time_points.append(t)

            # Greenwood's formula for variance
            if at_risk > d:
                var_sum += d / (at_risk * (at_risk - d))

            # 95% CI using log transformation
            se = np.sqrt(var_sum) if var_sum > 0 else 0
            log_s = np.log(survival[-1]) if survival[-1] > 0 else -np.inf
            ci_factor = 1.96 * se / abs(log_s) if log_s != 0 else 0

            ci_lower.append(survival[-1] ** np.exp(ci_factor))
            ci_upper.append(survival[-1] ** np.exp(-ci_factor))

    # Get censored observation positions
    for t, e in zip(times, events, strict=True):
        if e == 0:  # censored
            # Find survival at this time
            idx = np.searchsorted(time_points[1:], t, side="right")
            if idx < len(survival):
                censored_times.append(t)
                censored_survival.append(survival[idx])

    return (
        np.array(time_points),
        np.array(survival),
        np.array(ci_lower),
        np.array(ci_upper),
        np.array(censored_times),
        np.array(censored_survival),
    )


# Calculate Kaplan-Meier estimates
t_time, t_surv, t_ci_low, t_ci_up, t_cens_t, t_cens_s = kaplan_meier(treatment_times, treatment_events)
c_time, c_surv, c_ci_low, c_ci_up, c_cens_t, c_cens_s = kaplan_meier(control_times, control_events)

# Calculate median survival (time when survival = 0.5)
treatment_median = t_time[np.searchsorted(-t_surv, -0.5)] if np.any(t_surv <= 0.5) else None
control_median = c_time[np.searchsorted(-c_surv, -0.5)] if np.any(c_surv <= 0.5) else None


# Create step function data for bokeh (duplicate points for steps)
def make_step_data(x, y):
    """Convert point data to step function format."""
    x_step = np.repeat(x, 2)[1:]
    y_step = np.repeat(y, 2)[:-1]
    return x_step, y_step


# Prepare step data
t_x_step, t_y_step = make_step_data(t_time, t_surv)
c_x_step, c_y_step = make_step_data(c_time, c_surv)

# Prepare CI bands (step function for shaded area)
t_ci_low_x, t_ci_low_y = make_step_data(t_time, t_ci_low)
t_ci_up_x, t_ci_up_y = make_step_data(t_time, t_ci_up)
c_ci_low_x, c_ci_low_y = make_step_data(c_time, c_ci_low)
c_ci_up_x, c_ci_up_y = make_step_data(c_time, c_ci_up)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="survival-kaplan-meier \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time (months)",
    y_axis_label="Survival Probability",
    x_range=(0, 38),
    y_range=(0, 1.05),
)

# Colors
treatment_color = "#306998"  # Python Blue
control_color = "#FFD43B"  # Python Yellow

# Plot confidence interval bands
treatment_ci_source = ColumnDataSource(
    data={"x": np.concatenate([t_ci_low_x, t_ci_up_x[::-1]]), "y": np.concatenate([t_ci_low_y, t_ci_up_y[::-1]])}
)
control_ci_source = ColumnDataSource(
    data={"x": np.concatenate([c_ci_low_x, c_ci_up_x[::-1]]), "y": np.concatenate([c_ci_low_y, c_ci_up_y[::-1]])}
)

p.patch(x="x", y="y", source=treatment_ci_source, fill_color=treatment_color, fill_alpha=0.2, line_alpha=0)
p.patch(x="x", y="y", source=control_ci_source, fill_color=control_color, fill_alpha=0.2, line_alpha=0)

# Plot survival curves (step functions)
treatment_line = p.line(
    x=t_x_step, y=t_y_step, line_color=treatment_color, line_width=4, legend_label="Treatment (n=80)"
)
control_line = p.line(x=c_x_step, y=c_y_step, line_color=control_color, line_width=4, legend_label="Control (n=80)")

# Plot censored observations as tick marks
if len(t_cens_t) > 0:
    p.scatter(
        x=t_cens_t,
        y=t_cens_s,
        marker="dash",
        size=20,
        angle=1.5708,  # vertical
        line_color=treatment_color,
        line_width=3,
    )
if len(c_cens_t) > 0:
    p.scatter(
        x=c_cens_t,
        y=c_cens_s,
        marker="dash",
        size=20,
        angle=1.5708,  # vertical
        line_color=control_color,
        line_width=3,
    )

# Add median survival line
median_line = Span(location=0.5, dimension="width", line_color="#888888", line_width=2, line_dash="dashed")
p.add_layout(median_line)

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend
p.legend.location = "bottom_left"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_alpha = 0

# Save
export_png(p, filename="plot.png")
