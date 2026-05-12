"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times by service type
np.random.seed(42)

services = ["API Gateway", "Database Query", "Authentication", "File Storage", "Cache Lookup", "Email Service"]

data = []
distributions = {
    "API Gateway": (120, 40, 3),
    "Database Query": (250, 100, 5),
    "Authentication": (80, 25, 2),
    "File Storage": (300, 80, 4),
    "Cache Lookup": (15, 8, 2),
    "Email Service": (180, 60, 6),
}

for service in services:
    mean, std, n_outliers = distributions[service]
    values = np.random.normal(mean, std, 80)
    outliers = np.random.normal(mean + 4 * std, std / 2, n_outliers)
    all_values = np.concatenate([values, outliers])
    all_values = np.maximum(all_values, 5)

    for val in all_values:
        data.append({"Service": service, "Response Time (ms)": val})

df = pd.DataFrame(data)

# Create horizontal box plot
plot = (
    ggplot(df, aes(x="Response Time (ms)", y="Service"))
    + geom_boxplot(
        fill=BRAND, color=INK_SOFT, alpha=0.7, outlier_color=INK_SOFT, outlier_size=4, outlier_alpha=0.6, size=1.0
    )
    + labs(x="Response Time (ms)", y="Service Type", title="box-horizontal · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        panel_grid_major_x=element_line(color=INK_SOFT, size=0.2),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
