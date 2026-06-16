""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    geom_segment,
    ggplot,
    labs,
    theme,
    theme_minimal,
)
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 for rug

# Data - Train a model and compute partial dependence
np.random.seed(42)

# Generate synthetic data for a regression problem
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
feature_names = ["Energy Consumption", "Room Size", "Occupancy Rate", "Ventilation", "Age"]

# Train a gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
model.fit(X, y)

# Compute partial dependence for Room Size (feature index 1)
feature_idx = 1

# Get partial dependence values
pd_results = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=80)
grid_actual = pd_results["grid_values"][0]

# Compute ICE curves for confidence interval estimation
pd_individual = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=80)
ice_values = pd_individual["individual"][0]

# Calculate confidence interval (mean ± 1.96 * std for 95% CI)
pd_mean = ice_values.mean(axis=0)
pd_std = ice_values.std(axis=0)
ci_lower = pd_mean - 1.96 * pd_std
ci_upper = pd_mean + 1.96 * pd_std

# Create DataFrame for plotting
df = pd.DataFrame(
    {"feature_value": grid_actual, "partial_dependence": pd_mean, "ci_lower": ci_lower, "ci_upper": ci_upper}
)

# Rug data - sample of training data positioned at the axis baseline
y_min = df["partial_dependence"].min()
y_max = df["partial_dependence"].max()
rug_height = (y_max - y_min) * 0.03
rug_sample = pd.DataFrame({"x": X[:100, feature_idx], "y": y_min - rug_height, "yend": y_min})

# Plot
plot = (
    ggplot(df, aes(x="feature_value", y="partial_dependence"))
    + geom_ribbon(aes(ymin="ci_lower", ymax="ci_upper"), alpha=0.15, fill=BRAND, color=BRAND, size=0.5)
    + geom_line(color=BRAND, size=2)
    + geom_segment(data=rug_sample, mapping=aes(x="x", xend="x", y="y", yend="yend"), color=ACCENT, alpha=0.6, size=0.8)
    + labs(
        title="pdp-basic · plotnine · anyplot.ai",
        x="Room Size (standardized)",
        y="Partial Dependence (avg. prediction)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
