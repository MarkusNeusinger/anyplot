"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: altair 6.0.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Label-to-index mappings
likelihood_map = {lbl: i + 1 for i, lbl in enumerate(likelihood_labels)}
impact_map = {lbl: i + 1 for i, lbl in enumerate(impact_labels)}

# Background grid: all 25 cells with risk scores
grid_rows = []
for li in range(1, 6):
    for im in range(1, 6):
        grid_rows.append(
            {"li": li, "im": im, "risk_score": li * im, "x1": im - 0.5, "x2": im + 0.5, "y1": li - 0.5, "y2": li + 0.5}
        )

grid_df = pd.DataFrame(grid_rows)

# Risk items with realistic project risk data
risk_items = [
    {"risk_name": "Server Outage", "likelihood": "Unlikely", "impact": "Catastrophic", "category": "Technical"},
    {"risk_name": "Budget Overrun", "likelihood": "Likely", "impact": "Major", "category": "Financial"},
    {"risk_name": "Key Staff Loss", "likelihood": "Possible", "impact": "Major", "category": "Operational"},
    {"risk_name": "Scope Creep", "likelihood": "Almost Certain", "impact": "Moderate", "category": "Operational"},
    {"risk_name": "Data Breach", "likelihood": "Unlikely", "impact": "Catastrophic", "category": "Technical"},
    {"risk_name": "Vendor Delay", "likelihood": "Possible", "impact": "Moderate", "category": "Operational"},
    {"risk_name": "Reg. Change", "likelihood": "Unlikely", "impact": "Major", "category": "Financial"},
    {"risk_name": "Req. Gap", "likelihood": "Likely", "impact": "Moderate", "category": "Technical"},
    {"risk_name": "Currency Risk", "likelihood": "Possible", "impact": "Minor", "category": "Financial"},
    {"risk_name": "Power Failure", "likelihood": "Rare", "impact": "Moderate", "category": "Technical"},
    {"risk_name": "Supply Issue", "likelihood": "Possible", "impact": "Major", "category": "Operational"},
    {"risk_name": "Testing Delay", "likelihood": "Likely", "impact": "Minor", "category": "Technical"},
    {"risk_name": "Legal Dispute", "likelihood": "Rare", "impact": "Catastrophic", "category": "Financial"},
    {"risk_name": "Team Conflict", "likelihood": "Unlikely", "impact": "Minor", "category": "Operational"},
    {"risk_name": "Tech Debt", "likelihood": "Almost Certain", "impact": "Minor", "category": "Technical"},
]

risk_df = pd.DataFrame(risk_items)
risk_df["li"] = risk_df["likelihood"].map(likelihood_map)
risk_df["im"] = risk_df["impact"].map(impact_map)

# Smart jitter: spread items sharing same cell to avoid label overlaps
cell_key = risk_df["likelihood"] + "|" + risk_df["impact"]
cell_counts = cell_key.map(cell_key.value_counts())
cell_idx = cell_key.groupby(cell_key).cumcount()

# Items in shared cells get systematic spread; solo items stay centered
risk_df["x"] = (
    risk_df["im"]
    + np.where(cell_counts > 1, (cell_idx - (cell_counts - 1) / 2) * 0.28, 0)
    + np.random.uniform(-0.04, 0.04, len(risk_df))
)
risk_df["y"] = (
    risk_df["li"]
    + np.where(cell_counts > 1, (cell_idx - (cell_counts - 1) / 2) * 0.15, 0)
    + np.random.uniform(-0.04, 0.04, len(risk_df))
)

# Color scale: green → yellow → orange → red
color_scale = alt.Scale(
    domain=[1, 5, 10, 16, 25], range=["#4caf50", "#c6d93e", "#ff9800", "#f44336", "#b71c1c"], interpolate="lab"
)

category_scale = alt.Scale(domain=["Technical", "Financial", "Operational"], range=["#306998", "#e8871e", "#7b2d8e"])

# Axis label expressions: map numeric ticks to descriptive labels
x_label_expr = " : ".join(f"datum.value === {i + 1} ? '{lbl}'" for i, lbl in enumerate(impact_labels)) + " : ''"
y_label_expr = " : ".join(f"datum.value === {i + 1} ? '{lbl}'" for i, lbl in enumerate(likelihood_labels)) + " : ''"

x_axis = alt.Axis(
    values=[1, 2, 3, 4, 5],
    labelExpr=x_label_expr,
    labelFontSize=17,
    titleFontSize=22,
    titleFontWeight="bold",
    labelAngle=0,
    domainWidth=0,
    tickWidth=0,
    titlePadding=16,
    labelPadding=10,
)
y_axis = alt.Axis(
    values=[1, 2, 3, 4, 5],
    labelExpr=y_label_expr,
    labelFontSize=17,
    titleFontSize=22,
    titleFontWeight="bold",
    domainWidth=0,
    tickWidth=0,
    titlePadding=16,
    labelPadding=10,
)

x_scale = alt.Scale(domain=[0.5, 5.5])
y_scale = alt.Scale(domain=[0.5, 5.5], reverse=True)

# Heatmap background cells using rect with x/y/x2/y2
heatmap = (
    alt.Chart(grid_df)
    .mark_rect(stroke="#ffffff", strokeWidth=3, cornerRadius=4)
    .encode(
        x=alt.X("x1:Q", scale=x_scale, axis=None),
        x2="x2:Q",
        y=alt.Y("y1:Q", scale=y_scale, axis=None),
        y2="y2:Q",
        color=alt.Color("risk_score:Q", scale=color_scale, legend=None),
    )
)

# Risk score text in each cell
score_text = (
    alt.Chart(grid_df)
    .mark_text(fontSize=28, fontWeight="bold", opacity=0.18)
    .encode(
        x=alt.X("im:Q", scale=x_scale, axis=None),
        y=alt.Y("li:Q", scale=y_scale, axis=None),
        text=alt.Text("risk_score:Q"),
        color=alt.condition(
            alt.datum.risk_score > 12, alt.value("rgba(255,255,255,0.6)"), alt.value("rgba(0,0,0,0.3)")
        ),
    )
)

# Risk markers — single layer with jittered quantitative positions
markers = (
    alt.Chart(risk_df)
    .mark_circle(size=500, stroke="#ffffff", strokeWidth=2.5, opacity=0.92)
    .encode(
        x=alt.X("x:Q", scale=x_scale, title="Impact", axis=x_axis),
        y=alt.Y("y:Q", scale=y_scale, title="Likelihood", axis=y_axis),
        color=alt.Color("category:N", scale=category_scale, legend=None),
        tooltip=[
            alt.Tooltip("risk_name:N", title="Risk"),
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("likelihood:N", title="Likelihood"),
            alt.Tooltip("impact:N", title="Impact"),
        ],
    )
)

# Risk labels — single layer, positioned above markers
labels = (
    alt.Chart(risk_df)
    .mark_text(fontSize=13, fontWeight="bold", dy=-16)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        text=alt.Text("risk_name:N"),
        color=alt.value("#222222"),
    )
)

# Category legend via invisible marks
legend_source = pd.DataFrame({"category": ["Technical", "Financial", "Operational"], "x": [1] * 3, "y": [1] * 3})
legend_layer = (
    alt.Chart(legend_source)
    .mark_circle(size=0, opacity=0)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        color=alt.Color(
            "category:N",
            scale=category_scale,
            legend=alt.Legend(
                title="Risk Category",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                symbolSize=300,
                orient="bottom-right",
                direction="vertical",
                fillColor="rgba(255,255,255,0.85)",
                strokeColor="#cccccc",
                padding=12,
                cornerRadius=6,
            ),
        ),
    )
)

# Combine all layers
chart = (
    alt.layer(heatmap, score_text, markers, labels, legend_layer)
    .properties(
        width=1100,
        height=1100,
        title=alt.Title(
            "heatmap-risk-matrix · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle=[
                "Project risk assessment — 15 risks plotted by likelihood and impact severity",
                "Risk Zones:  Low (1-4)  ·  Medium (5-9)  ·  High (10-16)  ·  Critical (20-25)",
            ],
            subtitleFontSize=17,
            subtitleColor="#666666",
            subtitlePadding=10,
        ),
    )
    .resolve_axis(x="independent", y="independent")
    .configure_view(strokeWidth=0)
    .configure(padding={"left": 30, "right": 30, "top": 20, "bottom": 40}, background="#ffffff")
    .configure_axis(labelColor="#444444", titleColor="#333333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
