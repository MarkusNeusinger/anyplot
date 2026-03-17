""" pyplots.ai
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

# Background grid: all 25 cells with risk scores
grid_rows = []
for li in range(1, 6):
    for im in range(1, 6):
        score = li * im
        grid_rows.append(
            {"likelihood": likelihood_labels[li - 1], "impact": impact_labels[im - 1], "risk_score": score}
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

# Pixel jitter to separate overlapping markers within cells
risk_df["jx"] = np.random.uniform(-55, 55, len(risk_df)).astype(int)
risk_df["jy"] = np.random.uniform(-40, 40, len(risk_df)).astype(int)

# Color scale: green → yellow → orange → red
color_scale = alt.Scale(
    domain=[1, 5, 10, 16, 25], range=["#4caf50", "#c6d93e", "#ff9800", "#f44336", "#b71c1c"], interpolate="lab"
)

x_sort = impact_labels
y_sort = likelihood_labels

category_scale = alt.Scale(domain=["Technical", "Financial", "Operational"], range=["#306998", "#e8871e", "#7b2d8e"])

# Heatmap background cells
heatmap = (
    alt.Chart(grid_df)
    .mark_rect(stroke="#ffffff", strokeWidth=3, cornerRadius=4)
    .encode(
        x=alt.X(
            "impact:O",
            title="Impact",
            sort=x_sort,
            axis=alt.Axis(
                labelFontSize=17,
                titleFontSize=22,
                titleFontWeight="bold",
                labelAngle=0,
                domainWidth=0,
                tickWidth=0,
                titlePadding=16,
                labelPadding=10,
            ),
        ),
        y=alt.Y(
            "likelihood:O",
            title="Likelihood",
            sort=y_sort,
            axis=alt.Axis(
                labelFontSize=17,
                titleFontSize=22,
                titleFontWeight="bold",
                domainWidth=0,
                tickWidth=0,
                titlePadding=16,
                labelPadding=10,
            ),
        ),
        color=alt.Color("risk_score:Q", scale=color_scale, legend=None),
    )
)

# Risk score text in each cell
score_text = (
    alt.Chart(grid_df)
    .mark_text(fontSize=28, fontWeight="bold", opacity=0.18)
    .encode(
        x=alt.X("impact:O", sort=x_sort),
        y=alt.Y("likelihood:O", sort=y_sort),
        text=alt.Text("risk_score:Q"),
        color=alt.condition(
            alt.datum.risk_score > 12, alt.value("rgba(255,255,255,0.6)"), alt.value("rgba(0,0,0,0.3)")
        ),
    )
)

# Risk markers and labels — per-item dx/dy for jitter within ordinal cells
risk_layers = []
for _, row in risk_df.iterrows():
    single = pd.DataFrame([row])
    dx, dy = int(row["jx"]), int(row["jy"])

    risk_layers.append(
        alt.Chart(single)
        .mark_circle(size=500, stroke="#ffffff", strokeWidth=2.5, opacity=0.92, dx=dx, dy=dy)
        .encode(
            x=alt.X("impact:O", sort=x_sort),
            y=alt.Y("likelihood:O", sort=y_sort),
            color=alt.Color("category:N", scale=category_scale, legend=None),
            tooltip=[
                alt.Tooltip("risk_name:N", title="Risk"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("likelihood:N", title="Likelihood"),
                alt.Tooltip("impact:N", title="Impact"),
            ],
        )
    )
    risk_layers.append(
        alt.Chart(single)
        .mark_text(fontSize=11, fontWeight="bold", dx=dx, dy=dy - 16)
        .encode(
            x=alt.X("impact:O", sort=x_sort),
            y=alt.Y("likelihood:O", sort=y_sort),
            text=alt.Text("risk_name:N"),
            color=alt.value("#222222"),
        )
    )

# Invisible layer to generate the category legend
legend_source = pd.DataFrame(
    {"category": ["Technical", "Financial", "Operational"], "impact": ["Negligible"] * 3, "likelihood": ["Rare"] * 3}
)
legend_layer = (
    alt.Chart(legend_source)
    .mark_circle(size=0, opacity=0)
    .encode(
        x=alt.X("impact:O", sort=x_sort),
        y=alt.Y("likelihood:O", sort=y_sort),
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
    alt.layer(heatmap, score_text, *risk_layers, legend_layer)
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
    .configure_view(strokeWidth=0)
    .configure(padding={"left": 30, "right": 30, "top": 20, "bottom": 30}, background="#ffffff")
    .configure_axis(labelColor="#444444", titleColor="#333333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
