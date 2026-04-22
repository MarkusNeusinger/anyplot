""" pyplots.ai
calibration-curve: Calibration Curve
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_line,
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


# Data - Simulate a classifier with realistic calibration characteristics
np.random.seed(42)
n_samples = 2000

# Generate predicted probabilities from a slightly overconfident model
y_prob = np.random.beta(2, 3, n_samples)  # Skewed toward lower probabilities

# Generate true labels - model is slightly overconfident (predicts higher than actual)
# Add noise to simulate real-world calibration issues
calibration_shift = 0.08  # Model predicts ~8% too high on average
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

# Create DataFrame for plotting
df_calibration = pd.DataFrame(
    {"mean_predicted": mean_predicted, "fraction_positives": fraction_positives, "bin_counts": bin_counts}
).dropna()

# Add size column for point sizing based on bin counts (normalized)
max_count = df_calibration["bin_counts"].max()
df_calibration["point_size"] = 3 + 5 * (df_calibration["bin_counts"] / max_count)

# Create plot
plot = (
    ggplot(df_calibration, aes(x="mean_predicted", y="fraction_positives"))
    + geom_abline(intercept=0, slope=1, linetype="dashed", color="#888888", size=1.2)  # Perfect calibration line
    + geom_line(color="#306998", size=2)  # Calibration curve line
    + geom_point(
        aes(size="point_size"), color="#306998", fill="#FFD43B", stroke=1.5, shape="o"
    )  # Points sized by bin count
    + scale_size_identity()
    + labs(
        x="Mean Predicted Probability",
        y="Fraction of Positives",
        title=f"calibration-curve · plotnine · pyplots.ai (ECE = {ece:.3f})",
    )
    + coord_fixed(ratio=1, xlim=(0, 1), ylim=(0, 1))
    + theme_minimal()
    + theme(
        figure_size=(12, 12),  # Square format for calibration curve (3600x3600 at 300dpi)
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=22),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
