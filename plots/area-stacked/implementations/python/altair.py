""" pyplots.ai
area-stacked: Stacked Area Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Monthly revenue by product category over two years
np.random.seed(42)
months = pd.date_range("2023-01", periods=24, freq="MS")

# Generate realistic revenue data with trends
base_software = 120 + np.cumsum(np.random.randn(24) * 5)
base_hardware = 80 + np.cumsum(np.random.randn(24) * 4)
base_services = 50 + np.cumsum(np.random.randn(24) * 3)
base_support = 30 + np.cumsum(np.random.randn(24) * 2)

# Ensure all values are positive
software = np.maximum(base_software, 20)
hardware = np.maximum(base_hardware, 15)
services = np.maximum(base_services, 10)
support = np.maximum(base_support, 5)

# Create long-form data for Altair
df = pd.DataFrame(
    {
        "Month": list(months) * 4,
        "Revenue": np.concatenate([software, hardware, services, support]),
        "Category": (["Software"] * 24 + ["Hardware"] * 24 + ["Services"] * 24 + ["Support"] * 24),
    }
)

# Define category order (largest at bottom for easier reading)
# Stack order: 1=bottom, 4=top
category_order = ["Software", "Hardware", "Services", "Support"]
stack_order = {"Software": 1, "Hardware": 2, "Services": 3, "Support": 4}
df["StackOrder"] = df["Category"].map(stack_order)

# Color palette: Python Blue, Python Yellow, and colorblind-safe colors
colors = ["#306998", "#FFD43B", "#5D9B9B", "#A85C5C"]

# Create stacked area chart
chart = (
    alt.Chart(df)
    .mark_area(opacity=0.85, line=alt.MarkConfig(strokeWidth=2))
    .encode(
        x=alt.X(
            "Month:T", title="Month", axis=alt.Axis(labelFontSize=18, titleFontSize=22, format="%b %Y", labelAngle=-45)
        ),
        y=alt.Y(
            "Revenue:Q", title="Revenue ($ thousands)", stack="zero", axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        color=alt.Color(
            "Category:N",
            scale=alt.Scale(domain=category_order, range=colors),
            legend=alt.Legend(
                title="Product Category",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                symbolSize=300,
                symbolStrokeWidth=0,
            ),
        ),
        order=alt.Order("StackOrder:Q", sort="ascending"),
        tooltip=[
            alt.Tooltip("Month:T", title="Month", format="%B %Y"),
            alt.Tooltip("Category:N", title="Category"),
            alt.Tooltip("Revenue:Q", title="Revenue ($k)", format=".1f"),
        ],
    )
    .properties(
        width=1400, height=800, title=alt.Title("area-stacked · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1400 * 3 = 4200, 800 * 3 = 2400 ≈ target size)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.interactive().save("plot.html")
