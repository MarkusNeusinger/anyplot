"""pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import binom


# Data
fraction_defective = np.linspace(0, 0.20, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 100, "c": 2, "label": "n=100, c=2"},
    {"n": 150, "c": 3, "label": "n=150, c=3"},
]

colors = ["#306998", "#E8793A", "#5BA85B"]

aql = 0.02
ltpd = 0.08

# Compute acceptance probabilities
oc_curves = {}
for plan in sampling_plans:
    prob_accept = binom.cdf(plan["c"], plan["n"], fraction_defective)
    oc_curves[plan["label"]] = prob_accept

# Plot
fig = go.Figure()

for i, plan in enumerate(sampling_plans):
    label = plan["label"]
    fig.add_trace(
        go.Scatter(
            x=fraction_defective,
            y=oc_curves[label],
            mode="lines",
            name=label,
            line={"color": colors[i], "width": 3.5},
            hovertemplate=(f"<b>{label}</b><br>Fraction defective: %{{x:.3f}}<br>P(accept): %{{y:.3f}}<extra></extra>"),
        )
    )

# AQL vertical reference line
fig.add_shape(type="line", x0=aql, x1=aql, y0=0, y1=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})
fig.add_annotation(x=aql, y=1.04, text="<b>AQL = 0.02</b>", showarrow=False, font={"size": 14, "color": "#555555"})

# LTPD vertical reference line
fig.add_shape(type="line", x0=ltpd, x1=ltpd, y0=0, y1=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})
fig.add_annotation(x=ltpd, y=1.04, text="<b>LTPD = 0.08</b>", showarrow=False, font={"size": 14, "color": "#555555"})

# Producer's risk (alpha) at AQL for first plan
alpha_plan = sampling_plans[0]
prob_accept_aql = binom.cdf(alpha_plan["c"], alpha_plan["n"], aql)
alpha = 1 - prob_accept_aql

fig.add_trace(
    go.Scatter(
        x=[aql],
        y=[prob_accept_aql],
        mode="markers",
        marker={"size": 16, "color": colors[0], "symbol": "diamond", "line": {"color": "white", "width": 2}},
        name=f"Producer's risk \u03b1 = {alpha:.3f}",
        hovertemplate=(
            f"<b>Producer's Risk (\u03b1)</b><br>"
            f"At AQL = {aql}<br>"
            f"P(accept) = {prob_accept_aql:.3f}<br>"
            f"\u03b1 = {alpha:.3f}<extra></extra>"
        ),
    )
)

# Consumer's risk (beta) at LTPD for first plan
beta = binom.cdf(alpha_plan["c"], alpha_plan["n"], ltpd)

fig.add_trace(
    go.Scatter(
        x=[ltpd],
        y=[beta],
        mode="markers",
        marker={"size": 16, "color": "#D64545", "symbol": "diamond", "line": {"color": "white", "width": 2}},
        name=f"Consumer's risk \u03b2 = {beta:.3f}",
        hovertemplate=(f"<b>Consumer's Risk (\u03b2)</b><br>At LTPD = {ltpd}<br>P(accept) = {beta:.3f}<extra></extra>"),
    )
)

# Shaded region for producer's risk
fig.add_shape(
    type="rect",
    x0=aql,
    x1=aql + 0.003,
    y0=prob_accept_aql,
    y1=1,
    fillcolor="rgba(48, 105, 152, 0.12)",
    line={"width": 0},
)

# Shaded region for consumer's risk
fig.add_shape(
    type="rect", x0=ltpd - 0.003, x1=ltpd, y0=0, y1=beta, fillcolor="rgba(214, 69, 69, 0.12)", line={"width": 0}
)

# Style
fig.update_layout(
    title={
        "text": "curve-oc \u00b7 plotly \u00b7 pyplots.ai",
        "font": {"size": 28, "color": "#2c3e50", "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Fraction Defective (p)", "font": {"size": 22, "color": "#34495e"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#ccc",
        "range": [0, 0.20],
        "dtick": 0.02,
        "tickformat": ".2f",
    },
    yaxis={
        "title": {"text": "Probability of Acceptance", "font": {"size": 22, "color": "#34495e"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 0.5,
        "range": [-0.02, 1.08],
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#ccc",
        "dtick": 0.2,
    },
    template="plotly_white",
    legend={
        "font": {"size": 15, "color": "#34495e"},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 70, "b": 70},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
