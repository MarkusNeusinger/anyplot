""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import pandas as pd


# Data - Budget allocation example
categories = ["Marketing", "Operations", "R&D", "HR"]
values = [35, 28, 25, 12]  # Percentages (sum to 100)
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51"]

# Build 10x10 grid (100 squares, each = 1%)
squares = []
square_idx = 0
for cat, val, color in zip(categories, values, colors, strict=True):
    for _ in range(val):
        row = square_idx // 10
        col = square_idx % 10
        squares.append({"category": cat, "row": row, "col": col, "color": color})
        square_idx += 1

df = pd.DataFrame(squares)

# Create waffle chart
chart = (
    alt.Chart(df)
    .mark_rect(stroke="white", strokeWidth=3, cornerRadius=6)
    .encode(
        x=alt.X("col:O", axis=None),
        y=alt.Y("row:O", axis=None, sort="descending"),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=categories, range=colors),
            legend=alt.Legend(
                title="Category",
                titleFontSize=24,
                labelFontSize=20,
                symbolSize=500,
                orient="right",
                labelExpr="datum.label + ' (' + {"
                + ", ".join([f"'{cat}': '{val}%'" for cat, val in zip(categories, values, strict=True)])
                + "}[datum.label] + ')'",
            ),
        ),
        tooltip=["category:N"],
    )
    .properties(
        width=1200,
        height=900,
        title=alt.Title("Budget Allocation · waffle-basic · altair · pyplots.ai", fontSize=32, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
