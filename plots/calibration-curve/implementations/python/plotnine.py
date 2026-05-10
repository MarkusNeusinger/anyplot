"""anyplot.ai
calibration-curve: Calibration Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_size_identity,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Simulate a classifier with realistic calibration characteristics
np.random.seed(42)
n_samples = 2000

# Generate predicted probabilities from a slightly overconfident model
y_prob = np.random.beta(2, 3, n_samples)

# Generate true labels - model is slightly overconfident
calibration_shift = 0.08
true_prob = np.clip(y_prob - calibration_shift + np.random.normal(0, 0.05, n_samples), 0, 1)
y_true = (np.random.random(n_samples) < true_prob).astype(int)

# Calculate calibration curve using 10 bins
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
bin_indices = np.digitize(y_prob, bin_edges) - 1
bin_indices = np.clip(bin_indices, 0, n_bins - 1)

# Calculate mean predicted probability and fraction of positives per bin
mean_predicted = []
fraction_positives = []
bin_counts = []

for i in range(n_bins):
    mask = bin_indices == i
    if mask.sum() > 0:
        mean_predicted.append(y_prob[mask].mean())
        fraction_positives.append(y_true[mask].mean())
        bin_counts.append(mask.sum())
    else:
        mean_predicted.append(np.nan)
        fraction_positives.append(np.nan)
        bin_counts.append(0)

# Calculate Expected Calibration Error (ECE)
ece = 0
for i in range(n_bins):
    if bin_counts[i] > 0:
        ece += bin_counts[i] * abs(fraction_positives[i] - mean_predicted[i])
ece /= n_samples

# Create DataFrame for calibration curve
df_calibration = pd.DataFrame(
    {"mean_predicted": mean_predicted, "fraction_positives": fraction_positives, "bin_counts": bin_counts}
).dropna()

# Add size column for point sizing based on bin counts
max_count = df_calibration["bin_counts"].max()
df_calibration["point_size"] = 3 + 5 * (df_calibration["bin_counts"] / max_count)

# Create calibration curve plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.8),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.8),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot(df_calibration, aes(x="mean_predicted", y="fraction_positives"))
    + geom_abline(intercept=0, slope=1, linetype="dashed", color=INK_SOFT, size=1.2)
    + geom_line(color=BRAND, size=2)
    + geom_point(aes(size="point_size"), color=BRAND, fill=BRAND, stroke=0, alpha=0.8)
    + scale_size_identity()
    + labs(
        x="Mean Predicted Probability",
        y="Fraction of Positives (Observed)",
        title=f"calibration-curve · plotnine · anyplot.ai (ECE = {ece:.3f})",
    )
    + coord_fixed(ratio=1, xlim=(0, 1), ylim=(0, 1))
    + theme_minimal()
    + anyplot_theme
    + theme(figure_size=(12, 12))
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
