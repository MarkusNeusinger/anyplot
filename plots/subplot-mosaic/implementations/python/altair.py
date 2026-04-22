""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Create diverse datasets for dashboard-style mosaic layout
np.random.seed(42)

# Panel A: Wide time series (top, spanning 2 columns)
dates = pd.date_range("2024-01-01", periods=100, freq="D")
df_timeseries = pd.DataFrame(
    {"date": dates, "value": np.cumsum(np.random.randn(100)) + 50, "category": "Revenue Trend"}
)

# Panel B: Small metric (top right corner)
df_gauge = pd.DataFrame({"metric": ["Current"], "value": [78], "max_value": [100]})

# Panel C: Bar chart (middle left)
df_bars = pd.DataFrame({"region": ["North", "South", "East", "West", "Central"], "sales": [45, 38, 52, 29, 41]})

# Panel D: Scatter plot (middle right, spanning 2 rows)
n_points = 80
df_scatter = pd.DataFrame(
    {
        "efficiency": np.random.uniform(60, 95, n_points),
        "output": np.random.uniform(100, 500, n_points) + np.random.uniform(60, 95, n_points) * 3,
        "size": np.random.uniform(20, 100, n_points),
    }
)

# Panel E: Small bar chart (bottom left)
df_categories = pd.DataFrame({"type": ["Type A", "Type B", "Type C"], "count": [24, 18, 31]})

# Panel F: Small area chart (bottom middle)
df_area = pd.DataFrame(
    {
        "hour": list(range(24)),
        "traffic": [10, 8, 5, 4, 6, 15, 35, 55, 48, 42, 38, 45, 50, 48, 52, 60, 65, 55, 40, 30, 25, 20, 15, 12],
    }
)

# Note: Data is small enough to not need max_rows configuration

# Create individual charts with proper styling

# Chart A: Wide time series (spans 2 columns at top)
chart_a = (
    alt.Chart(df_timeseries)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
        y=alt.Y("value:Q", title="Revenue ($K)", axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
    )
    .properties(width=700, height=200, title=alt.Title("Monthly Revenue Overview", fontSize=20))
)

# Chart B: Gauge-style metric (small, top right)
chart_b_bg = (
    alt.Chart(df_gauge).mark_arc(innerRadius=50, outerRadius=80, theta=3.14159, theta2=0, color="#E0E0E0").encode()
)

chart_b_value = (
    alt.Chart(df_gauge)
    .mark_arc(
        innerRadius=50,
        outerRadius=80,
        theta=3.14159,
        theta2=alt.expr("3.14159 - (datum.value / datum.max_value) * 3.14159"),
        color="#306998",
    )
    .encode()
)

chart_b_text = (
    alt.Chart(df_gauge)
    .mark_text(fontSize=28, fontWeight="bold", color="#306998")
    .encode(text=alt.Text("value:Q", format=".0f"))
)

chart_b = alt.layer(chart_b_bg, chart_b_value, chart_b_text).properties(
    width=200, height=200, title=alt.Title("Performance Score", fontSize=18)
)

# Chart C: Bar chart (middle left)
chart_c = (
    alt.Chart(df_bars)
    .mark_bar(color="#306998", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("region:N", title="Region", axis=alt.Axis(labelFontSize=14, titleFontSize=16, labelAngle=0)),
        y=alt.Y("sales:Q", title="Sales ($K)", axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
    )
    .properties(width=280, height=180, title=alt.Title("Sales by Region", fontSize=18))
)

# Chart D: Scatter plot (spans 2 rows on right side)
chart_d = (
    alt.Chart(df_scatter)
    .mark_circle(opacity=0.7)
    .encode(
        x=alt.X(
            "efficiency:Q",
            title="Efficiency (%)",
            scale=alt.Scale(domain=[55, 100]),
            axis=alt.Axis(labelFontSize=14, titleFontSize=16),
        ),
        y=alt.Y("output:Q", title="Output (units)", axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
        size=alt.Size("size:Q", scale=alt.Scale(range=[50, 300]), legend=None),
        color=alt.Color("efficiency:Q", scale=alt.Scale(scheme="blues"), legend=None),
    )
    .properties(width=320, height=400, title=alt.Title("Efficiency vs Output", fontSize=18))
)

# Chart E: Small bar chart (bottom left)
chart_e = (
    alt.Chart(df_categories)
    .mark_bar(color="#FFD43B")
    .encode(
        x=alt.X("type:N", title=None, axis=alt.Axis(labelFontSize=12, labelAngle=0)),
        y=alt.Y("count:Q", title="Count", axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
    )
    .properties(width=180, height=160, title=alt.Title("By Category", fontSize=16))
)

# Chart F: Area chart (bottom middle)
chart_f = (
    alt.Chart(df_area)
    .mark_area(color="#306998", opacity=0.7, line={"color": "#306998", "strokeWidth": 2})
    .encode(
        x=alt.X("hour:Q", title="Hour", axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
        y=alt.Y("traffic:Q", title="Traffic", axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
    )
    .properties(width=200, height=160, title=alt.Title("Daily Traffic Pattern", fontSize=16))
)

# Build mosaic layout using Altair's concatenation
# Layout pattern: "AAB"
#                 "CDD"
#                 "EFD"

# Top row: time series (wide) + gauge
top_row = alt.hconcat(chart_a, chart_b, spacing=20)

# Middle row: bars + scatter (scatter spans into bottom row via vconcat)
# Bottom row: categories + area (scatter continues from middle)

# Left column for middle and bottom rows
left_middle = chart_c
left_bottom = alt.hconcat(chart_e, chart_f, spacing=15)
left_column = alt.vconcat(left_middle, left_bottom, spacing=15)

# Right side is the tall scatter plot
middle_bottom_row = alt.hconcat(left_column, chart_d, spacing=20)

# Combine all rows
mosaic = (
    alt.vconcat(top_row, middle_bottom_row, spacing=25)
    .properties(title=alt.Title("subplot-mosaic · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20))
    .configure(background="white")
    .configure_view(strokeWidth=0)
)

# Save outputs
mosaic.save("plot.png", scale_factor=3.0)
mosaic.save("plot.html")
