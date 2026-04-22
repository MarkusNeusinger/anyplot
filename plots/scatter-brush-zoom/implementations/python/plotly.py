""" pyplots.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import numpy as np
import plotly.graph_objects as go


# Data - Multiple clusters for demonstrating brush selection
np.random.seed(42)
n_points = 300

# Create 4 distinct clusters
cluster_centers = [(20, 30), (50, 70), (80, 40), (60, 20)]
cluster_names = ["Cluster A", "Cluster B", "Cluster C", "Cluster D"]
colors = ["#306998", "#FFD43B", "#4CAF50", "#E91E63"]

x_data = []
y_data = []
labels = []
color_values = []

for i, (cx, cy) in enumerate(cluster_centers):
    n = n_points // 4
    x_cluster = np.random.normal(cx, 8, n)
    y_cluster = np.random.normal(cy, 8, n)
    x_data.extend(x_cluster)
    y_data.extend(y_cluster)
    labels.extend([cluster_names[i]] * n)
    color_values.extend([colors[i]] * n)

# Add some outliers
n_outliers = 25
x_data.extend(np.random.uniform(0, 100, n_outliers))
y_data.extend(np.random.uniform(0, 100, n_outliers))
labels.extend(["Outlier"] * n_outliers)
color_values.extend(["#9E9E9E"] * n_outliers)

x_data = np.array(x_data)
y_data = np.array(y_data)

# Create figure
fig = go.Figure()

# Add traces for each group (for proper legend)
unique_labels = ["Cluster A", "Cluster B", "Cluster C", "Cluster D", "Outlier"]
unique_colors = ["#306998", "#FFD43B", "#4CAF50", "#E91E63", "#9E9E9E"]

for label, color in zip(unique_labels, unique_colors, strict=False):
    mask = np.array(labels) == label
    fig.add_trace(
        go.Scatter(
            x=x_data[mask],
            y=y_data[mask],
            mode="markers",
            name=label,
            marker={"size": 14, "color": color, "opacity": 0.75, "line": {"width": 1, "color": "white"}},
            hovertemplate="<b>%{text}</b><br>X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>",
            text=[label] * mask.sum(),
        )
    )

# Update layout for interactivity and styling
fig.update_layout(
    title={
        "text": "scatter-brush-zoom · plotly · pyplots.ai", "font": {"size": 32, "color": "#333333"}, "x": 0.5, "xanchor": "center"
    },
    xaxis={
        "title": {"text": "X Value", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
        "range": [-10, 110],
    },
    yaxis={
        "title": {"text": "Y Value", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
        "range": [-10, 110],
    },
    template="plotly_white",
    # Enable box and lasso select modes
    dragmode="select",
    # Selection styling
    selectdirection="any",
    # Legend styling
    legend={
        "font": {"size": 18},
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(128, 128, 128, 0.3)",
        "borderwidth": 1,
        "x": 1.02,
        "y": 1,
        "xanchor": "left",
        "yanchor": "top",
    },
    # Margin for labels
    margin={"l": 80, "r": 150, "t": 100, "b": 80},
    # Annotations for instructions
    annotations=[
        {
            "text": "Drag to select • Scroll to zoom • Double-click to reset",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.12,
            "showarrow": False,
            "font": {"size": 16, "color": "#666666"},
            "xanchor": "center",
        }
    ],
    # Add modebar buttons for zoom and selection
    modebar={
        "bgcolor": "rgba(255, 255, 255, 0.9)", "color": "#306998", "activecolor": "#FFD43B", "add": ["select2d", "lasso2d"]
    },
)

# Configure selection appearance
fig.update_traces(selected={"marker": {"opacity": 1.0, "size": 18}}, unselected={"marker": {"opacity": 0.3}})

# Save as PNG (static output for quality review)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML (interactive version)
fig.write_html(
    "plot.html",
    include_plotlyjs=True,
    full_html=True,
    config={
        "displayModeBar": True,
        "modeBarButtonsToAdd": ["select2d", "lasso2d"],
        "scrollZoom": True,
        "displaylogo": False,
    },
)
