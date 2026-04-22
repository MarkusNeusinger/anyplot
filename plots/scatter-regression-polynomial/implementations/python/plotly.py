""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulating diminishing returns in ad spend vs revenue
np.random.seed(42)
x = np.linspace(0, 50, 80)
# Quadratic relationship with noise: revenue increases but with diminishing returns
y = -0.08 * x**2 + 5 * x + 10 + np.random.normal(0, 8, len(x))

# Polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
x_fit = np.linspace(x.min(), x.max(), 200)
y_fit = poly(x_fit)

# Calculate R²
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.3f}x² + {b:.2f}x + {c:.1f}"

# Create figure
fig = go.Figure()

# Scatter points
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        name="Data Points",
        marker={"size": 14, "color": "#306998", "opacity": 0.65, "line": {"width": 1, "color": "#1e4263"}},
    )
)

# Polynomial regression curve
fig.add_trace(
    go.Scatter(x=x_fit, y=y_fit, mode="lines", name="Polynomial Fit (degree 2)", line={"color": "#FFD43B", "width": 4})
)

# Layout
fig.update_layout(
    title={
        "text": "Ad Spend vs Revenue · scatter-regression-polynomial · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Ad Spend ($K)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.3)",
    },
    yaxis={
        "title": {"text": "Revenue ($K)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.3)",
    },
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "bordercolor": "rgba(0, 0, 0, 0.3)",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
    # Add annotation for R² and equation
    annotations=[
        {
            "x": 0.98,
            "y": 0.05,
            "xref": "paper",
            "yref": "paper",
            "text": f"R² = {r_squared:.4f}<br>{equation}",
            "showarrow": False,
            "font": {"size": 18, "color": "#333333"},
            "bgcolor": "rgba(255, 255, 255, 0.8)",
            "bordercolor": "rgba(0, 0, 0, 0.3)",
            "borderwidth": 1,
            "borderpad": 8,
            "xanchor": "right",
            "yanchor": "bottom",
        }
    ],
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
