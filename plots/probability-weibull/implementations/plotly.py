"""pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: plotly 6.6.0 | Python 3.14.3
Quality: 73/100 | Created: 2026-03-11
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data - turbine blade fatigue life (hours)
np.random.seed(42)
n_failures = 25
n_censored = 5
n_total = n_failures + n_censored

shape_true = 2.5
scale_true = 5000
failure_times = np.sort(stats.weibull_min.rvs(shape_true, scale=scale_true, size=n_failures))
censored_times = np.sort(np.random.uniform(1000, 4500, size=n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_censored = np.concatenate([np.zeros(n_failures, dtype=bool), np.ones(n_censored, dtype=bool)])
sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_censored = is_censored[sort_idx]

# Median rank plotting positions for failures only
failure_ranks = np.zeros(n_total)
rank = 0
for i in range(n_total):
    if not is_censored[i]:
        rank += 1
        failure_ranks[i] = (rank - 0.3) / (n_failures + 0.4)

failure_mask = ~is_censored
failure_t = all_times[failure_mask]
failure_prob = failure_ranks[failure_mask]

# Weibull linearization: ln(t) vs ln(-ln(1-F))
weibull_y_failures = np.log(-np.log(1 - failure_prob))

# Fit line in Weibull space: weibull_y = beta * ln(t) - beta * ln(eta)
slope, intercept, r_value, _, _ = stats.linregress(np.log(failure_t), weibull_y_failures)
beta_fit = slope
eta_fit = np.exp(-intercept / beta_fit)

# Probability tick values and labels for Weibull y-axis
prob_ticks = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.95, 0.99]
prob_labels = ["1%", "2%", "5%", "10%", "20%", "50%", "63.2%", "90%", "95%", "99%"]
weibull_tick_vals = [np.log(-np.log(1 - p)) for p in prob_ticks]

# Plot - using Weibull linearized y-axis
fig = go.Figure()

# Fitted line (straight in Weibull space)
t_range = np.logspace(np.log10(failure_t.min() * 0.5), np.log10(failure_t.max() * 1.5), 200)
fit_weibull_y = beta_fit * np.log(t_range) - beta_fit * np.log(eta_fit)

fig.add_trace(
    go.Scatter(
        x=t_range,
        y=fit_weibull_y,
        mode="lines",
        name="Weibull Fit",
        line={"color": "#306998", "width": 3.5},
        hovertemplate="Time: %{x:.0f}h<br>Probability: %{customdata:.1%}<extra>Weibull Fit</extra>",
        customdata=1 - np.exp(-np.exp(fit_weibull_y)),
    )
)

# Failure data points
fig.add_trace(
    go.Scatter(
        x=failure_t,
        y=weibull_y_failures,
        mode="markers",
        name="Failures",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 1.5}},
        hovertemplate="Time: %{x:.0f}h<br>Probability: %{customdata:.1%}<br>Rank: %{text}<extra>Failure</extra>",
        customdata=failure_prob,
        text=[f"{i + 1}/{n_failures}" for i in range(n_failures)],
    )
)

# Censored data points - estimate their probability from the fitted model
censored_t = all_times[is_censored]
censored_weibull_y = beta_fit * np.log(censored_t) - beta_fit * np.log(eta_fit)
censored_prob_est = 1 - np.exp(-np.exp(censored_weibull_y))

fig.add_trace(
    go.Scatter(
        x=censored_t,
        y=censored_weibull_y,
        mode="markers",
        name="Censored (suspended)",
        marker={
            "size": 14,
            "color": "rgba(232, 93, 58, 0.15)",
            "line": {"color": "#E85D3A", "width": 3},
            "symbol": "diamond",
        },
        hovertemplate="Time: %{x:.0f}h<br>Est. Probability: %{customdata:.1%}<extra>Censored</extra>",
        customdata=censored_prob_est,
    )
)

# 63.2% reference line (characteristic life) in Weibull coordinates
weibull_632 = np.log(-np.log(1 - 0.632))
fig.add_hline(
    y=weibull_632,
    line_dash="dash",
    line_color="#999999",
    line_width=1.5,
    annotation_text="63.2% — characteristic life",
    annotation_position="top left",
    annotation_font={"size": 16, "color": "#666666"},
)

# On-plot annotation for fitted parameters
fig.add_annotation(
    x=np.log10(eta_fit * 1.3),
    y=weibull_tick_vals[2],
    xref="x",
    yref="y",
    text=(
        f"<b>Weibull Parameters</b><br>"
        f"β (shape) = {beta_fit:.2f}<br>"
        f"η (scale) = {eta_fit:.0f}h<br>"
        f"R² = {r_value**2:.4f}"
    ),
    showarrow=False,
    font={"size": 16, "color": "#333333"},
    align="left",
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="rgba(0,0,0,0.15)",
    borderwidth=1,
    borderpad=8,
)

# Style - Weibull probability paper with custom y-axis ticks
fig.update_layout(
    title={"text": "probability-weibull · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5},
    xaxis={
        "title": {"text": "Time to Failure (hours)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.3)",
        "minor": {"showgrid": True, "gridcolor": "rgba(0,0,0,0.04)"},
    },
    yaxis={
        "title": {"text": "Cumulative Failure Probability (Weibull Scale)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickmode": "array",
        "tickvals": weibull_tick_vals,
        "ticktext": prob_labels,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.3)",
        "range": [weibull_tick_vals[0] - 0.3, weibull_tick_vals[-1] + 0.3],
    },
    template="plotly_white",
    legend={"font": {"size": 18}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    plot_bgcolor="white",
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
