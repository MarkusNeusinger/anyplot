""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
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


# Data - Train a model and compute partial dependence
np.random.seed(42)

# Generate synthetic data for a regression problem
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
feature_names = ["Temperature", "Humidity", "Pressure", "WindSpeed", "Elevation"]

# Train a gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
model.fit(X, y)

# Compute partial dependence for the first feature (Temperature)
feature_idx = 0

# Get partial dependence values
pd_results = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=80)
pd_values = pd_results["average"][0]
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

# Rug data - sample of training data for feature distribution at bottom of plot
y_min = ci_lower.min()
rug_height = (ci_upper.max() - ci_lower.min()) * 0.02
rug_sample = pd.DataFrame({"x": X[:80, feature_idx], "yend": y_min, "y": y_min - rug_height})

# Plot
plot = (
    ggplot(df, aes(x="feature_value", y="partial_dependence"))
    + geom_ribbon(aes(ymin="ci_lower", ymax="ci_upper"), fill="#306998", alpha=0.25)
    + geom_line(color="#306998", size=2)
    + geom_segment(
        data=rug_sample, mapping=aes(x="x", xend="x", y="y", yend="yend"), color="#FFD43B", alpha=0.7, size=0.8
    )
    + labs(
        title="pdp-basic · plotnine · pyplots.ai",
        x="Temperature (standardized)",
        y="Partial Dependence (avg. prediction)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", ha="left"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
