""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_line, ggplot, labs, scale_color_manual, theme, theme_minimal
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Load iris dataset
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Normalize the data
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)

# Generate t values for the curve
t = np.linspace(-np.pi, np.pi, 100)

# Create data for plotting with inlined Andrews curve transformation
plot_data = []
for idx in range(len(X_normalized)):
    row = X_normalized[idx]
    n = len(row)
    # Andrews curve Fourier transformation: x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
    curve_values = row[0] / np.sqrt(2)
    for i in range(1, n):
        if i % 2 == 1:
            curve_values = curve_values + row[i] * np.sin((i // 2 + 1) * t)
        else:
            curve_values = curve_values + row[i] * np.cos((i // 2) * t)
    species = target_names[y[idx]]
    for t_val, curve_val in zip(t, curve_values, strict=True):
        plot_data.append({"t": t_val, "value": curve_val, "species": species, "observation": idx})

df = pd.DataFrame(plot_data)

# Distinct colors for the three species (blue, orange, green - colorblind-safe)
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

# Create plot
plot = (
    ggplot(df, aes(x="t", y="value", color="species", group="observation"))
    + geom_line(alpha=0.4, size=0.8)
    + labs(title="andrews-curves · plotnine · pyplots.ai", x="t (radians)", y="Andrews Curve Value", color="Species")
    + scale_color_manual(values=colors)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
)

# Save plot
plot.save("plot.png", dpi=300, verbose=False)
