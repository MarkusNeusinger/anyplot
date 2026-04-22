""" pyplots.ai
lift-curve: Model Lift Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - simulated customer response model scores
np.random.seed(42)
n_samples = 1000

# Generate realistic response probabilities
# Assume a model that has learned some signal
base_prob = 0.15  # 15% baseline response rate
model_score = np.random.beta(2, 5, n_samples)  # Model predictions

# True responses correlated with model score (good model)
response_prob = 0.05 + 0.6 * model_score  # Higher score = higher response chance
y_true = (np.random.random(n_samples) < response_prob).astype(int)
y_score = model_score + np.random.normal(0, 0.05, n_samples)  # Add noise
y_score = np.clip(y_score, 0, 1)

# Calculate lift curve data
# Sort by predicted score descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift
n_total = len(y_true)
n_positive = y_true.sum()
baseline_rate = n_positive / n_total

# Calculate cumulative values at each decile percentage
percentiles = np.arange(1, 101)
lift_values = []
pct_population = []

for pct in percentiles:
    n_targeted = int(np.ceil(n_total * pct / 100))
    n_positive_captured = y_true_sorted[:n_targeted].sum()

    # Lift = (response rate in targeted group) / (baseline response rate)
    targeted_rate = n_positive_captured / n_targeted
    lift = targeted_rate / baseline_rate if baseline_rate > 0 else 0

    lift_values.append(lift)
    pct_population.append(pct)

# Create DataFrame for plotting
df = pd.DataFrame({"pct_population": pct_population, "lift": lift_values})

# Add reference line data
df_reference = pd.DataFrame({"pct_population": [0, 100], "lift": [1.0, 1.0]})

# Create key points for markers (at deciles)
decile_points = df[df["pct_population"].isin([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])]

# Plot
plot = (
    ggplot()
    + geom_hline(yintercept=1.0, linetype="dashed", color="#888888", size=1.2, alpha=0.7)
    + geom_line(data=df, mapping=aes(x="pct_population", y="lift"), color="#306998", size=2.5)
    + geom_point(
        data=decile_points,
        mapping=aes(x="pct_population", y="lift"),
        color="#306998",
        size=5,
        fill="#FFD43B",
        stroke=1.5,
    )
    + scale_x_continuous(breaks=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], limits=(0, 100))
    + scale_y_continuous(breaks=[0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], limits=(0, None))
    + labs(title="lift-curve · plotnine · pyplots.ai", x="Population Targeted (%)", y="Cumulative Lift")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_minor=element_text(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
