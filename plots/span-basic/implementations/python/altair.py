""" anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-04-30
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

# Okabe-Ito data colors
BRAND = "#009E73"  # position 1 — main price line
SPAN1_COLOR = "#E69F00"  # position 5 — recession vertical span
SPAN2_COLOR = "#D55E00"  # position 2 — threshold horizontal span

# Data — stock price with recession dip and warning threshold zone
np.random.seed(42)
dates = pd.date_range(start="2007-01-01", periods=36, freq="MS")

base_price = 100
prices = [base_price]
for i in range(1, 36):
    if 12 <= i < 24:
        drift = -0.01
    else:
        drift = 0.008
    change = drift + np.random.randn() * 0.03
    prices.append(prices[-1] * (1 + change))

df = pd.DataFrame({"Date": dates, "Price": prices})

recession_start = pd.Timestamp("2008-01-01")
recession_end = pd.Timestamp("2009-12-01")
threshold_low = 85
threshold_high = 95

# Base line chart
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=4, color=BRAND)
    .encode(
        x=alt.X(
            "Date:T",
            title="Date",
            axis=alt.Axis(
                labelFontSize=18, titleFontSize=22, tickCount={"interval": "month", "step": 3}, format="%b %Y"
            ),
        ),
        y=alt.Y(
            "Price:Q",
            title="Stock Price ($)",
            scale=alt.Scale(domain=[60, 130]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        tooltip=[alt.Tooltip("Date:T", format="%b %Y"), alt.Tooltip("Price:Q", format=".2f", title="Price ($)")],
    )
)

points = (
    alt.Chart(df)
    .mark_point(size=150, color=BRAND, filled=True)
    .encode(
        x="Date:T",
        y=alt.Y("Price:Q", scale=alt.Scale(domain=[60, 130])),
        tooltip=[alt.Tooltip("Date:T", format="%b %Y"), alt.Tooltip("Price:Q", format=".2f", title="Price ($)")],
    )
)

# Vertical span — recession period
recession_span_data = pd.DataFrame({"start": [recession_start], "end": [recession_end]})
vertical_span = (
    alt.Chart(recession_span_data)
    .mark_rect(opacity=0.25, color=SPAN1_COLOR)
    .encode(x=alt.X("start:T"), x2=alt.X2("end:T"))
)

left_edge = (
    alt.Chart(pd.DataFrame({"x": [recession_start]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color=SPAN1_COLOR)
    .encode(x="x:T")
)

right_edge = (
    alt.Chart(pd.DataFrame({"x": [recession_end]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color=SPAN1_COLOR)
    .encode(x="x:T")
)

# Horizontal span — warning threshold zone
threshold_span_data = pd.DataFrame({"y": [threshold_low], "y2": [threshold_high]})
horizontal_span = (
    alt.Chart(threshold_span_data)
    .mark_rect(opacity=0.2, color=SPAN2_COLOR)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[60, 130])), y2=alt.Y2("y2:Q"))
)

bottom_edge = (
    alt.Chart(pd.DataFrame({"y": [threshold_low]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color=SPAN2_COLOR)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[60, 130])))
)

top_edge = (
    alt.Chart(pd.DataFrame({"y": [threshold_high]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color=SPAN2_COLOR)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[60, 130])))
)

# Text labels for span regions
recession_label = (
    alt.Chart(pd.DataFrame({"x": [pd.Timestamp("2008-07-01")], "y": [125], "text": ["Recession Period"]}))
    .mark_text(fontSize=18, fontWeight="bold", color=SPAN1_COLOR)
    .encode(x="x:T", y=alt.Y("y:Q", scale=alt.Scale(domain=[60, 130])), text="text:N")
)

threshold_label = (
    alt.Chart(pd.DataFrame({"x": [pd.Timestamp("2007-06-01")], "y": [90], "text": ["Warning Zone"]}))
    .mark_text(fontSize=16, fontWeight="bold", color=SPAN2_COLOR)
    .encode(x="x:T", y=alt.Y("y:Q", scale=alt.Scale(domain=[60, 130])), text="text:N")
)

# Combine all layers with theme-adaptive chrome
chart = (
    alt.layer(
        horizontal_span,
        bottom_edge,
        top_edge,
        vertical_span,
        left_edge,
        right_edge,
        line,
        points,
        recession_label,
        threshold_label,
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("span-basic · altair · anyplot.ai", fontSize=28, color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK_SOFT,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(color=INK, fontSize=28)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
