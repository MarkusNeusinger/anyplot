""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_iris


# Data - Load Iris dataset
iris = load_iris()
X = iris.data  # 150 samples, 4 features
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]
colors = ["#306998", "#FFD43B", "#E74C3C"]  # Python Blue, Python Yellow, Red

# Normalize data to prevent dominant variables
X_normalized = (X - X.mean(axis=0)) / X.std(axis=0)

# Andrews curve transformation
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + x5*cos(2t) + ...
t = np.linspace(-np.pi, np.pi, 200)


def andrews_curve(x, t_vals):
    """Transform a single observation to Andrews curve values."""
    n_features = len(x)
    curve = np.ones_like(t_vals) * x[0] / np.sqrt(2)
    for i in range(1, n_features):
        freq = (i + 1) // 2
        if i % 2 == 1:
            curve += x[i] * np.sin(freq * t_vals)
        else:
            curve += x[i] * np.cos(freq * t_vals)
    return curve


# Create figure
fig = go.Figure()

# Plot Andrews curves for each sample, colored by species
for species_idx in range(3):
    species_mask = y == species_idx
    X_species = X_normalized[species_mask]

    for i, x in enumerate(X_species):
        curve_y = andrews_curve(x, t)
        fig.add_trace(
            go.Scatter(
                x=t,
                y=curve_y,
                mode="lines",
                line=dict(color=colors[species_idx], width=2),
                opacity=0.4,
                name=species_names[species_idx],
                legendgroup=species_names[species_idx],
                showlegend=(i == 0),  # Only show legend for first curve of each species
                hovertemplate=f"{species_names[species_idx]}<br>t: %{{x:.2f}}<br>f(t): %{{y:.2f}}<extra></extra>",
            )
        )

# Update layout for 4800x2700 canvas
fig.update_layout(
    title=dict(text="Iris Dataset · andrews-curves · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Parameter t (radians)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(128, 128, 128, 0.5)",
        zerolinewidth=1,
        range=[-np.pi, np.pi],
        tickvals=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi],
        ticktext=["-π", "-π/2", "0", "π/2", "π"],
    ),
    yaxis=dict(
        title=dict(text="f(t) (normalized units)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(128, 128, 128, 0.3)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(128, 128, 128, 0.5)",
        zerolinewidth=1,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=20),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=100, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
