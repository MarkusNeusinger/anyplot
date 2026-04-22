""" pyplots.ai
strip-basic: Basic Strip Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Survey response scores grouped by demographic category
np.random.seed(42)

categories = ["Group A", "Group B", "Group C", "Group D"]
n_per_group = [45, 60, 50, 55]

# Generate data with different distributions to show variety
data = {
    "Group A": np.random.normal(65, 12, n_per_group[0]),  # Medium, moderate spread
    "Group B": np.random.normal(78, 8, n_per_group[1]),  # Higher, tighter
    "Group C": np.random.normal(55, 15, n_per_group[2]),  # Lower, wider spread
    "Group D": np.random.normal(70, 10, n_per_group[3]),  # Medium-high, moderate
}

# Python colors
colors = ["#306998", "#FFD43B", "#306998", "#FFD43B"]

# Create figure
fig = go.Figure()

# Add strip plot traces for each category with jitter
for i, (cat, values) in enumerate(data.items()):
    # Apply jitter to x positions (0.2 jitter width)
    jitter = np.random.uniform(-0.2, 0.2, len(values))
    x_positions = np.full(len(values), i) + jitter

    fig.add_trace(
        go.Scatter(
            x=x_positions,
            y=values,
            mode="markers",
            name=cat,
            marker={"size": 14, "opacity": 0.6, "color": colors[i]},
            hovertemplate=f"{cat}<br>Value: %{{y:.1f}}<extra></extra>",
        )
    )

# Add mean lines for reference
for i, (_cat, values) in enumerate(data.items()):
    mean_val = np.mean(values)
    fig.add_shape(
        type="line",
        x0=i - 0.3,
        x1=i + 0.3,
        y0=mean_val,
        y1=mean_val,
        line={"color": "#333333", "width": 3, "dash": "solid"},
    )

# Layout
fig.update_layout(
    title={"text": "strip-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Category", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "tickmode": "array",
        "tickvals": list(range(len(categories))),
        "ticktext": categories,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Response Score", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 1.02, "y": 0.5, "xanchor": "left", "yanchor": "middle"},
    margin={"l": 80, "r": 150, "t": 100, "b": 80},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
