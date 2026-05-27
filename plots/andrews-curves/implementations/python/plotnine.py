""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
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

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
)

# Plot
plot = (
    ggplot(df, aes(x="t", y="value", color="species", group="observation"))
    + geom_line(alpha=0.4, size=0.8)
    + labs(title="andrews-curves · plotnine · anyplot.ai", x="t (radians)", y="Andrews Curve Value", color="Species")
    + scale_color_manual(values=IMPRINT)
    + theme_minimal()
    + anyplot_theme
    + theme(figure_size=(16, 9))
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
