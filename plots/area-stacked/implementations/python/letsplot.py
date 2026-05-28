""" anyplot.ai
area-stacked: Stacked Area Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly revenue by product category over 2 years
np.random.seed(42)
months = pd.date_range("2023-01", periods=24, freq="ME")

# Generate revenue data for each product category (in thousands)
# Largest categories at the bottom for easier reading
base_electronics = 80 + np.cumsum(np.random.randn(24) * 3)
base_clothing = 50 + np.cumsum(np.random.randn(24) * 2)
base_home = 35 + np.cumsum(np.random.randn(24) * 2)
base_sports = 25 + np.cumsum(np.random.randn(24) * 1.5)

# Add seasonality
seasonality = 10 * np.sin(np.linspace(0, 4 * np.pi, 24))
electronics = np.maximum(base_electronics + seasonality, 20)
clothing = np.maximum(base_clothing + seasonality * 0.7, 15)
home = np.maximum(base_home + seasonality * 0.5, 10)
sports = np.maximum(base_sports + seasonality * 0.3, 8)

# Create long-format dataframe for lets-plot
df = pd.DataFrame(
    {
        "Month": list(months) * 4,
        "Revenue": np.concatenate([electronics, clothing, home, sports]),
        "Category": ["Electronics"] * 24 + ["Clothing"] * 24 + ["Home & Garden"] * 24 + ["Sports"] * 24,
    }
)

# Convert to numeric for x-axis (months since start)
df["MonthNum"] = df.groupby("Category").cumcount()

# Reorder categories for stacking (largest at bottom)
category_order = ["Electronics", "Clothing", "Home & Garden", "Sports"]
df["Category"] = pd.Categorical(df["Category"], categories=category_order, ordered=True)

# Create stacked area chart
plot = (
    ggplot(df, aes(x="MonthNum", y="Revenue", fill="Category"))
    + geom_area(alpha=0.85, position="stack", size=0.5, color=PAGE_BG)
    + scale_fill_manual(values=IMPRINT)
    + scale_x_continuous(
        name="Month", breaks=[0, 6, 12, 18, 23], labels=["Jan 2023", "Jul 2023", "Jan 2024", "Jul 2024", "Dec 2024"]
    )
    + scale_y_continuous(name="Revenue (Thousands USD)")
    + labs(title="area-stacked · letsplot · anyplot.ai", fill="Product Category")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.5),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, f"plot-{THEME}.html", path=".")
