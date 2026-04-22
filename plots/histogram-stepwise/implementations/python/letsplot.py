""" pyplots.ai
histogram-stepwise: Step Histogram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401


LetsPlot.setup_html()

# Data - Generate two distributions for comparison (temperature readings)
np.random.seed(42)
morning_temps = np.random.normal(loc=18, scale=4, size=500)  # Morning temperatures (°C)
afternoon_temps = np.random.normal(loc=26, scale=5, size=500)  # Afternoon temperatures (°C)

# Compute histogram bins manually for step representation
bins = 30
all_data = np.concatenate([morning_temps, afternoon_temps])
bin_edges = np.linspace(all_data.min(), all_data.max(), bins + 1)

# Calculate histogram counts for each distribution
morning_counts, _ = np.histogram(morning_temps, bins=bin_edges)
afternoon_counts, _ = np.histogram(afternoon_temps, bins=bin_edges)

# Create step data: duplicate each point for step appearance
# For step histogram, we need x values at bin edges and corresponding y values
step_data = []
for counts, label in [(morning_counts, "Morning"), (afternoon_counts, "Afternoon")]:
    for i in range(len(counts)):
        # Left edge of bin at count level
        step_data.append({"x": bin_edges[i], "y": counts[i], "period": label})
        # Right edge of bin at count level
        step_data.append({"x": bin_edges[i + 1], "y": counts[i], "period": label})

df_step = pd.DataFrame(step_data)

# Plot - Step histogram using geom_line (outline only, no fill)
plot = (
    ggplot(df_step, aes(x="x", y="y", color="period"))
    + geom_line(size=2.5)
    + scale_color_manual(values=["#306998", "#FFD43B"])
    + labs(x="Temperature (°C)", y="Frequency", title="histogram-stepwise · letsplot · pyplots.ai", color="Time Period")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
