# ruff: noqa: F405
"""pyplots.ai
residual-plot: Residual Plot
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data: Generate realistic regression scenario with deliberate pattern in residuals
np.random.seed(42)
n = 150

# Create feature with mild non-linearity to show residual patterns
X = np.linspace(10, 100, n)
noise = np.random.normal(0, 5, n)
# Add slight heteroscedasticity: variance increases with X
heteroscedastic_noise = noise * (0.5 + 0.01 * X)
y_true = 2.5 * X + 0.02 * X**2 + heteroscedastic_noise + 50

# Simple linear regression (manual implementation)
X_mean = np.mean(X)
y_mean = np.mean(y_true)
slope = np.sum((X - X_mean) * (y_true - y_mean)) / np.sum((X - X_mean) ** 2)
intercept = y_mean - slope * X_mean
y_pred = slope * X + intercept

# Calculate residuals
residuals = y_true - y_pred

# Calculate residual standard deviation for outlier bands
residual_std = np.std(residuals)

# Identify outliers (beyond ±2 standard deviations)
outlier_threshold = 2 * residual_std
is_outlier = np.abs(residuals) > outlier_threshold

# Create DataFrame for plotting
df = pd.DataFrame(
    {"Fitted Values": y_pred, "Residuals": residuals, "Outlier": np.where(is_outlier, "Outlier (>2σ)", "Normal")}
)

# Create residual plot
plot = (
    ggplot(df, aes(x="Fitted Values", y="Residuals"))
    # Reference line at y=0
    + geom_hline(yintercept=0, color="#306998", size=1.5, linetype="solid")
    # Outlier bands at ±2 standard deviations
    + geom_hline(yintercept=outlier_threshold, color="#DC2626", size=1, linetype="dashed", alpha=0.7)
    + geom_hline(yintercept=-outlier_threshold, color="#DC2626", size=1, linetype="dashed", alpha=0.7)
    # Points colored by outlier status
    + geom_point(aes(color="Outlier"), size=5, alpha=0.7)
    # LOWESS smoothing line to detect patterns
    + geom_smooth(method="loess", color="#FFD43B", size=2, se=False, span=0.6)
    # Color scale for outliers
    + scale_color_manual(values=["#306998", "#DC2626"], name="Point Type")
    # Labels
    + labs(title="residual-plot · letsplot · pyplots.ai", x="Fitted Values", y="Residuals (Observed - Predicted)")
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    # Size for export (1600 × 900 base, scaled 3x = 4800 × 2700)
    + ggsize(1600, 900)
)

# Save as PNG and HTML (path='.' ensures files are saved in current directory)
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
