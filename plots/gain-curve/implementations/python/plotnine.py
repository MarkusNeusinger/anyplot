""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - simulate a marketing response classification model
np.random.seed(42)
n_samples = 1000

# Generate synthetic model scores and true labels
# Create base scores with correlation to true class
base_score = np.random.randn(n_samples)

# Generate true labels with ~30% positive rate, correlated with score
prob_positive = 1 / (1 + np.exp(-(base_score + np.random.randn(n_samples) * 0.5)))
y_true = (prob_positive > 0.7).astype(int)

# Model predictions - scores correlated with true labels but with noise
y_score = base_score + np.where(y_true == 1, 1.0, -0.5) + np.random.randn(n_samples) * 0.8
y_score = 1 / (1 + np.exp(-y_score))  # Convert to probabilities

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

total_positives = np.sum(y_true)
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100

n_samples = len(y_true)
percentages = np.arange(1, n_samples + 1) / n_samples * 100

# Create DataFrame for plotting
df_model = pd.DataFrame({"percent_population": percentages, "percent_positives": gains, "curve": "Model"})

# Random baseline (diagonal)
df_random = pd.DataFrame({"percent_population": [0, 100], "percent_positives": [0, 100], "curve": "Random (Baseline)"})

# Perfect model: vertical rise to 100% at positive rate, then horizontal
positive_rate = (total_positives / n_samples) * 100
df_perfect = pd.DataFrame(
    {"percent_population": [0, positive_rate, 100], "percent_positives": [0, 100, 100], "curve": "Perfect Model"}
)

# Combine all curves
df = pd.concat([df_model, df_random, df_perfect], ignore_index=True)

# Create plot
plot = (
    ggplot(df, aes(x="percent_population", y="percent_positives", color="curve"))
    + geom_line(size=2.5)
    + scale_color_manual(values={"Model": "#306998", "Random (Baseline)": "#888888", "Perfect Model": "#FFD43B"})
    + scale_x_continuous(breaks=range(0, 101, 20), limits=(0, 100))
    + scale_y_continuous(breaks=range(0, 101, 20), limits=(0, 100))
    + labs(
        title="gain-curve · plotnine · pyplots.ai",
        x="Population Targeted (%)",
        y="Positive Cases Captured (%)",
        color="Curve",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_major=element_line(color="#dddddd", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
        plot_background=element_rect(fill="white"),
        panel_background=element_rect(fill="white"),
    )
)

# Save
plot.save("plot.png", dpi=300)
