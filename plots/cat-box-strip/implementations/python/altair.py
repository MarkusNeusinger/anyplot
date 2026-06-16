""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-13
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Product quality scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
data = []

# Create varied distributions per department
for dept in departments:
    if dept == "Engineering":
        # Higher scores, tight distribution
        values = np.random.normal(85, 6, 40)
    elif dept == "Marketing":
        # Medium scores, wider spread
        values = np.random.normal(72, 12, 35)
        # Add some outliers
        values = np.append(values, [45, 48, 98])
    elif dept == "Sales":
        # Lower scores, moderate spread
        values = np.random.normal(65, 10, 45)
        # Add outliers
        values = np.append(values, [35, 92, 95])
    else:  # Support
        # Bimodal distribution
        values = np.concatenate([np.random.normal(60, 8, 20), np.random.normal(80, 5, 25)])

    for v in values:
        data.append({"Department": dept, "Quality Score": np.clip(v, 30, 100), "Series": "Data Point"})

df = pd.DataFrame(data)

# Box plot layer
boxplot = (
    alt.Chart(df)
    .mark_boxplot(size=60, color=BRAND, median={"color": "#954477", "strokeWidth": 3}, opacity=0.8)
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "Quality Score:Q",
            title="Quality Score",
            scale=alt.Scale(domain=[25, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
    )
)

# Strip plot layer with jitter
strip = (
    alt.Chart(df)
    .mark_circle(size=100, color=BRAND, opacity=0.6)
    .encode(
        x=alt.X("Department:N"),
        y=alt.Y("Quality Score:Q"),
        xOffset="jitter:Q",
        tooltip=["Department:N", alt.Tooltip("Quality Score:Q", format=".1f")],
    )
    .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())*15")
)

# Combine layers
chart = (
    alt.layer(boxplot, strip)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("cat-box-strip · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_title(color=INK)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
