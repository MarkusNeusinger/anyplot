""" pyplots.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Test scores across different teaching methods
np.random.seed(42)

# Generate realistic test score distributions for 4 teaching methods
groups = ["Traditional", "Interactive", "Online", "Hybrid"]
data = {
    "Traditional": np.random.normal(70, 12, 80),  # Centered around 70
    "Interactive": np.random.normal(78, 10, 85),  # Higher scores, tighter
    "Online": np.concatenate(
        [  # Bimodal distribution
            np.random.normal(55, 8, 40),
            np.random.normal(80, 7, 45),
        ]
    ),
    "Hybrid": np.random.normal(75, 15, 90),  # More spread
}

# Clip to realistic test score range (0-100)
for group in groups:
    data[group] = np.clip(data[group], 0, 100)

# Colors - Python palette + accessible colors
colors = ["#306998", "#FFD43B", "#4B8BBE", "#E377C2"]

# Create figure
fig = go.Figure()

# Add violin with embedded box plot for each group
for i, group in enumerate(groups):
    fig.add_trace(
        go.Violin(
            y=data[group],
            name=group,
            box_visible=True,  # Show box plot inside
            meanline_visible=True,  # Show mean line
            fillcolor=colors[i],
            opacity=0.7,
            line={"color": "black", "width": 1.5},
            points="outliers",  # Show outliers
            pointpos=0,
            marker={"size": 8, "color": "black", "opacity": 0.7},
            box={"fillcolor": "white", "line": {"color": "black", "width": 2}, "width": 0.15},
            meanline={"color": "darkred", "width": 2},
        )
    )

# Layout for 4800x2700 px output
fig.update_layout(
    title={
        "text": "violin-box · plotly · pyplots.ai",
        "font": {"size": 32, "color": "black"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"title": {"text": "Teaching Method", "font": {"size": 24}}, "tickfont": {"size": 20}, "showgrid": False},
    yaxis={
        "title": {"text": "Test Score (points)", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "range": [0, 105],
    },
    template="plotly_white",
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 100, "r": 50, "t": 100, "b": 100},
    violingap=0.3,
    violinmode="group",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
