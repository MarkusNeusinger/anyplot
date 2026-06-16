""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
"""

import os
import sys


# Prevent import collision with this script's filename
sys.path = [p for p in sys.path if not p.endswith("/python")]

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
POSITIVE_COLOR = "#009E73"  # Okabe-Ito position 1 (brand green)
NEGATIVE_COLOR = "#AE3030"  # imprint red — negative

# Data - Customer satisfaction survey results by department
data = pd.DataFrame(
    {
        "department": [
            "Customer Service",
            "Engineering",
            "Sales",
            "Marketing",
            "HR",
            "Finance",
            "Operations",
            "IT Support",
            "R&D",
            "Quality Assurance",
            "Legal",
            "Logistics",
        ],
        "satisfaction_score": [42, 35, 28, 15, 8, -5, -12, -18, -25, -32, -38, -45],
    }
)

# Add color indicator for positive/negative
data["sentiment"] = data["satisfaction_score"].apply(lambda x: "Positive" if x >= 0 else "Negative")

# Sort by value for better pattern recognition
data = data.sort_values("satisfaction_score", ascending=True)

# Create diverging bar chart
chart = (
    alt.Chart(data)
    .mark_bar(cornerRadius=3, height=35)
    .encode(
        x=alt.X(
            "satisfaction_score:Q",
            title="Net Satisfaction Score",
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10),
            scale=alt.Scale(domain=[-60, 60]),
        ),
        y=alt.Y(
            "department:N",
            title=None,
            sort=alt.EncodingSortField(field="satisfaction_score", order="ascending"),
            axis=alt.Axis(labelFontSize=18),
        ),
        color=alt.Color(
            "sentiment:N",
            scale=alt.Scale(domain=["Positive", "Negative"], range=[POSITIVE_COLOR, NEGATIVE_COLOR]),
            legend=alt.Legend(title="Sentiment", titleFontSize=20, labelFontSize=18, orient="bottom-right", offset=10),
        ),
        tooltip=[alt.Tooltip("department:N", title="Department"), alt.Tooltip("satisfaction_score:Q", title="Score")],
    )
    .properties(
        width=1400, height=800, title=alt.Title("bar-diverging · altair · anyplot.ai", fontSize=28, anchor="middle")
    )
)

# Add zero baseline rule with theme-adaptive color
zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=INK_SOFT, strokeWidth=2).encode(x="x:Q")

# Combine chart and zero line with theme-adaptive styling
final_chart = (
    (chart + zero_line)
    .properties(background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        grid=True,
        gridOpacity=0.10,
        gridColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK, anchor="middle")
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG and HTML with theme-suffixed filenames
final_chart.save(f"plot-{THEME}.png", scale_factor=3.0)
final_chart.save(f"plot-{THEME}.html")
