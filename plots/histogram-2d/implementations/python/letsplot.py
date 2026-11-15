""" anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-15
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
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: sequential ramp for continuous density uses positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 25  # bins per axis, fine enough for the tilt and coarse enough for a smooth gradient

# Columns: set these to your table's column names
AGE = "Customer age (years)"  # role: x
SPENDING = "Annual spending ($k)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("customers.csv")
rng = np.random.default_rng(42)
mean = [42, 55]  # average age 42, average spending $55k
cov = [[120, 60], [60, 200]]  # positive correlation between age and spending
sample = rng.multivariate_normal(mean, cov, 2000)
df = pd.DataFrame({AGE: np.clip(sample[:, 0], 18, 75), SPENDING: np.clip(sample[:, 1], 5, 120)})

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=AGE, y=SPENDING))
    + geom_bin2d(bins=[BINS, BINS])
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name="Customers (count)")
    + labs(title="histogram-2d · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images to current directory
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    shutil.move(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
