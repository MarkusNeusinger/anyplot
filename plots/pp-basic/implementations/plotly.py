"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data
np.random.seed(42)
observed = np.random.normal(loc=50, scale=10, size=200) + np.random.exponential(scale=2, size=200)

observed_sorted = np.sort(observed)
n = len(observed_sorted)

# Fit normal distribution to observed data
mu, sigma = stats.norm.fit(observed_sorted)

# Empirical CDF using plotting position formula i/(n+1)
empirical_cdf = np.arange(1, n + 1) / (n + 1)

# Theoretical CDF from fitted normal
theoretical_cdf = stats.norm.cdf(observed_sorted, loc=mu, scale=sigma)

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=theoretical_cdf,
        y=empirical_cdf,
        mode="markers",
        marker={"size": 8, "color": "#306998", "opacity": 0.7, "line": {"width": 0.5, "color": "white"}},
        name="Data points",
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        line={"color": "#AAAAAA", "width": 2, "dash": "dash"},
        name="Perfect fit",
        showlegend=False,
    )
)

# Style
fig.update_layout(
    title={"text": "pp-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Theoretical CDF (Normal)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 1],
        "showgrid": False,
        "showline": True,
        "linecolor": "#CCCCCC",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Empirical CDF", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 1],
        "showgrid": False,
        "showline": True,
        "linecolor": "#CCCCCC",
        "zeroline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    width=1200,
    height=1200,
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
