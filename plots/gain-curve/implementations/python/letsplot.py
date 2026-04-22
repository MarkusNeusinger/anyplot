""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - simulated customer response model
np.random.seed(42)
n_samples = 1000

# Generate realistic customer response data
# True probability of response varies by customer segment
customer_score = np.random.beta(2, 5, n_samples)  # Model prediction scores
# Actual responses are influenced by score with some noise
y_true = (np.random.random(n_samples) < customer_score * 0.6 + 0.05).astype(int)
y_score = customer_score + np.random.normal(0, 0.1, n_samples)
y_score = np.clip(y_score, 0, 1)

# Sort by predicted score descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative gains
total_positives = y_true.sum()
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Add origin point (0, 0)
gains = np.insert(gains, 0, 0)
population_pct = np.insert(population_pct, 0, 0)

# Perfect model curve
positive_rate = total_positives / n_samples
perfect_gains = np.minimum(population_pct / (positive_rate * 100), 1) * 100

# Create DataFrame for plotting
df = pd.DataFrame({"Population": population_pct, "Model": gains, "Random": population_pct, "Perfect": perfect_gains})

# Melt for lets-plot line plotting
df_long = pd.melt(
    df, id_vars=["Population"], value_vars=["Model", "Random", "Perfect"], var_name="Type", value_name="Gain"
)

# Plot
plot = (
    ggplot(df_long, aes(x="Population", y="Gain", color="Type"))
    + geom_line(size=1.5)
    + scale_color_manual(values=["#306998", "#888888", "#FFD43B"], name="Curve")
    + labs(x="Population Targeted (%)", y="Positive Cases Captured (%)", title="gain-curve · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position=[0.85, 0.25],
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
