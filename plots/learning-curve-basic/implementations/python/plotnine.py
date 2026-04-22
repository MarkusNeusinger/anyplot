""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Simulating learning curve with typical ML model behavior
np.random.seed(42)

# Training set sizes (10 points from 50 to 800 samples)
train_sizes = np.linspace(50, 800, 10).astype(int)

# Simulate cross-validation folds (5 folds)
n_folds = 5

# Training scores: start high, stay high (model learns training data well)
train_mean = 0.99 - 0.15 * np.exp(-train_sizes / 150)
train_std = 0.02 * np.exp(-train_sizes / 300) + 0.005

# Validation scores: start lower, improve with more data (learning pattern)
val_mean = 0.65 + 0.25 * (1 - np.exp(-train_sizes / 250))
val_std = 0.08 * np.exp(-train_sizes / 400) + 0.01

# Create DataFrame for plotting
df_train = pd.DataFrame(
    {
        "Training Set Size": train_sizes,
        "Score": train_mean,
        "Score_low": train_mean - train_std,
        "Score_high": train_mean + train_std,
        "Type": "Training Score",
    }
)

df_val = pd.DataFrame(
    {
        "Training Set Size": train_sizes,
        "Score": val_mean,
        "Score_low": val_mean - val_std,
        "Score_high": val_mean + val_std,
        "Type": "Validation Score",
    }
)

df = pd.concat([df_train, df_val], ignore_index=True)

# Colors: Python Blue for training, Python Yellow for validation
colors = {"Training Score": "#306998", "Validation Score": "#FFD43B"}

# Create plot
plot = (
    ggplot(df, aes(x="Training Set Size", y="Score", color="Type", fill="Type"))
    + geom_ribbon(aes(ymin="Score_low", ymax="Score_high"), alpha=0.25, color="none")
    + geom_line(size=2)
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(
        x="Training Set Size",
        y="Accuracy Score",
        title="learning-curve-basic · plotnine · pyplots.ai",
        color="",
        fill="",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_position=(0.85, 0.25),
    )
)

# Save
plot.save("plot.png", dpi=300)
