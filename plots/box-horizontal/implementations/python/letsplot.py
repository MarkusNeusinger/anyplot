"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first position is the single series color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SERVICE = "Service Type"  # role: categories
RESPONSE_TIME = "Response Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
distributions = {
    "API Gateway": (120, 40, 3),
    "Database Query": (250, 100, 5),
    "Authentication": (80, 25, 2),
    "File Storage": (300, 80, 4),
    "Cache Lookup": (15, 8, 2),
    "Email Service": (180, 60, 6),
}
services, times = [], []
for service, (mean, std, n_outliers) in distributions.items():
    values = np.random.normal(mean, std, 80)
    outliers = np.random.normal(mean + 4 * std, std / 2, n_outliers)
    all_values = np.maximum(np.concatenate([values, outliers]), 5)
    services.extend([service] * len(all_values))
    times.extend(all_values)
df = pd.DataFrame({SERVICE: services, RESPONSE_TIME: times})

# Plot
plot = (
    ggplot(df, aes(x=RESPONSE_TIME, y=SERVICE))
    + geom_boxplot(
        fill=IMPRINT_PALETTE[0],
        color=INK_SOFT,
        alpha=0.7,
        outlier_color=INK_SOFT,
        outlier_size=1.5,
        outlier_alpha=0.6,
        size=0.6,
    )
    + labs(title="box-horizontal · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        panel_grid_major_x=element_line(color=INK_SOFT, size=0.15),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.3),
    )
    + ggsize(800, 450)
)

# Save PNG (scale 4x gives 3200 x 1800 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
