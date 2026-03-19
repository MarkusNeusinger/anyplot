""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: altair 6.0.0 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-19
"""

from math import comb

import altair as alt
import numpy as np
import pandas as pd


# Data — varied c/n ratios for better curve contrast
fraction_defective = np.linspace(0, 0.20, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1 (lenient)"},
    {"n": 100, "c": 3, "label": "n=100, c=3 (moderate)"},
    {"n": 200, "c": 2, "label": "n=200, c=2 (strict)"},
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
pa_at_aql = sum(comb(100, k) * aql**k * (1 - aql) ** (100 - k) for k in range(4))
alpha = 1 - pa_at_aql

pa_at_ltpd = sum(comb(100, k) * ltpd**k * (1 - ltpd) ** (100 - k) for k in range(4))
beta = pa_at_ltpd

ref_data = pd.DataFrame(
    [
        {"x": aql, "y": pa_at_aql, "risk": f"\u03b1 = {alpha:.1%} (Producer\u2019s Risk)"},
        {"x": ltpd, "y": pa_at_ltpd, "risk": f"\u03b2 = {beta:.1%} (Consumer\u2019s Risk)"},
    ]
)

# Scales and encodings
plan_order = [p["label"] for p in sampling_plans]
color_scale = alt.Scale(domain=plan_order, range=["#306998", "#E8792B", "#8B5CF6"])
dash_scale = alt.Scale(domain=plan_order, range=[[1, 0], [8, 4], [2, 2]])

nearest = alt.selection_point(nearest=True, on="pointerover", fields=["fraction_defective"], empty=False)

base_x = alt.X(
    "fraction_defective:Q",
    title="Fraction Defective (p)",
    scale=alt.Scale(domain=[0, 0.20]),
    axis=alt.Axis(format=".0%", values=np.arange(0, 0.21, 0.02).tolist()),
)
base_y = alt.Y(
    "probability_acceptance:Q",
    title="Probability of Acceptance P(a)",
    scale=alt.Scale(domain=[0, 1.05]),
    axis=alt.Axis(values=np.arange(0, 1.1, 0.1).tolist()),
)

# OC curves with native Altair legend
oc_lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=3)
    .encode(
        x=base_x,
        y=base_y,
        color=alt.Color(
            "plan:N",
            scale=color_scale,
            sort=plan_order,
            legend=alt.Legend(
                title="Sampling Plan",
                titleFontSize=17,
                titleFontWeight="bold",
                titleColor="#333333",
                labelFontSize=16,
                labelColor="#444444",
                symbolStrokeWidth=3,
                symbolSize=200,
                orient="top-right",
                offset=10,
                padding=12,
                cornerRadius=8,
                fillColor="#fafafa",
                strokeColor="#cccccc",
                direction="vertical",
            ),
        ),
        strokeDash=alt.StrokeDash("plan:N", scale=dash_scale, sort=plan_order, legend=None),
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
        tooltip=[alt.Tooltip("risk:N", title="Risk"), alt.Tooltip("y:Q", title="P(Accept)", format=".3f")],
    )
)

# Position alpha label to the right, beta label above to avoid x-axis crowding
alpha_label = (
    alt.Chart(ref_data.iloc[:1])
    .mark_text(fontSize=17, fontWeight="bold", align="left", dx=12, dy=-12, color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="risk:N")
)

beta_label = (
    alt.Chart(ref_data.iloc[1:])
    .mark_text(fontSize=17, fontWeight="bold", align="left", dx=14, dy=-24, color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="risk:N")
)

# Shaded risk regions for storytelling
alpha_area = (
    alt.Chart(pd.DataFrame([{"x": 0, "x2": aql, "y": 0, "y2": 1.05}]))
    .mark_rect(fill="#306998", opacity=0.04)
    .encode(x=alt.X("x:Q"), x2="x2:Q", y=alt.Y("y:Q"), y2="y2:Q")
)

beta_area = (
    alt.Chart(pd.DataFrame([{"x": ltpd, "x2": 0.20, "y": 0, "y2": 1.05}]))
    .mark_rect(fill="#D62728", opacity=0.04)
    .encode(x=alt.X("x:Q"), x2="x2:Q", y=alt.Y("y:Q"), y2="y2:Q")
)

# Combine layers
chart = (
    alpha_area
    + beta_area
    + aql_rule
    + ltpd_rule
    + oc_lines
    + hover_points
    + risk_points
    + alpha_label
    + beta_label
    + aql_label
    + ltpd_label
    + select_layer
    + hover_rule
)

chart = (
    chart.properties(
        width=1600,
        height=900,
        title=alt.Title(
            "curve-oc \u00b7 altair \u00b7 pyplots.ai",
            subtitle="Acceptance Sampling Plans \u2014 Producer\u2019s & Consumer\u2019s Risk",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        gridOpacity=0.12,
        gridColor="#cccccc",
        domainWidth=0,
        tickColor="#cccccc",
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titlePadding=8, labelLimit=300)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
