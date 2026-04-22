""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Monthly streaming hours by music genre over 2 years
np.random.seed(42)
months = pd.date_range(start="2022-01-01", periods=24, freq="ME")
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

# Generate smooth, realistic streaming data
base_values = {"Pop": 45, "Rock": 35, "Hip-Hop": 40, "Electronic": 25, "Jazz": 15, "Classical": 12}
data = {}
for genre in genres:
    # Create smooth trends with seasonal variation
    trend = np.cumsum(np.random.randn(24) * 2)
    seasonal = 5 * np.sin(np.linspace(0, 4 * np.pi, 24))
    noise = np.random.randn(24) * 3
    values = base_values[genre] + trend + seasonal + noise
    values = np.maximum(values, 5)  # Ensure positive values
    data[genre] = values

df = pd.DataFrame(data, index=months)

# Calculate streamgraph layout (centered baseline)
values_array = df.values.T  # Shape: (n_genres, n_time_points)
n_genres, n_time = values_array.shape

# Calculate cumulative sums for stacking
cumsum = np.vstack([np.zeros(n_time), np.cumsum(values_array, axis=0)])

# Center the baseline symmetrically around the x-axis
total = cumsum[-1]
offset = total / 2

# Colors - Python Blue and Yellow first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#E24A33", "#8EBA42", "#988ED5", "#348ABD"]

# Create figure
fig = go.Figure()

# Add each genre as a filled area with smooth spline curves
for i, genre in enumerate(genres):
    y_lower = cumsum[i] - offset
    y_upper = cumsum[i + 1] - offset

    # Create coordinates for fill (forward then backward)
    x_fill = list(months) + list(months)[::-1]
    y_fill = list(y_upper) + list(y_lower)[::-1]

    fig.add_trace(
        go.Scatter(
            x=x_fill,
            y=y_fill,
            fill="toself",
            fillcolor=colors[i],
            line={"color": colors[i], "width": 0.5, "shape": "spline", "smoothing": 1.0},
            name=genre,
            mode="none",
            hoverinfo="name+x",
            hoveron="fills",
        )
    )

# Update layout for 4800x2700 px
fig.update_layout(
    title={"text": "streamgraph-basic · plotly · pyplots.ai", "font": {"size": 36}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Month", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "showgrid": True,
        "gridcolor": "rgba(128,128,128,0.2)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Streaming Hours (Millions)", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "showgrid": True,
        "gridcolor": "rgba(128,128,128,0.2)",
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": "rgba(128,128,128,0.3)",
        "zerolinewidth": 1,
    },
    legend={"font": {"size": 22}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    margin={"l": 100, "r": 50, "t": 120, "b": 80},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
