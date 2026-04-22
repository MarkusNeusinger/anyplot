""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import altair as alt
import pandas as pd


# Data: Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Cost of Goods", "Gross Profit", "Operating Expenses", "Other Income", "Taxes", "Net Income"]
# Values: First and last are totals (None), middle values are changes
values = [500, -200, None, -150, 25, -45, None]

# Calculate running totals and bar positions
n = len(categories)
running_total = [0] * n
bar_bottom = [0] * n
bar_top = [0] * n
bar_types = []  # 'total', 'positive', 'negative'

running_total[0] = values[0]
bar_bottom[0] = 0
bar_top[0] = values[0]
bar_types.append("total")

current = values[0]
for i in range(1, n):
    if values[i] is None:
        # Subtotal bar (Gross Profit or Net Income)
        running_total[i] = current
        bar_bottom[i] = 0
        bar_top[i] = current
        bar_types.append("total")
    else:
        # Change bar
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

# Create display values for labels (show change for non-totals, running total for totals)
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

# Color scale: Python Blue for totals, green for positive, red for negative
color_scale = alt.Scale(domain=["total", "positive", "negative"], range=["#306998", "#4CAF50", "#E53935"])

# Sort by order field
sort_order = alt.EncodingSortField(field="order", order="ascending")

# Create bar chart using bar marks with y and y2
bars = (
    alt.Chart(df)
    .mark_bar(size=65, stroke="white", strokeWidth=2)
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
    .mark_text(fontSize=18, fontWeight="bold", color="white")
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
    .mark_rule(color="#666666", strokeDash=[6, 4], strokeWidth=2)
    .encode(x=alt.X("x:N", sort=sort_order), x2=alt.X2("x2:N"), y=alt.Y("y:Q"))
)

# Combine all layers
chart = (
    alt.layer(connectors, bars, labels)
    .properties(width=1600, height=900, title=alt.Title("waterfall-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
