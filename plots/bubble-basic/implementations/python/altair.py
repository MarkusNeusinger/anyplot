""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-02-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data — tech startup metrics: funding vs revenue, sized by employees, colored by stage
np.random.seed(42)
n = 40

stages = np.random.choice(["Seed", "Series A", "Series B", "Growth"], size=n, p=[0.25, 0.30, 0.25, 0.20])

# Base funding depends on stage — spread across full range
stage_funding = {"Seed": (6, 4), "Series A": (18, 7), "Series B": (38, 10), "Growth": (60, 12)}
funding_m = np.array([np.random.normal(*stage_funding[s]) for s in stages])
funding_m = np.clip(funding_m, 1, 80)

# Revenue correlates with funding plus noise
revenue_m = funding_m * np.random.uniform(0.7, 1.5, size=n) + np.random.normal(5, 3, size=n)
revenue_m = np.clip(revenue_m, 2, 100)

# Employees scale with funding stage
stage_emp = {"Seed": (25, 10), "Series A": (80, 35), "Series B": (250, 90), "Growth": (550, 150)}
employees = np.array([int(np.clip(np.random.normal(*stage_emp[s]), 15, 900)) for s in stages])

df = pd.DataFrame(
    {
        "Funding ($M)": np.round(funding_m, 1),
        "Revenue ($M)": np.round(revenue_m, 1),
        "Employees": employees,
        "Stage": pd.Categorical(stages, categories=["Seed", "Series A", "Series B", "Growth"], ordered=True),
    }
)

# Flag top-3 companies by revenue for annotation
top3_idx = df["Revenue ($M)"].nlargest(3).index
df["label"] = ""
for i in top3_idx:
    df.loc[i, "label"] = f"{df.loc[i, 'Stage']} · ${df.loc[i, 'Funding ($M)']}M"

# Cohesive palette starting with Python Blue — warm progression through stages
stage_colors = ["#306998", "#4B8BBE", "#E8A838", "#D35F2D"]

# Base bubble layer
bubbles = (
    alt.Chart(df)
    .mark_circle(stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X(
            "Funding ($M):Q",
            scale=alt.Scale(domain=[0, 85], nice=False),
            axis=alt.Axis(
                gridDash=[3, 3], gridColor="#dcdcdc", gridOpacity=0.6, domainWidth=0, tickSize=6, tickColor="#bbbbbb"
            ),
        ),
        y=alt.Y(
            "Revenue ($M):Q",
            scale=alt.Scale(domain=[0, 110], nice=False),
            axis=alt.Axis(
                gridDash=[3, 3], gridColor="#dcdcdc", gridOpacity=0.6, domainWidth=0, tickSize=6, tickColor="#bbbbbb"
            ),
        ),
        size=alt.Size(
            "Employees:Q",
            scale=alt.Scale(range=[80, 3000], domain=[15, 900]),
            legend=alt.Legend(
                title="Employees",
                titleFontSize=18,
                labelFontSize=16,
                values=[50, 200, 500, 900],
                symbolFillColor="#306998",
                symbolStrokeColor="white",
                symbolOpacity=0.7,
                direction="vertical",
            ),
        ),
        color=alt.Color(
            "Stage:N",
            scale=alt.Scale(domain=["Seed", "Series A", "Series B", "Growth"], range=stage_colors),
            legend=alt.Legend(
                title="Stage",
                titleFontSize=18,
                labelFontSize=16,
                symbolType="circle",
                symbolSize=350,
                symbolStrokeWidth=0,
                symbolOpacity=0.7,
            ),
        ),
        opacity=alt.condition(alt.datum.label != "", alt.value(0.85), alt.value(0.55)),
        tooltip=["Stage:N", "Funding ($M):Q", "Revenue ($M):Q", "Employees:Q"],
    )
)

# Annotation layer for top revenue companies — storytelling emphasis
annotations = (
    alt.Chart(df[df["label"] != ""])
    .mark_text(align="left", dx=14, dy=-10, fontSize=14, fontWeight="bold", color="#333333")
    .encode(x="Funding ($M):Q", y="Revenue ($M):Q", text="label:N")
)

# Combine layers
chart = (
    (bubbles + annotations)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "bubble-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle="Tech Startup Metrics — Funding vs Revenue by Stage & Team Size",
            subtitleFontSize=18,
            subtitleColor="#666666",
            subtitlePadding=6,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, titleColor="#444444", labelColor="#555555")
    .configure_view(strokeWidth=0, fill="#fafbfc")
    .configure_legend(orient="right", padding=15, titleColor="#444444", labelColor="#555555")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
