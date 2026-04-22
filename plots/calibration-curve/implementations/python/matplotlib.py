""" pyplots.ai
calibration-curve: Calibration Curve
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Simulate predictions from classifiers with different calibration properties
np.random.seed(42)
n_samples = 2000
n_bins = 10

# Generate ground truth - imbalanced to be realistic (35% positive rate)
y_true = np.random.binomial(1, 0.35, n_samples)

# Well-calibrated model: predictions closely match true probability
# Using logistic transformation with moderate noise
logits_calibrated = 1.2 * (y_true * 2 - 1) + np.random.normal(0, 1.0, n_samples)
y_prob_calibrated = 1 / (1 + np.exp(-logits_calibrated))

# Overconfident model: pushes predictions toward 0 and 1 (sigmoid with steeper slope)
logits_over = 2.0 * (y_true * 2 - 1) + np.random.normal(0, 0.5, n_samples)
y_prob_overconfident = 1 / (1 + np.exp(-logits_over))

# Underconfident model: predictions clustered toward 0.5 (flatter sigmoid)
logits_under = 0.5 * (y_true * 2 - 1) + np.random.normal(0, 0.8, n_samples)
y_prob_underconfident = 1 / (1 + np.exp(-logits_under))

# Calculate calibration curves for each model
bin_edges = np.linspace(0, 1, n_bins + 1)

# Well-calibrated model calibration curve
bin_idx_cal = np.digitize(y_prob_calibrated, bin_edges[1:-1])
prob_true_cal = [np.mean(y_true[bin_idx_cal == i]) for i in range(n_bins) if np.sum(bin_idx_cal == i) > 0]
prob_pred_cal = [np.mean(y_prob_calibrated[bin_idx_cal == i]) for i in range(n_bins) if np.sum(bin_idx_cal == i) > 0]

# Overconfident model calibration curve
bin_idx_over = np.digitize(y_prob_overconfident, bin_edges[1:-1])
prob_true_over = [np.mean(y_true[bin_idx_over == i]) for i in range(n_bins) if np.sum(bin_idx_over == i) > 0]
prob_pred_over = [
    np.mean(y_prob_overconfident[bin_idx_over == i]) for i in range(n_bins) if np.sum(bin_idx_over == i) > 0
]

# Underconfident model calibration curve
bin_idx_under = np.digitize(y_prob_underconfident, bin_edges[1:-1])
prob_true_under = [np.mean(y_true[bin_idx_under == i]) for i in range(n_bins) if np.sum(bin_idx_under == i) > 0]
prob_pred_under = [
    np.mean(y_prob_underconfident[bin_idx_under == i]) for i in range(n_bins) if np.sum(bin_idx_under == i) > 0
]

# Calculate Brier scores (mean squared error of probability predictions)
brier_cal = np.mean((y_prob_calibrated - y_true) ** 2)
brier_over = np.mean((y_prob_overconfident - y_true) ** 2)
brier_under = np.mean((y_prob_underconfident - y_true) ** 2)

# Create figure with two subplots: calibration curve and histogram
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), gridspec_kw={"height_ratios": [3, 1]})

# Primary colors from style guide
python_blue = "#306998"
python_yellow = "#FFD43B"
third_color = "#E377C2"  # Colorblind-safe pink/magenta

# Plot calibration curves
ax1.plot([0, 1], [0, 1], "k--", linewidth=2, label="Perfect Calibration", alpha=0.7)
ax1.plot(
    prob_pred_cal,
    prob_true_cal,
    "o-",
    color=python_blue,
    linewidth=3,
    markersize=12,
    label=f"Well-Calibrated (Brier: {brier_cal:.3f})",
)
ax1.plot(
    prob_pred_over,
    prob_true_over,
    "s-",
    color=python_yellow,
    linewidth=3,
    markersize=12,
    label=f"Overconfident (Brier: {brier_over:.3f})",
)
ax1.plot(
    prob_pred_under,
    prob_true_under,
    "^-",
    color=third_color,
    linewidth=3,
    markersize=12,
    label=f"Underconfident (Brier: {brier_under:.3f})",
)

# Style calibration plot
ax1.set_xlabel("Mean Predicted Probability", fontsize=20)
ax1.set_ylabel("Fraction of Positives", fontsize=20)
ax1.set_title("calibration-curve · matplotlib · pyplots.ai", fontsize=24)
ax1.tick_params(axis="both", labelsize=16)
ax1.legend(fontsize=16, loc="lower right")
ax1.grid(True, alpha=0.3, linestyle="--")
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)

# Histogram of predicted probabilities
ax2.hist(y_prob_calibrated, bins=20, alpha=0.6, color=python_blue, label="Well-Calibrated", edgecolor="white")
ax2.hist(y_prob_overconfident, bins=20, alpha=0.6, color=python_yellow, label="Overconfident", edgecolor="white")
ax2.hist(y_prob_underconfident, bins=20, alpha=0.6, color=third_color, label="Underconfident", edgecolor="white")
ax2.set_xlabel("Predicted Probability", fontsize=20)
ax2.set_ylabel("Count", fontsize=20)
ax2.tick_params(axis="both", labelsize=16)
ax2.legend(fontsize=14, loc="upper right")
ax2.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
