""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
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

# Okabe-Ito palette for categorical data
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

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

# Create multi-line chart
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, point=alt.OverlayMarkDef(size=100, filled=True))
    .encode(
        x=alt.X(
            "Month:T",
            title="Month",
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                format="%b %Y",
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
            ),
        ),
        y=alt.Y(
            "Sales (thousands):Q",
            title="Sales (thousands USD)",
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                labelColor=INK_SOFT,
                titleColor=INK,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
                gridOpacity=0.10,
                gridColor=INK,
            ),
        ),
        color=alt.Color(
            "Product:N",
            scale=alt.Scale(range=IMPRINT),
            legend=alt.Legend(
                title="Product Line",
                titleFontSize=20,
                titleColor=INK,
                labelFontSize=18,
                labelColor=INK_SOFT,
                orient="right",
                symbolStrokeWidth=4,
                symbolSize=200,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
            ),
        ),
        tooltip=["Month:T", "Sales (thousands):Q", "Product:N"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="line-multi · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(gridDash=[4, 4])
)

# Save as PNG (4800 x 2700 px with scale_factor=3)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.interactive().save(f"plot-{THEME}.html")
