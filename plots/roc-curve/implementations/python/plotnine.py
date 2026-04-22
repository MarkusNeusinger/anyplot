""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_line,
    element_text,
    geom_abline,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Simulate ROC curve from a good classifier
np.random.seed(42)

# Generate realistic ROC curve data using beta distribution for smooth curve
n_points = 200
thresholds = np.linspace(0, 1, n_points)

# Model 1: Good classifier (AUC ~ 0.92)
fpr_1 = np.sort(np.concatenate([[0], np.power(thresholds[1:-1], 2.5), [1]]))
tpr_1 = np.sort(np.concatenate([[0], np.power(thresholds[1:-1], 0.4), [1]]))

# Model 2: Moderate classifier (AUC ~ 0.78)
fpr_2 = np.sort(np.concatenate([[0], np.power(thresholds[1:-1], 1.8), [1]]))
tpr_2 = np.sort(np.concatenate([[0], np.power(thresholds[1:-1], 0.7), [1]]))

# Calculate AUC using trapezoidal rule
auc_1 = np.trapezoid(tpr_1, fpr_1)
auc_2 = np.trapezoid(tpr_2, fpr_2)

# Create DataFrame for plotting
df = pd.DataFrame(
    {
        "fpr": np.concatenate([fpr_1, fpr_2]),
        "tpr": np.concatenate([tpr_1, tpr_2]),
        "Model": [f"Random Forest (AUC = {auc_1:.2f})"] * len(fpr_1)
        + [f"Logistic Regression (AUC = {auc_2:.2f})"] * len(fpr_2),
    }
)

# Create plot
plot = (
    ggplot(df, aes(x="fpr", y="tpr", color="Model"))
    + geom_abline(intercept=0, slope=1, linetype="dashed", color="#888888", size=1)
    + geom_line(size=2.5, alpha=0.9)
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + scale_x_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + coord_fixed(ratio=1)
    + labs(x="False Positive Rate", y="True Positive Rate", title="roc-curve · plotnine · pyplots.ai", color="Model")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        text=element_text(size=14),
        axis_title=element_text(size=22, face="bold"),
        axis_text=element_text(size=18),
        plot_title=element_text(size=26, face="bold"),
        legend_text=element_text(size=18),
        legend_title=element_text(size=20, face="bold"),
        legend_position=(0.65, 0.25),
        legend_background=element_line(color="#CCCCCC", size=0.5),
        panel_grid_major=element_line(color="#DDDDDD", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.3, alpha=0.2),
    )
    + annotate("text", x=0.6, y=0.1, label="Diagonal = Random Classifier", size=12, color="#888888", fontstyle="italic")
)

# Save plot
plot.save("plot.png", dpi=300, width=12, height=12)
