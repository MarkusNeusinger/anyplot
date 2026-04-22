""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-26
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - theoretical bias-variance tradeoff curves
np.random.seed(42)
complexity = np.linspace(0.5, 10, 100)

# Bias squared: decreases with complexity
bias_squared = 2.5 / (1 + 0.5 * complexity)

# Variance: increases with complexity
variance = 0.05 * complexity**1.5

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.3)

# Total error: sum of all components
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create DataFrame in long format for plotting
df = pd.DataFrame(
    {
        "complexity": np.tile(complexity, 4),
        "error": np.concatenate([bias_squared, variance, irreducible_error, total_error]),
        "component": (
            ["Bias²"] * len(complexity)
            + ["Variance"] * len(complexity)
            + ["Irreducible Error"] * len(complexity)
            + ["Total Error"] * len(complexity)
        ),
    }
)

# Define colors for each component
colors = ["#306998", "#FFD43B", "#888888", "#DC2626"]

# Annotation data
annotations = pd.DataFrame(
    {
        "x": [optimal_complexity + 0.4, 1.5, 8.5, 5.0],
        "y": [optimal_error + 0.5, 2.0, 2.0, 0.05],
        "label": [
            "Optimal\nComplexity",
            "Underfitting\n(High Bias)",
            "Overfitting\n(High Variance)",
            "Total Error = Bias² + Variance + Irreducible Error",
        ],
    }
)

# Create the plot
plot = (
    ggplot(df, aes(x="complexity", y="error", color="component"))
    + geom_line(size=2)
    + geom_vline(xintercept=optimal_complexity, linetype="dashed", color="#444444", size=1)
    + scale_color_manual(values=colors)
    + geom_text(data=annotations, mapping=aes(x="x", y="y", label="label"), inherit_aes=False, size=14, color="#444444")
    + labs(
        x="Model Complexity",
        y="Prediction Error",
        title="curve-bias-variance-tradeoff · letsplot · pyplots.ai",
        color="Component",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
