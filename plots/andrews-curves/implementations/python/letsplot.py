""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Set seed for reproducibility
np.random.seed(42)

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

# Map species to Okabe-Ito colors
species_colors = {
    target_names[0]: IMPRINT[0],  # setosa: #009E73 (brand green)
    target_names[1]: IMPRINT[1],  # versicolor: #C475FD (vermillion)
    target_names[2]: IMPRINT[2],  # virginica: #4467A3 (blue)
}

# Create plot
plot = (
    ggplot(df_curves, aes(x="t", y="y", group="observation", color="species"))
    + geom_line(alpha=0.4, size=0.8)
    + scale_color_manual(values=list(species_colors.values()))
    + scale_x_continuous(breaks=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], labels=["-π", "-π/2", "0", "π/2", "π"])
    + labs(
        x="Parameter t (radians)",
        y="Fourier Function Value",
        title="andrews-curves · letsplot · anyplot.ai",
        color="Species",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
