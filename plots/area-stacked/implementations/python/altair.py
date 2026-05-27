""" anyplot.ai
area-stacked: Stacked Area Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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

# Okabe-Ito palette: first series ALWAYS #009E73
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Create stacked area chart
chart = (
    alt.Chart(df)
    .mark_area(opacity=0.85, line=alt.MarkConfig(strokeWidth=2))
    .encode(
        x=alt.X(
            "Month:T",
            title="Month",
            axis=alt.Axis(
                labelFontSize=18, titleFontSize=22, format="%b %Y", labelAngle=-45, labelColor=INK_SOFT, titleColor=INK
            ),
        ),
        y=alt.Y(
            "Revenue:Q",
            title="Revenue ($ thousands)",
            stack="zero",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelColor=INK_SOFT, titleColor=INK),
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
                labelColor=INK_SOFT,
                titleColor=INK,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
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
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("area-stacked · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, grid=True, gridColor=INK, gridOpacity=0.10)
    .configure_view(stroke=None, fill=PAGE_BG)
)

# Save as PNG (1600 * 3 = 4800, 900 * 3 = 2700)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.interactive().save(f"plot-{THEME}.html")
