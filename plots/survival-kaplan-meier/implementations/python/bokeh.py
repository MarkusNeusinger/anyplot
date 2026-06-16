""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

TREATMENT_COLOR = "#009E73"  # Okabe-Ito position 1 (brand green)
CONTROL_COLOR = "#C475FD"  # Okabe-Ito position 2 (vermillion)

# Data - Simulated clinical trial with two treatment groups
np.random.seed(42)

# Treatment group (new drug) - better survival
n_treatment = 80
treatment_times = np.random.exponential(scale=24, size=n_treatment)
treatment_times = np.clip(treatment_times, 0.5, 36)
treatment_censored = np.random.binomial(1, 0.35, n_treatment)
treatment_events = 1 - treatment_censored

# Control group (standard care) - worse survival
n_control = 80
control_times = np.random.exponential(scale=16, size=n_control)
control_times = np.clip(control_times, 0.5, 36)
control_censored = np.random.binomial(1, 0.3, n_control)
control_events = 1 - control_censored


# Calculate Kaplan-Meier estimator
def compute_km(times, events):
    """Compute Kaplan-Meier survival curve with 95% confidence intervals."""
    order = np.argsort(times)
    times = times[order]
    events = events[order]

    unique_event_times = np.unique(times[events == 1])

    survival = [1.0]
    time_points = [0.0]
    var_sum = 0
    ci_lower = [1.0]
    ci_upper = [1.0]
    censored_times = []
    censored_survival = []

    for t in unique_event_times:
        at_risk = np.sum(times >= t)
        d = np.sum((times == t) & (events == 1))

        if at_risk > 0:
            s_prob = 1 - d / at_risk
            survival.append(survival[-1] * s_prob)
            time_points.append(t)

            if at_risk > d:
                var_sum += d / (at_risk * (at_risk - d))

            se = np.sqrt(var_sum) if var_sum > 0 else 0
            log_s = np.log(survival[-1]) if survival[-1] > 0 else -np.inf
            ci_factor = 1.96 * se / abs(log_s) if log_s != 0 else 0

            ci_lower.append(survival[-1] ** np.exp(ci_factor))
            ci_upper.append(survival[-1] ** np.exp(-ci_factor))

    # Find censored observation positions
    for t, e in zip(times, events, strict=True):
        if e == 0:
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


t_time, t_surv, t_ci_low, t_ci_up, t_cens_t, t_cens_s = compute_km(treatment_times, treatment_events)
c_time, c_surv, c_ci_low, c_ci_up, c_cens_t, c_cens_s = compute_km(control_times, control_events)


# Convert to step functions
def to_steps(x, y):
    """Convert point data to step function."""
    x_step = np.repeat(x, 2)[1:]
    y_step = np.repeat(y, 2)[:-1]
    return x_step, y_step


t_x_step, t_y_step = to_steps(t_time, t_surv)
c_x_step, c_y_step = to_steps(c_time, c_surv)

t_ci_low_x, t_ci_low_y = to_steps(t_time, t_ci_low)
t_ci_up_x, t_ci_up_y = to_steps(t_time, t_ci_up)
c_ci_low_x, c_ci_low_y = to_steps(c_time, c_ci_low)
c_ci_up_x, c_ci_up_y = to_steps(c_time, c_ci_up)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="survival-kaplan-meier · bokeh · anyplot.ai",
    x_axis_label="Time (months)",
    y_axis_label="Survival Probability",
    x_range=(0, 38),
    y_range=(0, 1.05),
)

# Plot confidence interval bands
treatment_ci = ColumnDataSource(
    data={"x": np.concatenate([t_ci_low_x, t_ci_up_x[::-1]]), "y": np.concatenate([t_ci_low_y, t_ci_up_y[::-1]])}
)
control_ci = ColumnDataSource(
    data={"x": np.concatenate([c_ci_low_x, c_ci_up_x[::-1]]), "y": np.concatenate([c_ci_low_y, c_ci_up_y[::-1]])}
)

p.patch(x="x", y="y", source=treatment_ci, fill_color=TREATMENT_COLOR, fill_alpha=0.15, line_alpha=0)
p.patch(x="x", y="y", source=control_ci, fill_color=CONTROL_COLOR, fill_alpha=0.15, line_alpha=0)

# Plot survival curves
p.line(x=t_x_step, y=t_y_step, line_color=TREATMENT_COLOR, line_width=4, legend_label="Treatment (n=80)")
p.line(x=c_x_step, y=c_y_step, line_color=CONTROL_COLOR, line_width=4, legend_label="Control (n=80)")

# Plot censored observations as tick marks
if len(t_cens_t) > 0:
    p.scatter(x=t_cens_t, y=t_cens_s, marker="dash", size=28, angle=1.5708, line_color=TREATMENT_COLOR, line_width=4)
if len(c_cens_t) > 0:
    p.scatter(x=c_cens_t, y=c_cens_s, marker="dash", size=28, angle=1.5708, line_color=CONTROL_COLOR, line_width=4)

# Add median survival reference line
median_line = Span(location=0.5, dimension="width", line_color=INK_SOFT, line_width=3, line_dash="dashed")
p.add_layout(median_line)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"

p.xaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT

p.yaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "bottom_left"
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Save
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
