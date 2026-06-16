""" anyplot.ai
subplot-grid: Subplot Grid Layout
Library: altair 6.1.0 | Python 3.13.13
Quality: 98/100 | Updated: 2026-05-13
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

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]
BRAND = IMPRINT[0]
SECONDARY = IMPRINT[1]

# Data
np.random.seed(42)

# Panel 1: Scatter plot - Product metrics
n_products = 50
products_df = pd.DataFrame(
    {
        "Units Sold": np.random.randint(100, 1000, n_products),
        "Revenue ($K)": np.random.uniform(10, 100, n_products),
        "Product": [f"P{i}" for i in range(n_products)],
    }
)

# Panel 2: Line plot - Monthly performance
months = pd.date_range("2024-01", periods=12, freq="ME")
monthly_df = pd.DataFrame(
    {"Month": months, "Sales": np.cumsum(np.random.normal(50, 15, 12)) + 500, "Target": np.linspace(500, 700, 12)}
)
monthly_df = monthly_df.melt(id_vars=["Month"], var_name="Metric", value_name="Value")

# Panel 3: Bar plot - Regional performance
regions_df = pd.DataFrame(
    {"Region": ["North", "South", "East", "West", "Central"], "Performance": [85, 72, 91, 68, 79]}
)

# Panel 4: Histogram - Distribution of order values
order_values = np.random.lognormal(mean=4.5, sigma=0.5, size=200)
histogram_df = pd.DataFrame({"Order Value ($)": order_values})

# Chart 1: Scatter plot
scatter = (
    alt.Chart(products_df)
    .mark_circle(size=120, opacity=0.7)
    .encode(
        x=alt.X("Units Sold:Q", title="Units Sold"),
        y=alt.Y("Revenue ($K):Q", title="Revenue ($K)"),
        color=alt.value(BRAND),
        tooltip=["Product", "Units Sold", "Revenue ($K)"],
    )
    .properties(width=750, height=420, title=alt.Title("Product Performance", fontSize=22, anchor="start"))
)

# Chart 2: Line plot
line = (
    alt.Chart(monthly_df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Month:T", title="Month"),
        y=alt.Y("Value:Q", title="Sales ($K)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Metric:N",
            scale=alt.Scale(domain=["Sales", "Target"], range=[BRAND, SECONDARY]),
            legend=alt.Legend(title="Metric", titleFontSize=16, labelFontSize=14),
        ),
        strokeDash=alt.StrokeDash(
            "Metric:N", scale=alt.Scale(domain=["Sales", "Target"], range=[[0], [5, 5]]), legend=None
        ),
    )
    .properties(width=750, height=420, title=alt.Title("Monthly Sales Trend", fontSize=22, anchor="start"))
)

# Chart 3: Bar plot
bar = (
    alt.Chart(regions_df)
    .mark_bar(size=60)
    .encode(
        x=alt.X("Region:N", title="Region", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Performance:Q", title="Performance Score", scale=alt.Scale(domain=[0, 100])),
        color=alt.condition(alt.datum.Performance >= 80, alt.value(BRAND), alt.value(SECONDARY)),
        tooltip=["Region", "Performance"],
    )
    .properties(width=750, height=420, title=alt.Title("Regional Performance", fontSize=22, anchor="start"))
)

# Chart 4: Histogram
histogram = (
    alt.Chart(histogram_df)
    .mark_bar(opacity=0.8)
    .encode(
        x=alt.X("Order Value ($):Q", bin=alt.Bin(maxbins=25), title="Order Value ($)"),
        y=alt.Y("count():Q", title="Frequency"),
        color=alt.value(BRAND),
        tooltip=[alt.Tooltip("count()", title="Count")],
    )
    .properties(width=750, height=420, title=alt.Title("Order Value Distribution", fontSize=22, anchor="start"))
)

# Combine into 2x2 grid
row1 = alt.hconcat(scatter, line, spacing=60)
row2 = alt.hconcat(bar, histogram, spacing=60)

chart = (
    alt.vconcat(row1, row2, spacing=60)
    .properties(
        background=PAGE_BG,
        title=alt.Title("subplot-grid · altair · anyplot.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_axis(
        labelFontSize=16,
        titleFontSize=18,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK, fontSize=22)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=16,
        labelFontSize=14,
    )
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
