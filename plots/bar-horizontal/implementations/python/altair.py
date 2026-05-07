""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-07
"""

import os

import altair as alt
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: Top 10 programming languages by popularity
data = pd.DataFrame(
    {
        "language": ["Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust", "Swift", "Kotlin"],
        "popularity": [28.5, 18.2, 15.8, 10.3, 8.7, 6.2, 4.8, 3.5, 2.4, 1.6],
    }
)

# Sort by popularity for better readability
data = data.sort_values("popularity", ascending=True)

# Create horizontal bar chart
chart = (
    alt.Chart(data)
    .mark_bar(color=BRAND, cornerRadiusEnd=4)
    .encode(
        x=alt.X("popularity:Q", title="Popularity (%)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "language:N", title="Programming Language", sort="-x", axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        tooltip=[
            alt.Tooltip("language:N", title="Language"),
            alt.Tooltip("popularity:Q", title="Popularity (%)", format=".1f"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("bar-horizontal · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT)
)

# Save PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
