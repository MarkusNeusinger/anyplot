"""anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# SHAP semantic colors (Imprint palette positions)
POS_COLOR = IMPRINT_PALETTE[4]  # red: positive SHAP (pushes prediction up)
NEG_COLOR = IMPRINT_PALETTE[2]  # blue: negative SHAP (pushes prediction down)
REF_COLOR = IMPRINT_PALETTE[0]  # brand green: reference bars (base and final)

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP_VALUE = "SHAP value (impact on predicted default probability)"  # role: shap_value
BASE_VALUE = "Base value E[f(x)]"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Credit risk model, one high-risk loan applicant; the base value repeats on every row
df = pd.DataFrame(
    {
        FEATURE: [
            "Debt-to-Income Ratio",
            "Missed Payments (12 mo)",
            "Credit Utilization",
            "Credit Score",
            "Annual Income",
            "Employment Stability",
            "Credit History Length",
            "Account Diversity",
            "Property Ownership",
        ],
        SHAP_VALUE: [0.18, 0.15, 0.12, -0.09, 0.08, -0.06, 0.06, -0.04, -0.03],
        BASE_VALUE: [0.35] * 9,
    }
)

# Plot: reads only df and the constants above
# Plotly's horizontal waterfall draws the first y item at the bottom, so sort ascending by |SHAP|
table = df.iloc[np.argsort(df[SHAP_VALUE].abs().to_numpy(), kind="stable")]
base_value = float(table[BASE_VALUE].iloc[0])
final_value = base_value + float(table[SHAP_VALUE].sum())

base_label = f"E[f(x)] = {base_value:.2f}"
final_label = f"f(x) = {final_value:.2f}"
y_labels = [base_label] + table[FEATURE].tolist() + [final_label]
x_vals = [base_value] + table[SHAP_VALUE].tolist() + [0]
measures = ["absolute"] + ["relative"] * len(table) + ["total"]
text_vals = [f"{base_value:.2f}"] + [f"{v:+.3f}" for v in table[SHAP_VALUE]] + [f"{final_value:.2f}"]

# Axis range from the cumulative chain, with room on the right for the outside labels
chain = base_value + np.cumsum(table[SHAP_VALUE].to_numpy())
top = max(base_value, float(chain.max()))
x_range = [min(0.0, float(chain.min())) - 0.1 * top, top * 1.3]

title = "Credit Default Risk · shap-waterfall · python · plotly · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

fig = go.Figure(
    go.Waterfall(
        orientation="h",
        measure=measures,
        y=y_labels,
        x=x_vals,
        text=text_vals,
        textposition="outside",
        textfont=dict(size=10, color=INK),
        increasing=dict(marker=dict(color=POS_COLOR, line=dict(color=POS_COLOR, width=0))),
        decreasing=dict(marker=dict(color=NEG_COLOR, line=dict(color=NEG_COLOR, width=0))),
        totals=dict(marker=dict(color=REF_COLOR, line=dict(color=REF_COLOR, width=0))),
        connector=dict(line=dict(color=INK_MUTED, width=1, dash="dot")),
        cliponaxis=False,
    )
)

# Style
fig.update_layout(
    autosize=False,
    title=dict(text=title, font=dict(size=title_size, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(text=SHAP_VALUE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
        range=x_range,
    ),
    yaxis=dict(tickfont=dict(size=10, color=INK_SOFT), linecolor=INK_SOFT, showgrid=False),
    showlegend=False,
    margin=dict(l=130, r=60, t=50, b=50),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
