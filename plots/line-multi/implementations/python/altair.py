""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly sales for 4 product lines over 24 months
np.random.seed(42)

months = pd.date_range(start="2023-01-01", periods=24, freq="ME")

# Create distinct trends for each product line
base = np.linspace(100, 150, 24)
electronics = base + np.cumsum(np.random.randn(24) * 5) + 50
furniture = base * 0.8 + np.cumsum(np.random.randn(24) * 4)
clothing = base * 1.1 + np.sin(np.linspace(0, 4 * np.pi, 24)) * 20 + np.random.randn(24) * 3
books = base * 0.6 + np.cumsum(np.random.randn(24) * 3) - 20

# Long format for Altair
df = pd.DataFrame(
    {
        "Month": np.tile(months, 4),
        "Sales (thousands)": np.concatenate([electronics, furniture, clothing, books]),
        "Product": (["Electronics"] * 24 + ["Furniture"] * 24 + ["Clothing"] * 24 + ["Books"] * 24),
    }
)

# Color palette - Python Blue first, then colorblind-safe colors
colors = ["#306998", "#FFD43B", "#E15759", "#59A14F"]

# Create multi-line chart
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, point=alt.OverlayMarkDef(size=80, filled=True))
    .encode(
        x=alt.X("Month:T", title="Month", axis=alt.Axis(labelFontSize=18, titleFontSize=22, format="%b %Y")),
        y=alt.Y(
            "Sales (thousands):Q", title="Sales (thousands USD)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        color=alt.Color(
            "Product:N",
            scale=alt.Scale(range=colors),
            legend=alt.Legend(
                title="Product Line",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                symbolStrokeWidth=4,
                symbolSize=200,
            ),
        ),
        strokeDash=alt.StrokeDash("Product:N", legend=None),
    )
    .properties(
        width=1600, height=900, title=alt.Title(text="line-multi · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 px with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.interactive().save("plot.html")
