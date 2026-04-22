""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-17
"""

import altair as alt
import pandas as pd


# Data - Product sales comparing Q1 vs Q4 (10 products)
data = pd.DataFrame(
    {
        "Product": [
            "Laptop",
            "Phone",
            "Tablet",
            "Monitor",
            "Keyboard",
            "Mouse",
            "Headphones",
            "Webcam",
            "Speaker",
            "Charger",
        ],
        "Q1 Sales": [850, 1200, 420, 310, 580, 720, 390, 180, 260, 440],
        "Q4 Sales": [920, 980, 650, 410, 520, 810, 620, 350, 240, 380],
    }
)

# Reshape data to long format for slope chart
df_long = pd.melt(data, id_vars=["Product"], value_vars=["Q1 Sales", "Q4 Sales"], var_name="Period", value_name="Sales")

# Determine direction of change for color coding
data["Direction"] = data.apply(lambda row: "Increase" if row["Q4 Sales"] > row["Q1 Sales"] else "Decrease", axis=1)
df_long = df_long.merge(data[["Product", "Direction"]], on="Product")

# Create slope chart
lines = (
    alt.Chart(df_long)
    .mark_line(strokeWidth=3, opacity=0.8)
    .encode(
        x=alt.X("Period:N", axis=alt.Axis(labelFontSize=20, titleFontSize=24, title=None, labelAngle=0)),
        y=alt.Y(
            "Sales:Q",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, title="Sales (units)"),
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "Direction:N",
            scale=alt.Scale(domain=["Increase", "Decrease"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(titleFontSize=20, labelFontSize=18, orient="top-right"),
        ),
        detail="Product:N",
    )
)

# Add points at endpoints
points = (
    alt.Chart(df_long)
    .mark_circle(size=200, opacity=0.9)
    .encode(
        x="Period:N",
        y="Sales:Q",
        color=alt.Color(
            "Direction:N", scale=alt.Scale(domain=["Increase", "Decrease"], range=["#306998", "#FFD43B"]), legend=None
        ),
    )
)

# Add labels at left endpoint (Q1)
labels_left = (
    alt.Chart(df_long[df_long["Period"] == "Q1 Sales"])
    .mark_text(align="right", dx=-15, fontSize=16)
    .encode(
        x="Period:N",
        y="Sales:Q",
        text="Product:N",
        color=alt.Color(
            "Direction:N", scale=alt.Scale(domain=["Increase", "Decrease"], range=["#306998", "#FFD43B"]), legend=None
        ),
    )
)

# Add labels at right endpoint (Q4)
labels_right = (
    alt.Chart(df_long[df_long["Period"] == "Q4 Sales"])
    .mark_text(align="left", dx=15, fontSize=16)
    .encode(
        x="Period:N",
        y="Sales:Q",
        text="Product:N",
        color=alt.Color(
            "Direction:N", scale=alt.Scale(domain=["Increase", "Decrease"], range=["#306998", "#FFD43B"]), legend=None
        ),
    )
)

# Combine layers
chart = (
    (lines + points + labels_left + labels_right)
    .properties(
        width=1400, height=850, title=alt.Title(text="slope-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 × 2700 px) and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
