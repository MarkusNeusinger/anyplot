""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-19
"""

from math import comb

import altair as alt
import numpy as np
import pandas as pd


# Data — varied c/n ratios for better curve contrast
fraction_defective = np.linspace(0, 0.20, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 100, "c": 3, "label": "n=100, c=3"},
    {"n": 200, "c": 2, "label": "n=200, c=2"},
]

rows = []
for plan in sampling_plans:
    n, c = plan["n"], plan["c"]
    prob_accept = np.zeros_like(fraction_defective, dtype=float)
    for k in range(c + 1):
        prob_accept += comb(n, k) * fraction_defective**k * (1 - fraction_defective) ** (n - k)
    for p, pa in zip(fraction_defective, prob_accept, strict=True):
        rows.append({"fraction_defective": p, "probability_acceptance": pa, "plan": plan["label"]})

df = pd.DataFrame(rows)

# AQL and LTPD reference points
aql = 0.02
ltpd = 0.10

# Compute risk values for the primary plan (n=100, c=3)
pa_at_aql_arr = np.zeros(1, dtype=float)
for k in range(4):
    pa_at_aql_arr += comb(100, k) * np.array([aql]) ** k * (1 - np.array([aql])) ** (100 - k)
pa_at_aql = pa_at_aql_arr[0]
alpha = 1 - pa_at_aql

pa_at_ltpd_arr = np.zeros(1, dtype=float)
for k in range(4):
    pa_at_ltpd_arr += comb(100, k) * np.array([ltpd]) ** k * (1 - np.array([ltpd])) ** (100 - k)
pa_at_ltpd = pa_at_ltpd_arr[0]
beta = pa_at_ltpd

ref_data = pd.DataFrame(
    [
        {"x": aql, "y": pa_at_aql, "label": f"AQL = {aql:.0%}", "risk": f"α = {alpha:.1%} (Producer's Risk)"},
        {"x": ltpd, "y": pa_at_ltpd, "label": f"LTPD = {ltpd:.0%}", "risk": f"β = {beta:.1%} (Consumer's Risk)"},
    ]
)

# In-chart legend data (positioned in upper-right where curves have dropped)
legend_data = pd.DataFrame(
    [
        {"x1": 0.125, "x2": 0.14, "y": 0.85, "label": "  n=50, c=1  (lenient)", "color": "#306998"},
        {"x1": 0.125, "x2": 0.14, "y": 0.78, "label": "  n=100, c=3  (moderate)", "color": "#E8792B"},
        {"x1": 0.125, "x2": 0.14, "y": 0.71, "label": "  n=200, c=2  (strict)", "color": "#8B5CF6"},
    ]
)

# Plot
plan_labels = ["n=50, c=1", "n=100, c=3", "n=200, c=2"]
color_scale = alt.Scale(domain=plan_labels, range=["#306998", "#E8792B", "#8B5CF6"])

nearest = alt.selection_point(nearest=True, on="pointerover", fields=["fraction_defective"], empty=False)

base_x = alt.X(
    "fraction_defective:Q",
    title="Fraction Defective (p)",
    scale=alt.Scale(domain=[0, 0.20]),
    axis=alt.Axis(format=".0%", values=[0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20]),
)
base_y = alt.Y(
    "probability_acceptance:Q",
    title="Probability of Acceptance P(a)",
    scale=alt.Scale(domain=[0, 1.05]),
    axis=alt.Axis(values=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
)

# OC curves (no Vega legend — using in-chart legend instead)
oc_lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=base_x,
        y=base_y,
        color=alt.Color("plan:N", scale=color_scale, legend=None),
        strokeDash=alt.StrokeDash(
            "plan:N", scale=alt.Scale(domain=plan_labels, range=[[1, 0], [8, 4], [2, 2]]), legend=None
        ),
    )
)

# Transparent selection layer for hover
select_layer = (
    alt.Chart(df)
    .mark_point(size=300, opacity=0)
    .encode(x=alt.X("fraction_defective:Q"), y=alt.Y("probability_acceptance:Q"))
    .add_params(nearest)
)

# Vertical rule at hover
hover_rule = (
    alt.Chart(df)
    .mark_rule(strokeWidth=1.5, color="#999999", strokeDash=[3, 3])
    .encode(x=alt.X("fraction_defective:Q"))
    .transform_filter(nearest)
)

# Highlighted points on hover
hover_points = (
    alt.Chart(df)
    .mark_point(filled=True, stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X("fraction_defective:Q"),
        y=alt.Y("probability_acceptance:Q"),
        color=alt.Color("plan:N", scale=color_scale, legend=None),
        size=alt.condition(nearest, alt.value(250), alt.value(0)),
        tooltip=[
            alt.Tooltip("plan:N", title="Plan"),
            alt.Tooltip("fraction_defective:Q", title="Fraction Defective", format=".3f"),
            alt.Tooltip("probability_acceptance:Q", title="P(Accept)", format=".3f"),
        ],
    )
)

# AQL vertical reference line
aql_rule = (
    alt.Chart(pd.DataFrame([{"x": aql}]))
    .mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#306998", opacity=0.6)
    .encode(x=alt.X("x:Q"))
)

aql_label = (
    alt.Chart(pd.DataFrame([{"x": aql, "y": 1.02, "text": "AQL"}]))
    .mark_text(fontSize=18, fontWeight="bold", color="#306998", dy=-6)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# LTPD vertical reference line
ltpd_rule = (
    alt.Chart(pd.DataFrame([{"x": ltpd}]))
    .mark_rule(strokeDash=[8, 6], strokeWidth=2, color="#D62728", opacity=0.6)
    .encode(x=alt.X("x:Q"))
)

ltpd_label = (
    alt.Chart(pd.DataFrame([{"x": ltpd, "y": 1.02, "text": "LTPD"}]))
    .mark_text(fontSize=18, fontWeight="bold", color="#D62728", dy=-6)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# Risk annotation points on the n=100, c=3 curve
risk_points = (
    alt.Chart(ref_data)
    .mark_point(filled=True, size=300, stroke="white", strokeWidth=2.5, color="#333333")
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        tooltip=[
            alt.Tooltip("label:N", title="Reference"),
            alt.Tooltip("risk:N", title="Risk"),
            alt.Tooltip("y:Q", title="P(Accept)", format=".3f"),
        ],
    )
)

risk_labels = (
    alt.Chart(ref_data)
    .mark_text(fontSize=17, fontWeight="bold", align="left", dx=12, dy=-12, color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="risk:N")
)

# In-chart legend background
legend_bg = (
    alt.Chart(pd.DataFrame([{"x": 0.123, "y": 0.91, "x2": 0.197, "y2": 0.66}]))
    .mark_rect(cornerRadius=8, fill="#fafafa", stroke="#cccccc", strokeWidth=1.5, opacity=0.92)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), x2="x2:Q", y2="y2:Q")
)

legend_title = (
    alt.Chart(pd.DataFrame([{"x": 0.16, "y": 0.895, "text": "Sampling Plan"}]))
    .mark_text(fontSize=17, fontWeight="bold", color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# Legend color swatches (small line segments)
legend_lines = []
legend_texts = []
for _, row in legend_data.iterrows():
    line_df = pd.DataFrame([{"x": row["x1"], "y": row["y"], "x2": row["x2"], "y2": row["y"]}])
    legend_lines.append(
        alt.Chart(line_df)
        .mark_rule(strokeWidth=3, color=row["color"])
        .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), x2="x2:Q")
    )
    text_df = pd.DataFrame([{"x": row["x2"], "y": row["y"], "text": row["label"]}])
    legend_texts.append(
        alt.Chart(text_df)
        .mark_text(fontSize=16, align="left", color="#444444", dx=4)
        .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
    )

# Combine layers
chart = aql_rule + ltpd_rule + oc_lines + hover_points + risk_points + risk_labels + aql_label + ltpd_label
chart = chart + legend_bg + legend_title
for ll in legend_lines:
    chart = chart + ll
for lt in legend_texts:
    chart = chart + lt
chart = chart + select_layer + hover_rule

chart = (
    chart.properties(
        width=1600,
        height=900,
        title=alt.Title(
            "curve-oc · altair · pyplots.ai",
            subtitle="Acceptance Sampling Plans — Producer's & Consumer's Risk",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15, domainWidth=0)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
