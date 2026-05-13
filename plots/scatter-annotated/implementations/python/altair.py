""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-13
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Selected tech companies showing range of revenue/profit metrics
np.random.seed(42)
companies = ["NVIDIA", "Apple", "Microsoft", "Amazon", "Google", "Meta", "Adobe", "Oracle", "Tesla", "Intel"]
# Revenue (billions USD) - realistic values
revenue = np.array([61, 385, 211, 574, 307, 135, 19, 50, 97, 63])
# Profit margin (%) - realistic values
profit_margin = np.array([55, 25, 35, 6, 22, 20, 34, 26, 11, 8])

df = pd.DataFrame({"company": companies, "revenue": revenue, "profit_margin": profit_margin})

# Points layer with Okabe-Ito brand color
points = (
    alt.Chart(df)
    .mark_point(size=250, filled=True, opacity=0.7, color=BRAND)
    .encode(
        x=alt.X("revenue:Q", title="Revenue (Billions USD)", scale=alt.Scale(domain=[0, 620])),
        y=alt.Y("profit_margin:Q", title="Profit Margin (%)", scale=alt.Scale(domain=[0, 60])),
        tooltip=["company:N", "revenue:Q", "profit_margin:Q"],
    )
)

# Connector lines from points to labels
connector_lines = (
    alt.Chart(df)
    .mark_line(size=1, opacity=0.3, color=INK_SOFT)
    .encode(x="revenue:Q", y="profit_margin:Q", x2=alt.X2("revenue:Q"), y2=alt.Y2("profit_margin:Q"))
)

# Text labels layer with theme-adaptive color
labels = (
    alt.Chart(df)
    .mark_text(align="left", dx=12, dy=-8, fontSize=18, fontWeight="bold", color=INK)
    .encode(x=alt.X("revenue:Q"), y=alt.Y("profit_margin:Q"), text="company:N")
)

# Combine layers with theme-adaptive styling
chart = (
    (points + connector_lines + labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="scatter-annotated · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG (4800x2700 with scale_factor=3)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save(f"plot-{THEME}.html")
