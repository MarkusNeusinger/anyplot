""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_hline,
    geom_step,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Simulated binary classification results
np.random.seed(42)
n_samples = 500

# Create realistic classification scenario (imbalanced - ~20% positive class)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])

# Generate scores: positive class gets higher scores on average
y_scores = np.where(
    y_true == 1,
    np.clip(np.random.beta(5, 2, size=n_samples), 0, 1),
    np.clip(np.random.beta(2, 5, size=n_samples), 0, 1),
)

# Calculate precision-recall curve
sorted_indices = np.argsort(y_scores)[::-1]
y_true_sorted = y_true[sorted_indices]
tp_cumsum = np.cumsum(y_true_sorted)
total_positives = y_true.sum()
n_predictions = np.arange(1, len(y_true_sorted) + 1)

precision = tp_cumsum / n_predictions
recall = tp_cumsum / total_positives

# Add start point (recall=0, precision=1)
precision = np.concatenate([[1], precision])
recall = np.concatenate([[0], recall])

# Calculate average precision (area under PR curve)
recall_diff = np.diff(recall)
ap_score = np.sum(recall_diff * precision[1:])

# Baseline (positive class ratio)
baseline = y_true.mean()

# Create DataFrame for plotting
df = pd.DataFrame({"Recall": recall, "Precision": precision})

# Plot
plot = (
    ggplot(df, aes(x="Recall", y="Precision"))
    + geom_step(color="#306998", size=2, direction="vh")
    + geom_hline(yintercept=baseline, linetype="dashed", color="#FFD43B", size=1.5)
    + annotate(
        "text",
        x=0.95,
        y=baseline + 0.05,
        label=f"Random Classifier (baseline = {baseline:.2f})",
        ha="right",
        size=14,
        color="#FFD43B",
    )
    + annotate("rect", xmin=0.55, xmax=0.95, ymin=0.75, ymax=0.95, fill="white", alpha=0.9)
    + annotate(
        "text",
        x=0.75,
        y=0.85,
        label=f"Average Precision (AP) = {ap_score:.3f}",
        size=16,
        color="#306998",
        fontweight="bold",
    )
    + labs(
        x="Recall (Sensitivity)",
        y="Precision (Positive Predictive Value)",
        title="precision-recall · plotnine · pyplots.ai",
    )
    + scale_x_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, ha="center"),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
