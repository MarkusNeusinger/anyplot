""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-06
"""

import os
import sys

import pandas as pd


# Remove current directory from path to avoid local altair.py shadowing
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != script_dir and os.path.abspath(p) != script_dir]

import altair as alt  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1→3)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Quarterly revenue by product line
data = pd.DataFrame(
    {
        "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
        "Product": ["Software", "Hardware", "Services"] * 4,
        "Revenue": [
            120,
            85,
            45,  # Q1
            145,
            78,
            52,  # Q2
            132,
            92,
            68,  # Q3
            168,
            105,
            75,  # Q4
        ],
    }
)

# Create grouped bar chart
chart = (
    alt.Chart(data)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X(
            "Quarter:O",
            title="Quarter",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelColor=INK_SOFT, titleColor=INK),
        ),
        xOffset="Product:N",
        y=alt.Y(
            "Revenue:Q",
            title="Revenue (thousands USD)",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelColor=INK_SOFT, titleColor=INK),
        ),
        color=alt.Color(
            "Product:N",
            scale=alt.Scale(domain=["Software", "Hardware", "Services"], range=IMPRINT),
            legend=alt.Legend(
                title="Product Line", titleFontSize=20, labelFontSize=18, orient="bottom", direction="horizontal"
            ),
        ),
        tooltip=["Quarter", "Product", "Revenue"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("bar-grouped · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
