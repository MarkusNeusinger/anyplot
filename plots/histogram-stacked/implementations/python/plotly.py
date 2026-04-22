""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Product weights from three production lines
np.random.seed(42)
n_per_group = 150

# Three production lines with different weight distributions
line_a = np.random.normal(loc=250, scale=30, size=n_per_group)  # Line A - centered at 250g
line_b = np.random.normal(loc=280, scale=25, size=n_per_group)  # Line B - centered at 280g
line_c = np.random.normal(loc=260, scale=35, size=n_per_group)  # Line C - centered at 260g

# Define consistent bin edges for all groups
all_values = np.concatenate([line_a, line_b, line_c])
bin_edges = np.histogram_bin_edges(all_values, bins=20)

# Calculate histograms with same bins for proper stacking
hist_a, _ = np.histogram(line_a, bins=bin_edges)
hist_b, _ = np.histogram(line_b, bins=bin_edges)
hist_c, _ = np.histogram(line_c, bins=bin_edges)

# Bin centers for x-axis
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Create figure with stacked bars
fig = go.Figure()

# Colors: Python Blue, Python Yellow, and a complementary teal
colors = ["#306998", "#FFD43B", "#4ECDC4"]

fig.add_trace(go.Bar(x=bin_centers, y=hist_a, name="Line A", marker_color=colors[0], width=bin_width * 0.9))

fig.add_trace(go.Bar(x=bin_centers, y=hist_b, name="Line B", marker_color=colors[1], width=bin_width * 0.9))

fig.add_trace(go.Bar(x=bin_centers, y=hist_c, name="Line C", marker_color=colors[2], width=bin_width * 0.9))

# Layout
fig.update_layout(
    title=dict(text="histogram-stacked · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Product Weight (g)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Frequency", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
    ),
    barmode="stack",
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
