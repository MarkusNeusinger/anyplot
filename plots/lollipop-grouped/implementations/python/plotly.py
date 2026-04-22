""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - Quarterly revenue by product line across regions (in millions $)
np.random.seed(42)
categories = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
series_names = ["Electronics", "Apparel", "Home Goods"]
colors = ["#306998", "#FFD43B", "#8B4513"]  # Python Blue, Python Yellow, Brown

# Generate realistic revenue data
revenue_data = {
    "Electronics": [42.5, 38.2, 51.3, 18.7, 12.4],
    "Apparel": [28.3, 45.6, 32.1, 22.8, 8.9],
    "Home Goods": [35.1, 29.8, 25.4, 15.2, 10.6],
}

# Create figure
fig = go.Figure()

# Calculate positions for grouped lollipops
n_categories = len(categories)
n_series = len(series_names)
group_width = 0.7
bar_width = group_width / n_series
x_base = np.arange(n_categories)

# Add stems and markers for each series
for i, (series, color) in enumerate(zip(series_names, colors, strict=False)):
    # Calculate x positions with offset for grouping
    offset = (i - (n_series - 1) / 2) * bar_width
    x_positions = x_base + offset
    values = revenue_data[series]

    # Add stems (lines from 0 to value)
    for x_pos, val in zip(x_positions, values, strict=False):
        fig.add_trace(
            go.Scatter(
                x=[x_pos, x_pos],
                y=[0, val],
                mode="lines",
                line={"color": color, "width": 4},
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Add markers (dots at the top)
    fig.add_trace(
        go.Scatter(
            x=x_positions,
            y=values,
            mode="markers",
            marker={"size": 22, "color": color, "line": {"color": "white", "width": 2}},
            name=series,
            hovertemplate="%{text}<br>%{y:.1f}M $<extra></extra>",
            text=[f"{series} - {cat}" for cat in categories],
        )
    )

# Update layout
fig.update_layout(
    title={"text": "lollipop-grouped · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Region", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickvals": x_base,
        "ticktext": categories,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Quarterly Revenue (Million $)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "zerolinewidth": 2,
    },
    template="plotly_white",
    legend={"font": {"size": 18}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 80, "r": 40, "t": 120, "b": 80},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
