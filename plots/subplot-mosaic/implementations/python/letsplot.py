""" anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

np.random.seed(42)

# Panel A: Wide time series overview (top - spans full width)
dates = pd.date_range("2024-01-01", periods=100, freq="D")
revenue = np.cumsum(np.random.randn(100) * 10 + 5) + 1000
df_overview = pd.DataFrame({"date": dates, "revenue": revenue})
df_overview["day_num"] = range(len(df_overview))

# Panel B: Bar chart data (middle left - large panel)
categories = ["Product A", "Product B", "Product C", "Product D", "Product E"]
sales = [450, 380, 290, 520, 340]
df_bar = pd.DataFrame({"category": categories, "sales": sales})

# Panel C: Scatter data (middle right)
x_scatter = np.random.uniform(20, 80, 60)
y_scatter = x_scatter * 0.7 + np.random.randn(60) * 8 + 10
df_scatter = pd.DataFrame({"effort": x_scatter, "output": y_scatter})

# Panel D: Histogram data (bottom left)
values = np.concatenate([np.random.normal(50, 10, 150), np.random.normal(80, 8, 100)])
df_hist = pd.DataFrame({"metric": values})

# Panel E: Line chart data (bottom middle)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
growth = [2.1, 3.5, 2.8, 4.2, 3.9, 5.1]
df_line = pd.DataFrame({"month": months, "growth": growth})
df_line["month_num"] = range(len(df_line))

# Panel F: Heatmap data (bottom right - with some empty notation)
matrix_data = []
for row_label in ["Q1", "Q2", "Q3", "Q4"]:
    for col_label in ["Region A", "Region B", "Region C"]:
        value = int(np.random.uniform(60, 100))
        matrix_data.append({"quarter": row_label, "region": col_label, "value": value})
df_heatmap = pd.DataFrame(matrix_data)

# Theme configuration
base_theme = theme_minimal() + theme(
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    plot_title=element_text(size=22, face="bold", color=INK),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
)

# Panel A: Wide time series (top, spans all 3 columns)
plot_a = (
    ggplot(df_overview, aes("day_num", "revenue"))
    + geom_area(fill=IMPRINT[0], alpha=0.3)
    + geom_line(color=IMPRINT[0], size=2)
    + labs(x="Day", y="Revenue ($)", title="Daily Revenue Overview")
    + base_theme
)

# Panel B: Bar chart (middle row, spans 2/3 width)
plot_b = (
    ggplot(df_bar, aes("category", "sales"))
    + geom_bar(stat="identity", fill=IMPRINT[0], color=INK_SOFT, size=0.6, alpha=0.85)
    + labs(x="Product Category", y="Units Sold", title="Sales by Product")
    + base_theme
    + theme(axis_text_x=element_text(angle=45, hjust=1))
)

# Panel C: Scatter plot (middle row, 1/3 width)
plot_c = (
    ggplot(df_scatter, aes("effort", "output"))
    + geom_point(color=IMPRINT[0], size=6, alpha=0.7, fill=IMPRINT[0])
    + geom_smooth(method="lm", color=IMPRINT[1], size=1.5, se=False)
    + labs(x="Effort (hours)", y="Output (units)", title="Effort vs Output")
    + base_theme
)

# Panel D: Histogram (bottom left)
plot_d = (
    ggplot(df_hist, aes("metric"))
    + geom_histogram(bins=25, fill=IMPRINT[0], color=INK_SOFT, alpha=0.8, size=0.3)
    + labs(x="Performance Score", y="Frequency", title="Score Distribution")
    + base_theme
)

# Panel E: Line chart with points (bottom middle)
plot_e = (
    ggplot(df_line, aes("month_num", "growth"))
    + geom_line(color=IMPRINT[0], size=2.5)
    + geom_point(color=IMPRINT[0], size=8, fill=IMPRINT[0], alpha=0.8)
    + scale_x_continuous(breaks=list(range(6)), labels=months)
    + labs(x="Month", y="Growth Rate (%)", title="Monthly Growth")
    + base_theme
)

# Panel F: Heatmap (bottom right)
plot_f = (
    ggplot(df_heatmap, aes("region", "quarter", fill="value"))
    + geom_tile(color=INK_SOFT, size=1)
    + geom_text(aes(label="value"), format=".0f", size=14, color=INK)
    + scale_fill_viridis(name="Value")
    + labs(x="Region", y="Quarter", title="Regional Performance")
    + base_theme
    + theme(legend_position="right", legend_text=element_text(size=14))
)

# Create mosaic layout using ggbunch with regions
# AAA (top - full width)
# BBC (middle - B spans 2/3, C spans 1/3)
# DEF (bottom - three equal panels)
final_plot = ggbunch(
    plots=[plot_a, plot_b, plot_c, plot_d, plot_e, plot_f],
    regions=[
        (0, 0, 1.0, 0.22),
        (0, 0.24, 0.65, 0.38),
        (0.67, 0.24, 0.33, 0.38),
        (0, 0.64, 0.32, 0.36),
        (0.34, 0.64, 0.32, 0.36),
        (0.68, 0.64, 0.32, 0.36),
    ],
) + ggsize(1600, 900)

output_dir = os.path.dirname(os.path.abspath(__file__))

# Add centered title to the plot
final_plot_with_title = (
    final_plot
    + ggtitle("subplot-mosaic · letsplot · anyplot.ai")
    + theme(plot_title=element_text(size=26, color=INK, face="bold", hjust=0.5))
)

ggsave(final_plot_with_title, os.path.join(output_dir, f"plot-{THEME}.png"), scale=3)
ggsave(final_plot_with_title, os.path.join(output_dir, f"plot-{THEME}.html"))
