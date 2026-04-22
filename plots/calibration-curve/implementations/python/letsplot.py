""" pyplots.ai
calibration-curve: Calibration Curve
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Generate realistic binary classification predictions
np.random.seed(42)
n_samples = 1000

# Create true labels with imbalanced classes (60/40 split)
y_true = np.concatenate([np.zeros(600), np.ones(400)])

# Generate predicted probabilities with realistic calibration issues
# Model tends to be slightly overconfident (probabilities pushed toward extremes)
y_prob = np.zeros(n_samples)

# For true negatives: mostly low probabilities with some mid-range
y_prob[:600] = np.clip(np.random.beta(2, 5, 600) * 0.6 + np.random.normal(0, 0.05, 600), 0, 1)
# For true positives: mostly high probabilities but with spread
y_prob[600:] = np.clip(np.random.beta(5, 2, 400) * 0.6 + 0.35 + np.random.normal(0, 0.08, 400), 0, 1)

# Shuffle the data
shuffle_idx = np.random.permutation(n_samples)
y_true = y_true[shuffle_idx]
y_prob = y_prob[shuffle_idx]

# Calculate calibration curve with 10 bins
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

mean_predicted = []
fraction_positive = []
bin_counts = []

for i in range(n_bins):
    mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
    if i == n_bins - 1:  # Include right edge for last bin
        mask = (y_prob >= bin_edges[i]) & (y_prob <= bin_edges[i + 1])

    if mask.sum() > 0:
        mean_predicted.append(y_prob[mask].mean())
        fraction_positive.append(y_true[mask].mean())
        bin_counts.append(mask.sum())
    else:
        mean_predicted.append(bin_centers[i])
        fraction_positive.append(np.nan)
        bin_counts.append(0)

# Calculate Brier Score
brier_score = np.mean((y_prob - y_true) ** 2)

# Calculate Expected Calibration Error (ECE)
ece = 0
total_samples = sum(bin_counts)
for i in range(n_bins):
    if bin_counts[i] > 0:
        ece += (bin_counts[i] / total_samples) * abs(fraction_positive[i] - mean_predicted[i])

# Create dataframe for calibration curve
df_calibration = pd.DataFrame(
    {"mean_predicted": mean_predicted, "fraction_positive": fraction_positive, "bin_count": bin_counts}
)
df_calibration = df_calibration.dropna()

# Create dataframe for diagonal (perfect calibration)
df_diagonal = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Create dataframe for histogram of predictions
hist_bins = 20
hist_counts, hist_edges = np.histogram(y_prob, bins=hist_bins, range=(0, 1))
hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2
df_histogram = pd.DataFrame(
    {
        "prob_center": hist_centers,
        "count": hist_counts / hist_counts.max(),  # Normalize for subplot
    }
)

# Plot
plot = (
    ggplot()
    # Perfect calibration diagonal line
    + geom_line(aes(x="x", y="y"), data=df_diagonal, color="#888888", size=1.5, linetype="dashed")
    # Calibration curve
    + geom_line(aes(x="mean_predicted", y="fraction_positive"), data=df_calibration, color="#306998", size=2)
    + geom_point(
        aes(x="mean_predicted", y="fraction_positive"), data=df_calibration, color="#306998", size=5, alpha=0.9
    )
    # Histogram bars at bottom showing prediction distribution
    + geom_bar(
        aes(x="prob_center", y="count"), data=df_histogram, stat="identity", fill="#FFD43B", alpha=0.6, width=0.045
    )
    # Labels and styling
    + labs(
        x="Mean Predicted Probability",
        y="Fraction of Positives",
        title=f"calibration-curve · letsplot · pyplots.ai\nBrier Score: {brier_score:.4f} | ECE: {ece:.4f}",
    )
    + scale_x_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=22),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
