""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data: Simulated test scores with realistic distribution
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(65, 10, 300),  # Average performers
        np.random.normal(85, 5, 150),  # High performers
        np.random.normal(45, 8, 50),  # Low performers
    ]
)
scores = np.clip(scores, 0, 100)  # Keep scores in valid range

# Calculate cumulative histogram
bin_count = 25
counts, bin_edges = np.histogram(scores, bins=bin_count)
cumulative_counts = np.cumsum(counts)
cumulative_proportion = cumulative_counts / len(scores)

# Use bin centers for x-axis
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Create figure
fig = go.Figure()

# Add cumulative histogram as step line
fig.add_trace(
    go.Scatter(
        x=bin_edges[1:],  # Right edge of each bin
        y=cumulative_proportion,
        mode="lines",
        line=dict(
            color="#306998",  # Python Blue
            width=4,
            shape="hv",  # Step function (horizontal then vertical)
        ),
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.3)",
        name="Cumulative Distribution",
        hovertemplate="Score ≤ %{x:.1f}<br>Proportion: %{y:.2%}<extra></extra>",
    )
)

# Add reference lines for key percentiles
percentiles = [0.25, 0.50, 0.75]
percentile_labels = ["25th", "50th (Median)", "75th"]
for p, label in zip(percentiles, percentile_labels):
    x_val = np.percentile(scores, p * 100)
    fig.add_trace(
        go.Scatter(
            x=[x_val, x_val],
            y=[0, p],
            mode="lines",
            line=dict(color="#FFD43B", width=2, dash="dash"),  # Python Yellow
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, x_val],
            y=[p, p],
            mode="lines",
            line=dict(color="#FFD43B", width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add percentile annotations
fig.add_trace(
    go.Scatter(
        x=[np.percentile(scores, 25), np.percentile(scores, 50), np.percentile(scores, 75)],
        y=[0.25, 0.50, 0.75],
        mode="markers+text",
        marker=dict(color="#FFD43B", size=14, line=dict(color="#306998", width=2)),
        text=["25%", "50%", "75%"],
        textposition="top right",
        textfont=dict(size=16, color="#306998"),
        showlegend=False,
        hovertemplate="%{text} of scores ≤ %{x:.1f}<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="histogram-cumulative · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Test Score (points)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 105],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Cumulative Proportion", font=dict(size=22)),
        tickfont=dict(size=18),
        tickformat=".0%",
        range=[0, 1.05],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    showlegend=True,
    legend=dict(x=0.02, y=0.98, font=dict(size=16), bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
