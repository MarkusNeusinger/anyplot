""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Product performance across regions
np.random.seed(42)
n_per_group = 40

# Generate distinct clusters for each region
regions = ["North", "South", "West", "East"]
colors = ["#306998", "#FFD43B", "#8B5CF6", "#10B981"]

data = {
    "North": {"x": np.random.normal(35, 8, n_per_group), "y": np.random.normal(75, 10, n_per_group)},
    "South": {"x": np.random.normal(55, 10, n_per_group), "y": np.random.normal(60, 12, n_per_group)},
    "West": {"x": np.random.normal(70, 7, n_per_group), "y": np.random.normal(85, 8, n_per_group)},
    "East": {"x": np.random.normal(45, 9, n_per_group), "y": np.random.normal(45, 10, n_per_group)},
}

# Plot
fig = go.Figure()

for region, color in zip(regions, colors):
    fig.add_trace(
        go.Scatter(
            x=data[region]["x"],
            y=data[region]["y"],
            mode="markers",
            name=region,
            marker=dict(size=14, color=color, opacity=0.7, line=dict(width=1, color="white")),
            hovertemplate=f"{region}<br>Marketing: %{{x:.1f}}%<br>Sales: %{{y:.1f}}%<extra></extra>",
        )
    )

# Layout
fig.update_layout(
    title=dict(text="scatter-categorical · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Marketing Investment (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Sales Growth (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        showgrid=True,
    ),
    legend=dict(
        title=dict(text="Region", font=dict(size=20)),
        font=dict(size=18),
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
        x=1.02,
        y=0.5,
        yanchor="middle",
    ),
    template="plotly_white",
    margin=dict(l=80, r=150, t=80, b=80),
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
