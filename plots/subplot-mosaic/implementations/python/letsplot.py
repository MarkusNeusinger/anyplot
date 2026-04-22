""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data
np.random.seed(42)

# Panel A: Wide time series overview (top - spans full width)
dates = pd.date_range("2024-01-01", periods=100, freq="D")
revenue = np.cumsum(np.random.randn(100) * 10 + 5) + 1000
df_overview = pd.DataFrame({"date": dates, "revenue": revenue})
df_overview["day_num"] = range(len(df_overview))

# Panel B: Bar chart data (middle left - large panel, spans 2 cols)
categories = ["Product A", "Product B", "Product C", "Product D", "Product E"]
sales = [450, 380, 290, 520, 340]
df_bar = pd.DataFrame({"category": categories, "sales": sales})

# Panel C: Scatter data (middle right - small panel)
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

# Panel F: Heatmap data (bottom right)
matrix_data = []
for row_label in ["Q1", "Q2", "Q3", "Q4"]:
    for col_label in ["Region A", "Region B", "Region C"]:
        value = int(np.random.uniform(60, 100))
        matrix_data.append({"quarter": row_label, "region": col_label, "value": value})
df_heatmap = pd.DataFrame(matrix_data)

# Common theme with subtle grid
base_theme = theme_minimal() + theme(
    axis_title=element_text(size=18),
    axis_text=element_text(size=14),
    plot_title=element_text(size=20, face="bold"),
    panel_grid=element_line(color="#CCCCCC", size=0.5),
)

# Create individual plots (without ggsize - will be set in ggbunch regions)
# Mosaic pattern: AAA (top - full width overview)
#                 BBC (bar spans 2/3, scatter 1/3)
#                 DEF (three equal bottom panels)

# Panel A: Wide time series (top, spans all 3 columns)
plot_a = (
    ggplot(df_overview, aes("day_num", "revenue"))
    + geom_area(fill="#306998", alpha=0.3)
    + geom_line(color="#306998", size=1.5)
    + labs(x="Day", y="Revenue ($)", title="Daily Revenue Overview")
    + base_theme
)

# Panel B: Bar chart (middle row, spans columns 0-1)
plot_b = (
    ggplot(df_bar, aes("category", "sales"))
    + geom_bar(stat="identity", fill="#FFD43B", color="#306998", size=0.8)
    + labs(x="Product Category", y="Units Sold", title="Sales by Product")
    + base_theme
    + theme(axis_text_x=element_text(angle=45, hjust=1))
)

# Panel C: Scatter plot (middle row, column 2)
plot_c = (
    ggplot(df_scatter, aes("effort", "output"))
    + geom_point(color="#306998", size=5, alpha=0.7)
    + geom_smooth(method="lm", color="#FFD43B", size=2)
    + labs(x="Effort (hours)", y="Output (units)", title="Effort vs Output")
    + base_theme
)

# Panel D: Histogram (bottom left)
plot_d = (
    ggplot(df_hist, aes("metric"))
    + geom_histogram(bins=25, fill="#306998", color="white", alpha=0.85)
    + labs(x="Performance Score", y="Frequency", title="Score Distribution")
    + base_theme
)

# Panel E: Line chart with points (bottom middle)
plot_e = (
    ggplot(df_line, aes("month_num", "growth"))
    + geom_line(color="#FFD43B", size=2.5)
    + geom_point(color="#306998", size=7)
    + scale_x_continuous(breaks=list(range(6)), labels=months)
    + labs(x="Month", y="Growth Rate (%)", title="Monthly Growth")
    + base_theme
)

# Panel F: Heatmap (bottom right)
plot_f = (
    ggplot(df_heatmap, aes("region", "quarter", fill="value"))
    + geom_tile(color="white", size=1.5)
    + geom_text(aes(label="value"), format=".0f", size=12, color="white")
    + scale_fill_gradient(low="#FFD43B", high="#306998")
    + labs(x="Region", y="Quarter", title="Regional Performance")
    + base_theme
    + theme(legend_position="none")
)

# Use ggbunch() for mosaic layout with relative coordinates (0-1 range)
# Region format: (x, y, width, height) where (0,0) is top-left, (1,1) is bottom-right
# Mosaic layout:
#   Row 0: [A - full width]
#   Row 1: [B - 2/3 width] [C - 1/3 width]
#   Row 2: [D - 1/3 width] [E - 1/3 width] [F - 1/3 width]

final_plot = (
    ggbunch(
        plots=[plot_a, plot_b, plot_c, plot_d, plot_e, plot_f],
        regions=[
            # (x, y, width, height)
            (0, 0, 1.0, 0.22),  # A: top full width
            (0, 0.24, 0.65, 0.38),  # B: middle left (2/3)
            (0.67, 0.24, 0.33, 0.38),  # C: middle right (1/3)
            (0, 0.64, 0.32, 0.36),  # D: bottom left
            (0.34, 0.64, 0.32, 0.36),  # E: bottom middle
            (0.68, 0.64, 0.32, 0.36),  # F: bottom right
        ],
    )
    + ggsize(1600, 900)
    + ggtitle("subplot-mosaic · letsplot · pyplots.ai")
)

# Get current directory for saving
output_dir = os.path.dirname(os.path.abspath(__file__))

# Save as PNG (scale 3x for ~4800px width target)
ggsave(final_plot, os.path.join(output_dir, "plot.png"), scale=3)

# Save as HTML for interactivity
ggsave(final_plot, os.path.join(output_dir, "plot.html"))
