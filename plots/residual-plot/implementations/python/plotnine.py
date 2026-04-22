""" pyplots.ai
residual-plot: Residual Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_hline,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Data - Generate synthetic regression data
np.random.seed(42)
n_points = 150

X = np.linspace(0, 10, n_points)
y_true = 2 * X + 3 + np.random.normal(0, 1.5, n_points)

# Add a few outliers
outlier_indices = [20, 75, 130]
y_true[outlier_indices] += np.array([6, -7, 5])

# Fit linear regression using ordinary least squares (manual calculation)
X_mean = np.mean(X)
y_mean = np.mean(y_true)
slope = np.sum((X - X_mean) * (y_true - y_mean)) / np.sum((X - X_mean) ** 2)
intercept = y_mean - slope * X_mean
y_pred = slope * X + intercept

# Calculate residuals
residuals = y_true - y_pred

# Identify outliers (beyond 2 standard deviations)
std_resid = np.std(residuals)
is_outlier = np.abs(residuals) > 2 * std_resid
point_type = np.where(is_outlier, "Outlier", "Normal")

# Create DataFrame
df = pd.DataFrame({"fitted": y_pred, "residuals": residuals, "point_type": point_type})

# Create residual plot
plot = (
    ggplot(df, aes(x="fitted", y="residuals", color="point_type"))
    + geom_hline(yintercept=0, color="#306998", size=1.2, linetype="solid", alpha=0.8)
    + geom_hline(yintercept=2 * std_resid, color="#999999", size=0.8, linetype="dashed", alpha=0.6)
    + geom_hline(yintercept=-2 * std_resid, color="#999999", size=0.8, linetype="dashed", alpha=0.6)
    + geom_point(size=4, alpha=0.7)
    + geom_smooth(aes(group=1), method="lowess", color="#FFD43B", size=1.5, se=False, span=0.5)
    + scale_color_manual(values={"Normal": "#306998", "Outlier": "#E74C3C"})
    + labs(x="Fitted Values", y="Residuals", title="residual-plot · plotnine · pyplots.ai", color="Point Type")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save
plot.save("plot.png", dpi=300)
