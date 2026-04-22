""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Simulate learning curve for a model showing slight overfitting pattern
np.random.seed(42)

# Training set sizes (10 different sizes)
train_sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600])

# Simulate 5 cross-validation folds
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: Start high, stay high (model fits training data well)
train_scores_mean = 0.99 - 0.15 * np.exp(-train_sizes / 200)
train_scores = np.zeros((n_folds, n_sizes))
for i in range(n_folds):
    noise = np.random.randn(n_sizes) * 0.01
    train_scores[i] = train_scores_mean + noise

# Validation scores: Start lower, improve with more data (learning effect)
# Show a gap with training that narrows as data increases
validation_scores_mean = 0.65 + 0.20 * (1 - np.exp(-train_sizes / 500))
validation_scores = np.zeros((n_folds, n_sizes))
for i in range(n_folds):
    noise = np.random.randn(n_sizes) * 0.02
    validation_scores[i] = validation_scores_mean + noise

# Calculate means and standard deviations
train_mean = np.mean(train_scores, axis=0)
train_std = np.std(train_scores, axis=0)
val_mean = np.mean(validation_scores, axis=0)
val_std = np.std(validation_scores, axis=0)

# Create DataFrames for plotting
df_train = pd.DataFrame(
    {
        "Training Set Size": train_sizes,
        "Score": train_mean,
        "Lower": train_mean - train_std,
        "Upper": train_mean + train_std,
        "Type": "Training Score",
    }
)

df_val = pd.DataFrame(
    {
        "Training Set Size": train_sizes,
        "Score": val_mean,
        "Lower": val_mean - val_std,
        "Upper": val_mean + val_std,
        "Type": "Validation Score",
    }
)

df = pd.concat([df_train, df_val], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="Training Set Size", y="Score", color="Type", fill="Type"))
    + geom_ribbon(aes(ymin="Lower", ymax="Upper"), alpha=0.2, color="rgba(0,0,0,0)")
    + geom_line(size=2)
    + geom_point(size=4)
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + scale_fill_manual(values=["#306998", "#FFD43B"])
    + scale_y_continuous(limits=[0.55, 1.02])
    + scale_x_continuous(limits=[0, 1700], breaks=list(range(0, 1800, 200)))
    + labs(
        x="Training Set Size (samples)",
        y="Accuracy Score",
        title="learning-curve-basic · letsplot · pyplots.ai",
        color="",
        fill="",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position="bottom",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x = 4800 x 2700 px) and HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
