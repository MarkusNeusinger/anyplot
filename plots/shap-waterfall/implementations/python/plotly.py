""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# SHAP semantic colors (Okabe-Ito positions used for semantic encoding)
POS_COLOR = "#AE3030"  # imprint red — positive SHAP (pushes prediction up)
NEG_COLOR = "#4467A3"  # blue — negative SHAP (pushes prediction down)
REF_COLOR = "#009E73"  # brand green — reference bars (base & final)

# Data — credit risk model SHAP waterfall for a single high-risk loan applicant
base_value = 0.35  # E[f(x)]: average predicted default rate across training data
final_value = 0.72  # f(x): model's default probability prediction for this applicant

features = [
    "Debt-to-Income Ratio",
    "Missed Payments (12 mo)",
    "Credit Utilization",
    "Credit Score",
    "Annual Income",
    "Employment Stability",
    "Credit History Length",
    "Account Diversity",
    "Property Ownership",
]
shap_values = [0.18, 0.15, 0.12, -0.09, 0.08, -0.06, 0.06, -0.04, -0.03]

# Sort ascending by |SHAP| so the largest contributor appears nearest the top
# (Plotly horizontal waterfall: first y item = bottom, last y item = top)
order = np.argsort(np.abs(shap_values))
sorted_features = [features[i] for i in order]
sorted_shap = [shap_values[i] for i in order]

# Waterfall layers: base (absolute) → features (relative, small→large) → prediction (total)
y_labels = ["E[f(x)] = 0.35"] + sorted_features + ["f(x) = 0.72"]
x_vals = [base_value] + sorted_shap + [0]
measures = ["absolute"] + ["relative"] * len(sorted_features) + ["total"]
text_vals = [f"{base_value:.2f}"] + [f"{v:+.3f}" for v in sorted_shap] + [f"{final_value:.2f}"]

# Plot
fig = go.Figure(
    go.Waterfall(
        orientation="h",
        measure=measures,
        y=y_labels,
        x=x_vals,
        text=text_vals,
        textposition="outside",
        textfont=dict(size=17, color=INK),
        increasing=dict(marker=dict(color=POS_COLOR, line=dict(color=POS_COLOR, width=0))),
        decreasing=dict(marker=dict(color=NEG_COLOR, line=dict(color=NEG_COLOR, width=0))),
        totals=dict(marker=dict(color=REF_COLOR, line=dict(color=REF_COLOR, width=0))),
        connector=dict(line=dict(color=INK_MUTED, width=1.5, dash="dot")),
        cliponaxis=False,
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="Credit Default Risk · shap-waterfall · plotly · anyplot.ai",
        font=dict(size=26, color=INK),
        x=0.5,
        xanchor="center",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(text="SHAP Value (impact on predicted default probability)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=2,
        range=[-0.20, 0.95],
    ),
    yaxis=dict(tickfont=dict(size=18, color=INK_SOFT), linecolor=INK_SOFT, showgrid=False),
    showlegend=False,
    margin=dict(l=240, r=160, t=80, b=80),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
