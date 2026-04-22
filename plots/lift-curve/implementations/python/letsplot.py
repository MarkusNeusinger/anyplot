# ruff: noqa: F405
"""pyplots.ai
lift-curve: Model Lift Chart
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-27
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data: Simulated customer response model
np.random.seed(42)
n_samples = 1000

# Create realistic model scores with good discrimination
# Higher scores for positive class, lower for negative
y_true = np.concatenate([np.ones(200), np.zeros(800)])  # 20% response rate
positive_scores = np.random.beta(5, 2, 200)  # Skewed high
negative_scores = np.random.beta(2, 5, 800)  # Skewed low
y_score = np.concatenate([positive_scores, negative_scores])

# Shuffle data
shuffle_idx = np.random.permutation(n_samples)
y_true = y_true[shuffle_idx]
y_score = y_score[shuffle_idx]

# Calculate lift curve
sorted_idx = np.argsort(y_score)[::-1]  # Sort by score descending
y_true_sorted = y_true[sorted_idx]

# Calculate cumulative metrics
n_positive = np.sum(y_true)
baseline_rate = n_positive / n_samples
cumsum_positive = np.cumsum(y_true_sorted)
population_pct = np.arange(1, n_samples + 1) / n_samples * 100
response_rate = cumsum_positive / np.arange(1, n_samples + 1)
lift = response_rate / baseline_rate

# Sample points for smoother curve (every 1%)
sample_points = np.arange(10, n_samples + 1, 10)
df = pd.DataFrame({"population_pct": population_pct[sample_points - 1], "lift": lift[sample_points - 1]})

# Add starting point
df = pd.concat([pd.DataFrame({"population_pct": [0], "lift": [lift[0]]}), df], ignore_index=True)

# Reference line data (horizontal at y=1)
ref_df = pd.DataFrame({"population_pct": [0, 100], "lift": [1, 1]})

# Create plot
plot = (
    ggplot()
    + geom_line(aes(x="population_pct", y="lift"), data=ref_df, color="#888888", size=1.5, linetype="dashed")
    + geom_line(aes(x="population_pct", y="lift"), data=df, color="#306998", size=2.5)
    + geom_point(
        aes(x="population_pct", y="lift"), data=df[df["population_pct"] % 10 == 0], color="#306998", size=5, alpha=0.8
    )
    + labs(x="Population Targeted (%)", y="Cumulative Lift", title="lift-curve · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=list(range(0, 101, 10)))
    + scale_y_continuous(breaks=[1, 2, 3, 4, 5, 6])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Add annotation for reference line
plot = plot + geom_text(
    aes(x="x", y="y", label="label"),
    data=pd.DataFrame({"x": [85], "y": [1.15], "label": ["Random (Lift = 1)"]}),
    size=14,
    color="#666666",
)

# Save as PNG and HTML (path='.' to save in current directory)
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
