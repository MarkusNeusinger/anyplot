""" anyplot.ai
curve-oc: Operating Characteristic (OC) Curve
Library: plotly 6.8.0 | Python 3.13.14
Quality: 92/100 | Updated: 2026-06-20
"""

import os
import sys


# Prevent self-import: remove this script's directory from sys.path so that
# "import plotly" resolves to the installed package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np
import plotly.graph_objects as go
from scipy.stats import binom


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data
fraction_defective = np.linspace(0, 0.20, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1", "dash": "solid"},
    {"n": 100, "c": 2, "label": "n=100, c=2", "dash": "dash"},
    {"n": 150, "c": 3, "label": "n=150, c=3", "dash": "dot"},
]

colors = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], IMPRINT_PALETTE[2]]  # green, lavender, blue

aql = 0.02
ltpd = 0.08

# Compute acceptance probabilities
oc_curves = {}
for plan in sampling_plans:
    prob_accept = binom.cdf(plan["c"], plan["n"], fraction_defective)
    oc_curves[plan["label"]] = prob_accept

# Plot
fig = go.Figure()

# OC curves with distinct line styles for redundant encoding
for i, plan in enumerate(sampling_plans):
    label = plan["label"]
    fig.add_trace(
        go.Scatter(
            x=fraction_defective,
            y=oc_curves[label],
            mode="lines",
            name=label,
            line={"color": colors[i], "width": 3, "dash": plan["dash"]},
            hovertemplate=(f"<b>{label}</b><br>Fraction defective: %{{x:.3f}}<br>P(accept): %{{y:.3f}}<extra></extra>"),
        )
    )

# Risk calculations on the first plan
alpha_plan = sampling_plans[0]
prob_accept_aql = binom.cdf(alpha_plan["c"], alpha_plan["n"], aql)
alpha = 1 - prob_accept_aql

beta = binom.cdf(alpha_plan["c"], alpha_plan["n"], ltpd)

# Producer's risk shading (area between P(accept) and 1.0 near AQL)
p_region_x = fraction_defective[fraction_defective <= aql]
p_region_oc = binom.cdf(alpha_plan["c"], alpha_plan["n"], p_region_x)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([p_region_x, p_region_x[::-1]]),
        y=np.concatenate([p_region_oc, np.ones(len(p_region_x))]),
        fill="toself",
        fillcolor="rgba(0,158,115,0.15)",
        line={"width": 0},
        name=f"Producer's risk α = {alpha:.3f}",
        hoverinfo="skip",
        showlegend=True,
    )
)

# Consumer's risk shading (area from 0 to OC curve beyond LTPD)
c_region_x = fraction_defective[fraction_defective >= ltpd]
c_region_oc = binom.cdf(alpha_plan["c"], alpha_plan["n"], c_region_x)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([c_region_x, c_region_x[::-1]]),
        y=np.concatenate([np.zeros(len(c_region_x)), c_region_oc[::-1]]),
        fill="toself",
        fillcolor="rgba(174,48,48,0.15)",
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
        marker={"size": 14, "color": colors[0], "symbol": "diamond", "line": {"color": PAGE_BG, "width": 2}},
        text=[f"α={alpha:.3f}"],
        textposition="bottom right",
        textfont={"size": 10, "color": colors[0]},
        showlegend=False,
        hovertemplate=(
            f"<b>Producer's Risk (α)</b><br>"
            f"At AQL = {aql}<br>"
            f"P(accept) = {prob_accept_aql:.3f}<br>"
            f"α = {alpha:.3f}<extra></extra>"
        ),
    )
)

# Consumer's risk diamond marker at LTPD — matte red for semantic "bad lot accepted"
fig.add_trace(
    go.Scatter(
        x=[ltpd],
        y=[beta],
        mode="markers+text",
        marker={"size": 14, "color": IMPRINT_PALETTE[4], "symbol": "diamond", "line": {"color": PAGE_BG, "width": 2}},
        text=[f"β={beta:.3f}"],
        textposition="top right",
        textfont={"size": 10, "color": IMPRINT_PALETTE[4]},
        showlegend=False,
        hovertemplate=(f"<b>Consumer's Risk (β)</b><br>At LTPD = {ltpd}<br>P(accept) = {beta:.3f}<extra></extra>"),
    )
)

# AQL reference line
fig.add_shape(type="line", x0=aql, x1=aql, y0=0, y1=1, line={"color": INK_MUTED, "width": 1.5, "dash": "dash"})
fig.add_annotation(
    x=aql, y=1.05, text=f"<b>AQL={aql}</b>", showarrow=False, font={"size": 10, "color": INK_SOFT}, yref="y"
)

# LTPD reference line
fig.add_shape(type="line", x0=ltpd, x1=ltpd, y0=0, y1=1, line={"color": INK_MUTED, "width": 1.5, "dash": "dash"})
fig.add_annotation(
    x=ltpd, y=1.05, text=f"<b>LTPD={ltpd}</b>", showarrow=False, font={"size": 10, "color": INK_SOFT}, yref="y"
)

# Layout
fig.update_layout(
    autosize=False,
    title={
        "text": "curve-oc · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK, "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "y": 0.97,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Fraction Defective (p)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
        "range": [0, 0.20],
        "dtick": 0.02,
        "tickformat": ".2f",
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": INK_MUTED,
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Probability of Acceptance", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 0.5,
        "range": [-0.02, 1.12],
        "zeroline": False,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
        "dtick": 0.2,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": INK_MUTED,
        "spikedash": "dot",
    },
    legend={
        "title": {"text": "Sampling Plans", "font": {"size": 10, "color": INK_SOFT}},
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.99,
        "y": 0.98,
        "xanchor": "right",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    hovermode="x unified",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    width=800,
    height=450,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
