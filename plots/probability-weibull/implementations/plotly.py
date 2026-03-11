""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: plotly 6.6.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-11
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

# Confidence band (approximate 90% bounds for the fitted line)
t_range = np.logspace(np.log10(failure_t.min() * 0.5), np.log10(failure_t.max() * 1.5), 200)
fit_weibull_y = beta_fit * np.log(t_range) - beta_fit * np.log(eta_fit)
se_fit = np.sqrt(
    np.sum((weibull_y_failures - (beta_fit * np.log(failure_t) - beta_fit * np.log(eta_fit))) ** 2) / (n_failures - 2)
)
conf_upper = fit_weibull_y + 1.645 * se_fit
conf_lower = fit_weibull_y - 1.645 * se_fit

# Typography
font_family = "Helvetica Neue, Helvetica, Arial, sans-serif"

# Plot - using Weibull linearized y-axis
fig = go.Figure()

# 90% confidence band as filled area
fig.add_trace(
    go.Scatter(
        x=np.concatenate([t_range, t_range[::-1]]),
        y=np.concatenate([conf_upper, conf_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.08)",
        line={"width": 0},
        name="90% Confidence",
        hoverinfo="skip",
        showlegend=True,
    )
)

# Fitted line (straight in Weibull space)
fig.add_trace(
    go.Scatter(
        x=t_range,
        y=fit_weibull_y,
        mode="lines",
        name="Weibull Fit",
        line={"color": "#306998", "width": 3.5, "dash": "solid"},
        hovertemplate="Time: %{x:.0f}h<br>Probability: %{customdata:.1%}<extra>Weibull Fit</extra>",
        customdata=1 - np.exp(-np.exp(fit_weibull_y)),
    )
)

# Failure data points (larger markers for <30 data points)
fig.add_trace(
    go.Scatter(
        x=failure_t,
        y=weibull_y_failures,
        mode="markers",
        name="Failures",
        marker={"size": 18, "color": "#306998", "line": {"color": "white", "width": 2}, "opacity": 0.9},
        hovertemplate=(
            "<b>Failure #%{text}</b><br>Time: %{x:.0f} hours<br>Cum. Probability: %{customdata:.1%}<extra></extra>"
        ),
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
            "size": 18,
            "color": "rgba(232, 93, 58, 0.15)",
            "line": {"color": "#E85D3A", "width": 3},
            "symbol": "diamond",
        },
        hovertemplate=(
            "<b>Censored Observation</b><br>Time: %{x:.0f} hours<br>Est. Probability: %{customdata:.1%}<extra></extra>"
        ),
        customdata=censored_prob_est,
    )
)

# 63.2% reference line (characteristic life) in Weibull coordinates
weibull_632 = np.log(-np.log(1 - 0.632))
fig.add_hline(
    y=weibull_632,
    line_dash="dot",
    line_color="rgba(100, 100, 100, 0.5)",
    line_width=2,
    annotation_text=f"63.2% — characteristic life (η ≈ {eta_fit:.0f}h)",
    annotation_position="top left",
    annotation_font={"size": 16, "color": "#555555", "family": font_family},
)

# Vertical drop line from characteristic life to x-axis
fig.add_vline(x=eta_fit, line_dash="dot", line_color="rgba(100, 100, 100, 0.3)", line_width=1.5)

# On-plot annotation for fitted parameters
fig.add_annotation(
    x=np.log10(eta_fit * 1.3),
    y=weibull_tick_vals[2],
    xref="x",
    yref="y",
    text=(
        f"<b style='font-size:17px'>Weibull Parameters</b><br>"
        f"<span style='color:#306998'>β</span> (shape) = {beta_fit:.2f}<br>"
        f"<span style='color:#306998'>η</span> (scale) = {eta_fit:.0f}h<br>"
        f"R² = {r_value**2:.4f}"
    ),
    showarrow=False,
    font={"size": 16, "color": "#2a2a2a", "family": font_family},
    align="left",
    bgcolor="rgba(255,255,255,0.92)",
    bordercolor="rgba(48, 105, 152, 0.25)",
    borderwidth=1.5,
    borderpad=12,
)

# B10 life annotation (time at 10% failure probability)
b10_life = eta_fit * (-np.log(1 - 0.10)) ** (1 / beta_fit)
weibull_10 = np.log(-np.log(1 - 0.10))
fig.add_annotation(
    x=b10_life,
    y=weibull_10,
    xref="x",
    yref="y",
    text=f"B10 = {b10_life:.0f}h",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowcolor="#888888",
    ax=50,
    ay=30,
    font={"size": 15, "color": "#555555", "family": font_family},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="rgba(0,0,0,0.1)",
    borderwidth=1,
    borderpad=6,
)

# Style - Weibull probability paper with custom y-axis ticks
fig.update_layout(
    title={
        "text": "probability-weibull · plotly · pyplots.ai",
        "font": {"size": 28, "family": font_family, "color": "#1a1a1a"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {
            "text": "Time to Failure (hours)",
            "font": {"size": 22, "family": font_family, "color": "#333333"},
            "standoff": 15,
        },
        "tickfont": {"size": 18, "family": font_family, "color": "#444444"},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.2)",
        "linewidth": 1.5,
        "minor": {"showgrid": True, "gridcolor": "rgba(0,0,0,0.03)"},
        "zeroline": False,
    },
    yaxis={
        "title": {
            "text": "Cumulative Failure Probability (Weibull Scale)",
            "font": {"size": 22, "family": font_family, "color": "#333333"},
            "standoff": 10,
        },
        "tickfont": {"size": 18, "family": font_family, "color": "#444444"},
        "tickmode": "array",
        "tickvals": weibull_tick_vals,
        "ticktext": prob_labels,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.2)",
        "linewidth": 1.5,
        "range": [weibull_tick_vals[0] - 0.3, weibull_tick_vals[-1] + 0.3],
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 17, "family": font_family},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.08)",
        "borderwidth": 1,
    },
    plot_bgcolor="rgba(250, 251, 253, 1)",
    paper_bgcolor="white",
    margin={"l": 90, "r": 40, "t": 70, "b": 75},
    hoverlabel={"font": {"size": 14, "family": font_family}, "bgcolor": "white", "bordercolor": "#306998"},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
