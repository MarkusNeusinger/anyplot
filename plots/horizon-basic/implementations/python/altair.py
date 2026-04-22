""" pyplots.ai
horizon-basic: Horizon Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Generate server metrics over 24 hours for multiple servers
np.random.seed(42)

n_points = 96  # 15-minute intervals over 24 hours
hours = pd.date_range("2024-01-15 00:00", periods=n_points, freq="15min")

# Generate realistic CPU usage patterns with different behaviors
data_list = []
servers = ["Web Server 1", "Web Server 2", "Database", "Cache", "API Gateway", "Worker"]

for server in servers:
    # Base pattern with daily cycle
    t = np.linspace(0, 2 * np.pi, n_points)
    if server == "Database":
        # Database: high during business hours
        base = 40 + 30 * np.sin(t - np.pi / 2) + np.random.randn(n_points) * 8
    elif server == "Cache":
        # Cache: relatively stable with occasional spikes
        base = 25 + np.random.randn(n_points) * 5
        base[40:45] += 40  # Spike
    elif server == "Worker":
        # Worker: periodic batch processing
        base = 20 + 50 * (np.sin(t * 3) > 0.7) + np.random.randn(n_points) * 6
    else:
        # Web servers: follow traffic patterns
        base = 30 + 25 * np.sin(t - np.pi / 3) + np.random.randn(n_points) * 10

    # Normalize to deviation from mean (centered at 0)
    values = base - base.mean()

    for hour, val in zip(hours, values, strict=True):
        data_list.append({"date": hour, "value": val, "series": server})

df = pd.DataFrame(data_list)

# Horizon chart parameters
n_bands = 3
band_height = df["value"].abs().max() / n_bands

# Create band data
band_data = []
for _, row in df.iterrows():
    val = row["value"]
    for band in range(n_bands):
        band_min = band * band_height
        if val >= 0:
            # Positive values
            band_val = max(0, min(val - band_min, band_height))
            band_data.append(
                {"date": row["date"], "series": row["series"], "band": band, "value": band_val, "direction": "positive"}
            )
        else:
            # Negative values (use absolute value)
            abs_val = abs(val)
            band_val = max(0, min(abs_val - band_min, band_height))
            band_data.append(
                {"date": row["date"], "series": row["series"], "band": band, "value": band_val, "direction": "negative"}
            )

band_df = pd.DataFrame(band_data)

# Color scales for bands - blue for positive, red for negative
# Intensity increases with band number
positive_colors = ["#a6c8e0", "#306998", "#1a3d5c"]  # Light to dark blue
negative_colors = ["#f5b7b1", "#e74c3c", "#922b21"]  # Light to dark red

# Combine direction and band for color mapping
band_df["color_key"] = band_df["direction"] + "_" + band_df["band"].astype(str)

color_scale = alt.Scale(
    domain=["positive_0", "positive_1", "positive_2", "negative_0", "negative_1", "negative_2"],
    range=positive_colors + negative_colors,
)

# Create the horizon chart
chart = (
    alt.Chart(band_df)
    .mark_area()
    .encode(
        x=alt.X("date:T", title="Time", axis=alt.Axis(format="%H:%M", labelFontSize=14, titleFontSize=18)),
        y=alt.Y("value:Q", title=None, axis=None, scale=alt.Scale(domain=[0, band_height])),
        color=alt.Color(
            "color_key:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Band Intensity", orient="right", titleFontSize=16, labelFontSize=14, symbolSize=200
            ),
        ),
        order=alt.Order("band:O"),
    )
    .properties(width=1400, height=80)
    .facet(
        row=alt.Row(
            "series:N",
            title=None,
            header=alt.Header(labelFontSize=16, labelAngle=0, labelAlign="left", labelPadding=10),
        )
    )
    .properties(
        title=alt.Title(
            "Server CPU Metrics (24h) · horizon-basic · altair · pyplots.ai", fontSize=28, anchor="start", offset=20
        )
    )
    .configure_facet(spacing=5)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
