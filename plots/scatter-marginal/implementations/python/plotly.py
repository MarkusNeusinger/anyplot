""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.express as px


# Data - Bivariate normal with correlation
np.random.seed(42)
n = 200
x = np.random.randn(n) * 10 + 50
y = 0.7 * x + np.random.randn(n) * 8 + 15

# Create scatter plot with marginal histograms
fig = px.scatter(x=x, y=y, marginal_x="histogram", marginal_y="histogram")

# Style main scatter plot
fig.update_traces(
    marker={"size": 14, "color": "#306998", "opacity": 0.65, "line": {"width": 1, "color": "#1e4a6e"}},
    selector={"type": "scatter", "mode": "markers"},
)

# Style marginal histograms
fig.update_traces(
    marker={"color": "#306998", "opacity": 0.7, "line": {"width": 1, "color": "#1e4a6e"}},
    selector={"type": "histogram"},
)

# Layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "scatter-marginal \u00b7 plotly \u00b7 pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "X Value", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Y Value", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
    },
    xaxis2={"tickfont": {"size": 14}},
    yaxis2={"tickfont": {"size": 14}},
    xaxis3={"tickfont": {"size": 14}},
    yaxis3={"tickfont": {"size": 14}},
    template="plotly_white",
    font={"family": "Arial, sans-serif"},
    showlegend=False,
    margin={"l": 100, "r": 100, "t": 120, "b": 100},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
