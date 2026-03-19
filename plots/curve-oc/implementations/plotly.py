""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-19
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

# OC curves
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

# Producer's risk (alpha) shaded region: fill from OC curve up to y=1 at AQL
# Use the first plan for risk calculations
alpha_plan = sampling_plans[0]
prob_accept_aql = binom.cdf(alpha_plan["c"], alpha_plan["n"], aql)
alpha = 1 - prob_accept_aql

# Shaded region for producer's risk (area between P(accept) and 1.0 near AQL)
p_region_x = fraction_defective[fraction_defective <= aql]
p_region_oc = binom.cdf(alpha_plan["c"], alpha_plan["n"], p_region_x)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([p_region_x, p_region_x[::-1]]),
        y=np.concatenate([p_region_oc, np.ones(len(p_region_x))]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.15)",
        line={"width": 0},
        name=f"Producer's risk α = {alpha:.3f}",
        hoverinfo="skip",
        showlegend=True,
    )
)

# Consumer's risk (beta) shaded region: fill from 0 up to OC curve at LTPD
beta = binom.cdf(alpha_plan["c"], alpha_plan["n"], ltpd)

c_region_x = fraction_defective[fraction_defective >= ltpd]
c_region_oc = binom.cdf(alpha_plan["c"], alpha_plan["n"], c_region_x)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([c_region_x, c_region_x[::-1]]),
        y=np.concatenate([np.zeros(len(c_region_x)), c_region_oc[::-1]]),
        fill="toself",
        fillcolor="rgba(155, 44, 138, 0.15)",
        line={"width": 0},
        name=f"Consumer's risk β = {beta:.3f}",
        hoverinfo="skip",
        showlegend=True,
    )
)

# Producer's risk diamond marker at AQL
fig.add_trace(
    go.Scatter(
        x=[aql],
        y=[prob_accept_aql],
        mode="markers+text",
        marker={"size": 16, "color": colors[0], "symbol": "diamond", "line": {"color": "white", "width": 2}},
        text=[f"α={alpha:.3f}"],
        textposition="bottom right",
        textfont={"size": 14, "color": colors[0], "family": "Arial Black"},
        showlegend=False,
        hovertemplate=(
            f"<b>Producer's Risk (α)</b><br>"
            f"At AQL = {aql}<br>"
            f"P(accept) = {prob_accept_aql:.3f}<br>"
            f"α = {alpha:.3f}<extra></extra>"
        ),
    )
)

# Consumer's risk diamond marker at LTPD - use purple to distinguish from orange curve
fig.add_trace(
    go.Scatter(
        x=[ltpd],
        y=[beta],
        mode="markers+text",
        marker={"size": 16, "color": "#9B2C8A", "symbol": "diamond", "line": {"color": "white", "width": 2}},
        text=[f"β={beta:.3f}"],
        textposition="top right",
        textfont={"size": 14, "color": "#9B2C8A", "family": "Arial Black"},
        showlegend=False,
        hovertemplate=(f"<b>Consumer's Risk (β)</b><br>At LTPD = {ltpd}<br>P(accept) = {beta:.3f}<extra></extra>"),
    )
)

# AQL vertical reference line
fig.add_shape(type="line", x0=aql, x1=aql, y0=0, y1=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})
fig.add_annotation(x=aql, y=1.05, text="<b>AQL = 0.02</b>", showarrow=False, font={"size": 15, "color": "#34495e"})

# LTPD vertical reference line
fig.add_shape(type="line", x0=ltpd, x1=ltpd, y0=0, y1=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})
fig.add_annotation(x=ltpd, y=1.05, text="<b>LTPD = 0.08</b>", showarrow=False, font={"size": 15, "color": "#34495e"})

# Style
fig.update_layout(
    title={
        "text": "curve-oc · plotly · pyplots.ai",
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
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#aaa",
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Probability of Acceptance", "font": {"size": 22, "color": "#34495e"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 0.5,
        "range": [-0.02, 1.10],
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#ccc",
        "dtick": 0.2,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#aaa",
        "spikedash": "dot",
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
    hovermode="x unified",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 70, "b": 70},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
