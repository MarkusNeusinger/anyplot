# ruff: noqa: F405
"""pyplots.ai
residual-plot: Residual Plot
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens (read from environment)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1: bluish green (normal points)
OUTLIER_COLOR = "#AE3030"  # imprint red — outliers (>2σ)

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
    + geom_hline(yintercept=0, color=INK_SOFT, size=1.5, linetype="solid")
    # Outlier bands at ±2 standard deviations
    + geom_hline(yintercept=outlier_threshold, color=INK_MUTED, size=1, linetype="dashed", alpha=0.6)
    + geom_hline(yintercept=-outlier_threshold, color=INK_MUTED, size=1, linetype="dashed", alpha=0.6)
    # Points colored by outlier status
    + geom_point(aes(color="Outlier"), size=5, alpha=0.75)
    # LOWESS smoothing line to detect patterns
    + geom_smooth(method="loess", color=INK, size=2, se=False, span=0.6)
    # Color scale for outliers (Normal: brand green, Outlier: vermillion)
    + scale_color_manual(values=[BRAND, OUTLIER_COLOR], name="Point Type")
    # Labels
    + labs(title="residual-plot · letsplot · pyplots.ai", x="Fitted Values", y="Residuals (Observed - Predicted)")
    # Theme
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.4),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
    # Size for export (1600 × 900 base, scaled 3x = 4800 × 2700)
    + ggsize(1600, 900)
)

# Save as PNG and HTML with theme-suffixed filenames
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
