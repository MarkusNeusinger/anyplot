""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - Reaction times (ms) for three experimental conditions
np.random.seed(42)

# Control group - normal distribution centered around 350ms
control = np.random.normal(loc=350, scale=60, size=200)

# Caffeine group - faster reactions, centered around 280ms
caffeine = np.random.normal(loc=280, scale=50, size=200)

# Sleep deprived group - slower and more variable reactions
sleep_deprived = np.random.normal(loc=450, scale=90, size=200)

# Define consistent bins for all groups
bin_edges = np.linspace(100, 700, 31)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Calculate frequency for each group
control_freq, _ = np.histogram(control, bins=bin_edges)
caffeine_freq, _ = np.histogram(caffeine, bins=bin_edges)
sleep_deprived_freq, _ = np.histogram(sleep_deprived, bins=bin_edges)

# Extend to zero at both ends to close polygon
extended_centers = np.concatenate([[bin_edges[0]], bin_centers, [bin_edges[-1]]])
control_extended = np.concatenate([[0], control_freq, [0]])
caffeine_extended = np.concatenate([[0], caffeine_freq, [0]])
sleep_deprived_extended = np.concatenate([[0], sleep_deprived_freq, [0]])

# Create figure
fig = go.Figure()

# Add frequency polygons with semi-transparent fill
fig.add_trace(
    go.Scatter(
        x=extended_centers,
        y=control_extended,
        mode="lines+markers",
        name="Control",
        line={"color": "#306998", "width": 4},
        marker={"size": 10, "color": "#306998"},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.2)",
    )
)

fig.add_trace(
    go.Scatter(
        x=extended_centers,
        y=caffeine_extended,
        mode="lines+markers",
        name="Caffeine",
        line={"color": "#FFD43B", "width": 4},
        marker={"size": 10, "color": "#FFD43B"},
        fill="tozeroy",
        fillcolor="rgba(255, 212, 59, 0.2)",
    )
)

fig.add_trace(
    go.Scatter(
        x=extended_centers,
        y=sleep_deprived_extended,
        mode="lines+markers",
        name="Sleep Deprived",
        line={"color": "#E55934", "width": 4, "dash": "dash"},
        marker={"size": 10, "color": "#E55934"},
        fill="tozeroy",
        fillcolor="rgba(229, 89, 52, 0.2)",
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "frequency-polygon-basic · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Reaction Time (ms)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
        "range": [80, 720],
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
    },
    legend={
        "font": {"size": 20},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "bordercolor": "rgba(0, 0, 0, 0.2)",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
