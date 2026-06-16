""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os
import sys


# Fix import issue: remove script directory from path before importing plotly
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.getcwd()

if _script_dir in sys.path:
    sys.path.remove(_script_dir)
if "" in sys.path:
    sys.path.remove("")

import numpy as np
import plotly.graph_objects as go


# Ensure we save to the script's directory
SCRIPT_DIR = _script_dir if "_script_dir" in locals() else os.path.dirname(os.path.abspath(__file__))


def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
COLOR_A = "#009E73"  # First series (bluish green)
COLOR_B = "#C475FD"  # Second series (vermillion)

# Data - Clinical trial with two treatment groups
np.random.seed(42)

# Treatment A (experimental drug) - better survival
n_a = 80
time_a = np.random.exponential(scale=24, size=n_a)
time_a = np.clip(time_a, 1, 48)
event_a = np.random.binomial(1, 0.7, size=n_a)
censored_idx = time_a > 36
event_a[censored_idx] = 0

# Treatment B (standard care) - worse survival
n_b = 80
time_b = np.random.exponential(scale=16, size=n_b)
time_b = np.clip(time_b, 1, 48)
event_b = np.random.binomial(1, 0.8, size=n_b)
censored_idx = time_b > 36
event_b[censored_idx] = 0

# Kaplan-Meier estimator for Treatment A
order_a = np.argsort(time_a)
time_a_sorted = time_a[order_a]
event_a_sorted = event_a[order_a]
unique_times_a = np.unique(time_a_sorted[event_a_sorted == 1])

km_times_a = []
km_survival_a = []
km_ci_lower_a = []
km_ci_upper_a = []
S_a = 1.0
var_sum_a = 0.0

for t in unique_times_a:
    at_risk = np.sum(time_a_sorted >= t)
    events = np.sum((time_a_sorted == t) & (event_a_sorted == 1))
    if at_risk > 0:
        S_a = S_a * (1 - events / at_risk)
        if at_risk > events:
            var_sum_a += events / (at_risk * (at_risk - events))
        if S_a > 0 and S_a < 1 and var_sum_a > 0:
            se_log = np.sqrt(var_sum_a) / abs(np.log(S_a))
            lower = S_a ** np.exp(1.96 * se_log)
            upper = S_a ** np.exp(-1.96 * se_log)
        else:
            lower = max(0, S_a - 0.1)
            upper = min(1, S_a + 0.1)
        km_times_a.append(t)
        km_survival_a.append(S_a)
        km_ci_lower_a.append(max(0, lower))
        km_ci_upper_a.append(min(1, upper))

km_times_a = np.array(km_times_a)
km_survival_a = np.array(km_survival_a)
km_ci_lower_a = np.array(km_ci_lower_a)
km_ci_upper_a = np.array(km_ci_upper_a)

# Kaplan-Meier estimator for Treatment B
order_b = np.argsort(time_b)
time_b_sorted = time_b[order_b]
event_b_sorted = event_b[order_b]
unique_times_b = np.unique(time_b_sorted[event_b_sorted == 1])

km_times_b = []
km_survival_b = []
km_ci_lower_b = []
km_ci_upper_b = []
S_b = 1.0
var_sum_b = 0.0

for t in unique_times_b:
    at_risk = np.sum(time_b_sorted >= t)
    events = np.sum((time_b_sorted == t) & (event_b_sorted == 1))
    if at_risk > 0:
        S_b = S_b * (1 - events / at_risk)
        if at_risk > events:
            var_sum_b += events / (at_risk * (at_risk - events))
        if S_b > 0 and S_b < 1 and var_sum_b > 0:
            se_log = np.sqrt(var_sum_b) / abs(np.log(S_b))
            lower = S_b ** np.exp(1.96 * se_log)
            upper = S_b ** np.exp(-1.96 * se_log)
        else:
            lower = max(0, S_b - 0.1)
            upper = min(1, S_b + 0.1)
        km_times_b.append(t)
        km_survival_b.append(S_b)
        km_ci_lower_b.append(max(0, lower))
        km_ci_upper_b.append(min(1, upper))

km_times_b = np.array(km_times_b)
km_survival_b = np.array(km_survival_b)
km_ci_lower_b = np.array(km_ci_lower_b)
km_ci_upper_b = np.array(km_ci_upper_b)

# Create step coordinates for Treatment A
x_step_a = [0.0]
y_step_a = [1.0]
y_lower_a = [1.0]
y_upper_a = [1.0]
for i, t in enumerate(km_times_a):
    prev_surv = 1.0 if i == 0 else km_survival_a[i - 1]
    prev_lower = 1.0 if i == 0 else km_ci_lower_a[i - 1]
    prev_upper = 1.0 if i == 0 else km_ci_upper_a[i - 1]
    x_step_a.extend([t, t])
    y_step_a.extend([prev_surv, km_survival_a[i]])
    y_lower_a.extend([prev_lower, km_ci_lower_a[i]])
    y_upper_a.extend([prev_upper, km_ci_upper_a[i]])
x_step_a = np.array(x_step_a)
y_step_a = np.array(y_step_a)
y_lower_a = np.array(y_lower_a)
y_upper_a = np.array(y_upper_a)

# Create step coordinates for Treatment B
x_step_b = [0.0]
y_step_b = [1.0]
y_lower_b = [1.0]
y_upper_b = [1.0]
for i, t in enumerate(km_times_b):
    prev_surv = 1.0 if i == 0 else km_survival_b[i - 1]
    prev_lower = 1.0 if i == 0 else km_ci_lower_b[i - 1]
    prev_upper = 1.0 if i == 0 else km_ci_upper_b[i - 1]
    x_step_b.extend([t, t])
    y_step_b.extend([prev_surv, km_survival_b[i]])
    y_lower_b.extend([prev_lower, km_ci_lower_b[i]])
    y_upper_b.extend([prev_upper, km_ci_upper_b[i]])
x_step_b = np.array(x_step_b)
y_step_b = np.array(y_step_b)
y_lower_b = np.array(y_lower_b)
y_upper_b = np.array(y_upper_b)

# Create figure
fig = go.Figure()

# Treatment A - Confidence interval band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([x_step_a, x_step_a[::-1]]),
        y=np.concatenate([y_upper_a, y_lower_a[::-1]]),
        fill="toself",
        fillcolor=hex_to_rgba(COLOR_A, 0.15),
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
        name="CI A",
    )
)

# Treatment B - Confidence interval band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([x_step_b, x_step_b[::-1]]),
        y=np.concatenate([y_upper_b, y_lower_b[::-1]]),
        fill="toself",
        fillcolor=hex_to_rgba(COLOR_B, 0.15),
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
        name="CI B",
    )
)

# Treatment A - Survival curve
fig.add_trace(
    go.Scatter(
        x=x_step_a,
        y=y_step_a,
        mode="lines",
        line=dict(color=COLOR_A, width=4),
        name="Treatment A (Experimental)",
        hovertemplate="Time: %{x:.1f} months<br>Survival: %{y:.1%}<extra></extra>",
    )
)

# Treatment B - Survival curve
fig.add_trace(
    go.Scatter(
        x=x_step_b,
        y=y_step_b,
        mode="lines",
        line=dict(color=COLOR_B, width=4),
        name="Treatment B (Standard Care)",
        hovertemplate="Time: %{x:.1f} months<br>Survival: %{y:.1%}<extra></extra>",
    )
)

# Censored observations - Treatment A
censored_times_a = time_a[event_a == 0]
censored_surv_a = []
for t in censored_times_a:
    idx = np.searchsorted(km_times_a, t)
    if idx > 0:
        censored_surv_a.append(km_survival_a[idx - 1])
    else:
        censored_surv_a.append(1.0)

fig.add_trace(
    go.Scatter(
        x=censored_times_a,
        y=censored_surv_a,
        mode="markers",
        marker=dict(symbol="line-ns", size=14, line=dict(width=3, color=COLOR_A)),
        name="Censored",
        legendgroup="censored",
        hovertemplate="Censored at: %{x:.1f} months<extra></extra>",
    )
)

# Censored observations - Treatment B
censored_times_b = time_b[event_b == 0]
censored_surv_b = []
for t in censored_times_b:
    idx = np.searchsorted(km_times_b, t)
    if idx > 0:
        censored_surv_b.append(km_survival_b[idx - 1])
    else:
        censored_surv_b.append(1.0)

fig.add_trace(
    go.Scatter(
        x=censored_times_b,
        y=censored_surv_b,
        mode="markers",
        marker=dict(symbol="line-ns", size=14, line=dict(width=3, color=COLOR_B)),
        name="Censored",
        legendgroup="censored",
        showlegend=False,
        hovertemplate="Censored at: %{x:.1f} months<extra></extra>",
    )
)

# Calculate median survival (time when S = 0.5)
median_a = np.nan
for i, s in enumerate(km_survival_a):
    if s <= 0.5:
        median_a = km_times_a[i]
        break

median_b = np.nan
for i, s in enumerate(km_survival_b):
    if s <= 0.5:
        median_b = km_times_b[i]
        break

# Layout
fig.update_layout(
    title=dict(
        text="survival-kaplan-meier · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Time (months)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 50],
        gridcolor=GRID,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Survival Probability", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        tickformat=".0%",
        range=[0, 1.05],
        gridcolor=GRID,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    legend=dict(
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        font=dict(size=18, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=80, t=100, b=100),
)

# Add median survival annotation
median_a_str = f"{median_a:.1f}" if not np.isnan(median_a) else "N/A"
median_b_str = f"{median_b:.1f}" if not np.isnan(median_b) else "N/A"
median_text = f"Median Survival:<br>Treatment A: {median_a_str} months<br>Treatment B: {median_b_str} months"

fig.add_annotation(
    x=0.02,
    y=0.02,
    xref="paper",
    yref="paper",
    text=median_text,
    showarrow=False,
    font=dict(size=16, color=INK),
    align="left",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=8,
)

# Save
fig.write_image(os.path.join(SCRIPT_DIR, f"plot-{THEME}.png"), width=1600, height=900, scale=3)
fig.write_html(os.path.join(SCRIPT_DIR, f"plot-{THEME}.html"), include_plotlyjs="cdn")
