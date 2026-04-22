""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-19
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - KPI metrics with sparkline history
np.random.seed(42)

metrics = [
    {"name": "CPU Usage", "value": 45, "unit": "%", "change": -5.2},
    {"name": "Memory", "value": 72, "unit": "%", "change": 8.1},
    {"name": "Response Time", "value": 120, "unit": "ms", "change": -15.3},
    {"name": "Requests/sec", "value": 2847, "unit": "", "change": 12.4},
    {"name": "Error Rate", "value": 0.8, "unit": "%", "change": 0.3},
    {"name": "Disk I/O", "value": 156, "unit": "MB/s", "change": -2.1},
]


def create_tile(m, idx):
    """Create a complete metric tile."""
    # Generate sparkline data
    np.random.seed(100 + idx * 17)
    history_points = 20
    noise = np.cumsum(np.random.randn(history_points) * 5)
    trend_dir = -1 if m["change"] < 0 else 1
    trend = np.linspace(trend_dir * 15, 0, history_points)
    values = 50 + noise + trend
    v_min, v_max = values.min(), values.max()
    values = 20 + 60 * (values - v_min) / (v_max - v_min + 0.001)

    spark_df = pd.DataFrame({"time": range(history_points), "value": values})

    # Format value display
    if m["value"] >= 1000:
        val_str = f"{m['value']:,.0f}"
    elif m["value"] < 1:
        val_str = f"{m['value']:.1f}"
    else:
        val_str = f"{m['value']:.0f}"
    display_val = f"{val_str}{m['unit']}"

    # Change indicator
    arrow = "▲" if m["change"] > 0 else "▼"
    change_text = f"{arrow} {abs(m['change']):.1f}%"
    is_favorable = m["change"] < 0
    if m["name"] in ["Requests/sec"]:
        is_favorable = m["change"] > 0
    change_color = "#4CAF50" if is_favorable else "#f44336"

    # Sparkline area
    sparkline = (
        alt.Chart(spark_df)
        .mark_area(
            line={"color": "#306998", "strokeWidth": 3},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(48, 105, 152, 0.4)", offset=0),
                    alt.GradientStop(color="rgba(48, 105, 152, 0.05)", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
        )
        .encode(x=alt.X("time:Q", axis=None), y=alt.Y("value:Q", axis=None, scale=alt.Scale(domain=[0, 100])))
        .properties(width=380, height=100)
    )

    # Change text row
    change_df = pd.DataFrame([{"x": 0.5, "text": change_text}])
    change_row = (
        alt.Chart(change_df)
        .mark_text(fontSize=22, fontWeight="bold", color=change_color)
        .encode(x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 1])), text="text:N")
        .properties(width=380, height=35)
    )

    # Combine sparkline and change text vertically
    tile = alt.vconcat(sparkline, change_row, spacing=5).properties(
        title=alt.Title(
            text=[display_val, m["name"]],
            fontSize=48,
            subtitleFontSize=22,
            subtitleColor="#757575",
            color="#212121",
            anchor="middle",
            offset=10,
        )
    )
    return tile


# Create 6 tiles
tiles = [create_tile(m, idx) for idx, m in enumerate(metrics)]

# Arrange in 3x2 grid
row1 = alt.hconcat(tiles[0], tiles[1], tiles[2], spacing=25)
row2 = alt.hconcat(tiles[3], tiles[4], tiles[5], spacing=25)

chart = (
    alt.vconcat(row1, row2, spacing=25)
    .properties(
        title=alt.Title(
            text="dashboard-metrics-tiles · altair · pyplots.ai",
            fontSize=32,
            color="#306998",
            anchor="middle",
            offset=20,
        )
    )
    .configure_view(stroke="#e0e0e0", strokeWidth=2, cornerRadius=12)
    .configure_concat(spacing=25)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
