""" pyplots.ai
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
ln_t = np.log(failure_t)
weibull_y = np.log(-np.log(1 - failure_prob))

# Fit line: weibull_y = beta * ln(t) - beta * ln(eta)
slope, intercept, r_value, _, _ = stats.linregress(ln_t, weibull_y)
beta_fit = slope
eta_fit = np.exp(-intercept / beta_fit)

# Plot
fig = go.Figure()

t_range = np.linspace(np.log(failure_t.min() * 0.5), np.log(failure_t.max() * 1.5), 200)
fit_y = beta_fit * t_range - beta_fit * np.log(eta_fit)
fit_prob = 1 - np.exp(-np.exp(fit_y))

fig.add_trace(
    go.Scatter(
        x=np.exp(t_range),
        y=fit_prob,
        mode="lines",
        name=f"Weibull Fit (β={beta_fit:.2f}, η={eta_fit:.0f}h)",
        line={"color": "#306998", "width": 3},
    )
)

fig.add_trace(
    go.Scatter(
        x=failure_t,
        y=failure_prob,
        mode="markers",
        name="Failures",
        marker={"size": 12, "color": "#306998", "line": {"color": "white", "width": 1.5}},
    )
)

censored_t = all_times[is_censored]
censored_prob = 1 - np.exp(-((censored_t / eta_fit) ** beta_fit))

fig.add_trace(
    go.Scatter(
        x=censored_t,
        y=censored_prob,
        mode="markers",
        name="Censored (suspended)",
        marker={"size": 13, "color": "white", "line": {"color": "#E85D3A", "width": 2.5}, "symbol": "circle"},
    )
)

# 63.2% reference line
fig.add_hline(
    y=0.632,
    line_dash="dash",
    line_color="#999999",
    line_width=1.5,
    annotation_text="63.2% (characteristic life)",
    annotation_position="top left",
    annotation_font={"size": 16, "color": "#666666"},
)

# Style
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
    },
    yaxis={
        "title": {"text": "Cumulative Failure Probability", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickformat": ".0%",
        "range": [0, 1],
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.3)",
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
