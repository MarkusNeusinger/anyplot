""" anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-13
"""

import os
import sys


script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir and p != ""]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"

np.random.seed(42)
products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"]
central_values = np.array([85.2, 72.8, 91.5, 68.3, 78.9, 82.1])
error_lower = np.array([5.2, 8.1, 3.8, 9.5, 6.3, 4.9])
error_upper = np.array([8.7, 4.3, 6.2, 5.8, 10.1, 7.6])

df = pd.DataFrame(
    {
        "Product": products,
        "Quality Score": central_values,
        "Lower": central_values - error_lower,
        "Upper": central_values + error_upper,
    }
)

error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, color=BRAND)
    .encode(
        x=alt.X("Product:N", title="Product", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "Lower:Q",
            title="Quality Score (10th–90th Percentile)",
            scale=alt.Scale(domain=[50, 105]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        y2=alt.Y2("Upper:Q"),
    )
)

lower_caps = alt.Chart(df).mark_tick(size=30, thickness=3, color=BRAND).encode(x=alt.X("Product:N"), y=alt.Y("Lower:Q"))

upper_caps = alt.Chart(df).mark_tick(size=30, thickness=3, color=BRAND).encode(x=alt.X("Product:N"), y=alt.Y("Upper:Q"))

points = (
    alt.Chart(df)
    .mark_point(size=300, filled=True, color=BRAND, stroke=INK_SOFT, strokeWidth=2)
    .encode(
        x=alt.X("Product:N"),
        y=alt.Y("Quality Score:Q"),
        tooltip=[
            alt.Tooltip("Product:N", title="Product"),
            alt.Tooltip("Quality Score:Q", title="Quality Score", format=".1f"),
            alt.Tooltip("Lower:Q", title="10th Percentile", format=".1f"),
            alt.Tooltip("Upper:Q", title="90th Percentile", format=".1f"),
        ],
    )
)

annotation = (
    alt.Chart(pd.DataFrame({"x": ["Product F"], "y": [53], "text": ["Error bars show 10th–90th percentile range"]}))
    .mark_text(fontSize=16, fontStyle="italic", color=INK_MUTED, align="right")
    .encode(x=alt.X("x:N"), y=alt.Y("y:Q"), text="text:N")
)

chart = (
    alt.layer(error_bars, lower_caps, upper_caps, points, annotation)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("errorbar-asymmetric · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        grid=True,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        gridColor=INK_SOFT,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
