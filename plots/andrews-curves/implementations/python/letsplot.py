""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_line,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()

# Load and prepare data
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Normalize variables to similar scales
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Create DataFrame with normalized features and species
df_features = pd.DataFrame(X_scaled, columns=feature_names)
df_features["species"] = [target_names[i] for i in y]

# Andrews curves transformation
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + x5*cos(2t) + ...
t_values = np.linspace(-np.pi, np.pi, 200)

curves_data = []
for idx, row in df_features.iterrows():
    values = row[feature_names].values
    species = row["species"]

    for t in t_values:
        # Fourier expansion
        y_val = values[0] / np.sqrt(2)
        for i in range(1, len(values)):
            if i % 2 == 1:
                y_val += values[i] * np.sin((i // 2 + 1) * t)
            else:
                y_val += values[i] * np.cos((i // 2) * t)

        curves_data.append({"t": t, "y": y_val, "observation": idx, "species": species})

df_curves = pd.DataFrame(curves_data)

# Define colors for species - Python blue, yellow, and a third color
species_colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#DC2626"}

# Create plot
plot = (
    ggplot(df_curves, aes(x="t", y="y", group="observation", color="species"))
    + geom_line(alpha=0.4, size=0.8)
    + scale_color_manual(values=list(species_colors.values()))
    + scale_x_continuous(breaks=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], labels=["-π", "-π/2", "0", "π/2", "π"])
    + labs(
        x="Parameter t (radians)",
        y="Fourier Function Value",
        title="andrews-curves · letsplot · pyplots.ai",
        color="Species",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
