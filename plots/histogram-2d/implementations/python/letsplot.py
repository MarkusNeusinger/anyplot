""" anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-08
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot import ggsave

LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Bivariate normal distribution with correlation (2000 points)
np.random.seed(42)
n_points = 2000

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
    + geom_bin2d(bins=[25, 25], alpha=0.95)
    + scale_fill_viridis(name="Count", option="viridis")
    + labs(x="Customer Age (years)", y="Annual Spending ($k)", title="histogram-2d · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, color=INK, face="bold"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images to current directory
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
# Clean up empty directory
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
