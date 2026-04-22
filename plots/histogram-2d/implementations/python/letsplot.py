""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Bivariate normal distribution with correlation (1500 points)
np.random.seed(42)
n_points = 1500

# Create correlated bivariate data with realistic context
# Simulating: Customer Age vs Annual Spending ($k)
mean = [42, 55]  # Average age 42, average spending $55k
cov = [[120, 60], [60, 200]]  # Positive correlation between age and spending

data = np.random.multivariate_normal(mean, cov, n_points)
age = np.clip(data[:, 0], 18, 75)  # Realistic age range
spending = np.clip(data[:, 1], 5, 120)  # Realistic spending range

df = pd.DataFrame({"age": age, "spending": spending})

# Plot - 2D histogram heatmap using geom_bin2d
plot = (
    ggplot(df, aes(x="age", y="spending"))
    + geom_bin2d(bins=[25, 25], alpha=0.9)
    + scale_fill_viridis(name="Count", option="viridis")
    + labs(x="Customer Age (years)", y="Annual Spending ($k)", title="histogram-2d · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save - ggsave creates a subdirectory, so we move the files to current directory
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
