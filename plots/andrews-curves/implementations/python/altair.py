""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Set random seed for reproducibility
np.random.seed(42)

# Load and prepare data
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Normalize variables to similar scales
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Andrews curve transformation
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + x5*cos(2t) + ...
n_points = 100
t = np.linspace(-np.pi, np.pi, n_points)

# Compute Andrews curves for each observation
curves_data = []
for obs_idx in range(len(X_scaled)):
    x = X_scaled[obs_idx]
    curve = np.zeros(n_points)
    curve += x[0] / np.sqrt(2)

    for i in range(1, len(x)):
        freq = (i + 1) // 2
        if i % 2 == 1:
            curve += x[i] * np.sin(freq * t)
        else:
            curve += x[i] * np.cos(freq * t)

    for pt_idx in range(n_points):
        curves_data.append(
            {"t": t[pt_idx], "value": curve[pt_idx], "observation": obs_idx, "species": species_names[y[obs_idx]]}
        )

df = pd.DataFrame(curves_data)

# Define colors for species
species_colors = ["#306998", "#FFD43B", "#6B8E23"]

# Create chart
chart = (
    alt.Chart(df)
    .mark_line(opacity=0.4, strokeWidth=2)
    .encode(
        x=alt.X("t:Q", title="t (radians)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("value:Q", title="Andrews Curve Value", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "species:N",
            title="Species",
            scale=alt.Scale(domain=["Setosa", "Versicolor", "Virginica"], range=species_colors),
            legend=alt.Legend(titleFontSize=22, labelFontSize=20),
        ),
        detail="observation:N",
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Iris Classification · andrews-curves · altair · pyplots.ai",
            fontSize=28,
            subtitle="Fourier series transformation of multivariate data for visual pattern comparison",
            subtitleFontSize=18,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
    .configure_title(fontSize=28)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
