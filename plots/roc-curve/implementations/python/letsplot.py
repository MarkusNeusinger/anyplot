""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave

LetsPlot.setup_html()  # noqa: F405

# Data - Generate ROC curve data for multiple classifiers
np.random.seed(42)

# Generate synthetic classification scores
n_samples = 1000
y_true = np.concatenate([np.zeros(500), np.ones(500)])

# Model A - Good classifier (AUC ~0.92)
scores_a = np.concatenate(
    [
        np.random.beta(2, 5, 500),  # Negative class
        np.random.beta(5, 2, 500),  # Positive class
    ]
)

# Model B - Moderate classifier (AUC ~0.78)
scores_b = np.concatenate(
    [
        np.random.beta(2, 3, 500),  # Negative class
        np.random.beta(3, 2, 500),  # Positive class
    ]
)


# Calculate ROC curve points
def compute_roc(y_true, scores):
    thresholds = np.linspace(0, 1, 200)
    tpr_list = []
    fpr_list = []
    for thresh in thresholds:
        predictions = (scores >= thresh).astype(int)
        tp = np.sum((predictions == 1) & (y_true == 1))
        fn = np.sum((predictions == 0) & (y_true == 1))
        fp = np.sum((predictions == 1) & (y_true == 0))
        tn = np.sum((predictions == 0) & (y_true == 0))
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        tpr_list.append(tpr)
        fpr_list.append(fpr)
    return np.array(fpr_list), np.array(tpr_list)


# Compute ROC curves
fpr_a, tpr_a = compute_roc(y_true, scores_a)
fpr_b, tpr_b = compute_roc(y_true, scores_b)

# Calculate AUC using trapezoidal rule
auc_a = -np.trapezoid(tpr_a, fpr_a)
auc_b = -np.trapezoid(tpr_b, fpr_b)

# Create DataFrames for plotting
df_model_a = pd.DataFrame({"fpr": fpr_a, "tpr": tpr_a, "model": f"Model A (AUC = {auc_a:.2f})"})

df_model_b = pd.DataFrame({"fpr": fpr_b, "tpr": tpr_b, "model": f"Model B (AUC = {auc_b:.2f})"})

# Random classifier reference line
df_random = pd.DataFrame({"fpr": [0, 1], "tpr": [0, 1], "model": "Random (AUC = 0.50)"})

# Combine all data
df = pd.concat([df_model_a, df_model_b, df_random], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="fpr", y="tpr", color="model"))
    + geom_line(size=2)
    + scale_color_manual(values=["#306998", "#FFD43B", "#888888"])
    + scale_x_continuous(limits=[0, 1])
    + scale_y_continuous(limits=[0, 1])
    + coord_fixed(ratio=1)
    + labs(
        x="False Positive Rate", y="True Positive Rate", title="roc-curve · letsplot · pyplots.ai", color="Classifier"
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="bottom",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x = 4800 x 2700 px) and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
