""" anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-06
"""

import os

import altair as alt
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for waterfall types
POSITIVE_COLOR = "#009E73"  # Position 1: brand green for positive
NEGATIVE_COLOR = "#D55E00"  # Position 2: vermillion/red for negative
TOTAL_COLOR = "#0072B2"  # Position 3: blue for totals

# Data: Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Cost of Goods", "Gross Profit", "Operating Expenses", "Other Income", "Taxes", "Net Income"]
values = [500, -200, None, -150, 25, -45, None]

# Calculate running totals and bar positions
n = len(categories)
running_total = [0] * n
bar_bottom = [0] * n
bar_top = [0] * n
bar_types = []

running_total[0] = values[0]
bar_bottom[0] = 0
bar_top[0] = values[0]
bar_types.append("total")

current = values[0]
for i in range(1, n):
    if values[i] is None:
        running_total[i] = current
        bar_bottom[i] = 0
        bar_top[i] = current
        bar_types.append("total")
    else:
        running_total[i] = current + values[i]
        if values[i] >= 0:
            bar_bottom[i] = current
            bar_top[i] = current + values[i]
            bar_types.append("positive")
        else:
            bar_bottom[i] = current + values[i]
            bar_top[i] = current
            bar_types.append("negative")
        current = running_total[i]

# Create display values for labels
display_values = []
for i, val in enumerate(values):
    if val is None:
        display_values.append(f"${int(running_total[i])}")
    elif val >= 0:
        display_values.append(f"+${int(val)}")
    else:
        display_values.append(f"-${int(abs(val))}")

# Create DataFrame for bars
df = pd.DataFrame(
    {
        "category": categories,
        "bar_bottom": bar_bottom,
        "bar_top": bar_top,
        "bar_type": bar_types,
        "running_total": running_total,
        "display_value": display_values,
        "order": list(range(n)),
        "label_y": [(b + t) / 2 for b, t in zip(bar_bottom, bar_top, strict=True)],
    }
)

# Color scale using Okabe-Ito palette
color_scale = alt.Scale(domain=["total", "positive", "negative"], range=[TOTAL_COLOR, POSITIVE_COLOR, NEGATIVE_COLOR])

# Sort by order field
sort_order = alt.EncodingSortField(field="order", order="ascending")

# Create bar chart using bar marks with y and y2
bars = (
    alt.Chart(df)
    .mark_bar(size=65, stroke=INK_SOFT, strokeWidth=2)
    .encode(
        x=alt.X(
            "category:N",
            sort=sort_order,
            title="Category",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=-20),
        ),
        y=alt.Y("bar_bottom:Q", title="Amount ($)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y2=alt.Y2("bar_top:Q"),
        color=alt.Color("bar_type:N", scale=color_scale, legend=None),
    )
)

# Value labels on bars
labels = (
    alt.Chart(df)
    .mark_text(fontSize=18, fontWeight="bold", color=INK)
    .encode(x=alt.X("category:N", sort=sort_order), y=alt.Y("label_y:Q"), text="display_value:N")
)

# Create connector lines data
connector_data = []
for i in range(n - 1):
    connector_data.append(
        {"x": categories[i], "x2": categories[i + 1], "y": running_total[i], "order_x": i, "order_x2": i + 1}
    )

df_connectors = pd.DataFrame(connector_data)

# Connector lines using rule mark
connectors = (
    alt.Chart(df_connectors)
    .mark_rule(color=INK_SOFT, strokeDash=[6, 4], strokeWidth=2)
    .encode(x=alt.X("x:N", sort=sort_order), x2=alt.X2("x2:N"), y=alt.Y("y:Q"))
)

# Combine all layers
chart = (
    alt.layer(connectors, bars, labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("waterfall-basic · altair · anyplot.ai", fontSize=28, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, continuousWidth=1600, continuousHeight=900)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
)

# Save as PNG and HTML with theme suffix
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
