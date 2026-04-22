""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_histogram,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    stat_smooth,
    theme,
    theme_minimal,
)


# Data - Product performance dashboard
np.random.seed(42)

# Daily product metrics
n_days = 40
days = pd.date_range("2024-01-01", periods=n_days, freq="D")
products = ["A", "B"]

# Generate time series data
data_list = []
for product in products:
    base = 100 if product == "A" else 85
    trend = 0.5 if product == "A" else 0.8
    sales = base + np.arange(n_days) * trend + np.random.randn(n_days) * 10
    data_list.append(pd.DataFrame({"date": days, "sales": sales, "product": product}))

df_timeseries = pd.concat(data_list, ignore_index=True)
df_timeseries["day_num"] = (df_timeseries["date"] - df_timeseries["date"].min()).dt.days

# Category breakdown data
categories = ["Q1", "Q2", "Q3", "Q4"]
revenues = [45, 32, 28, 18]
df_category = pd.DataFrame({"category": categories, "revenue": revenues})
df_category["category"] = pd.Categorical(df_category["category"], categories=categories, ordered=True)

# Product distribution data
df_prod_a = df_timeseries[df_timeseries["product"] == "A"]["sales"]

# Scatter data - relationship between units sold and profit margin
units = np.random.uniform(100, 500, 60)
margin = 20 + 0.03 * units + np.random.randn(60) * 5
df_scatter = pd.DataFrame({"units": units, "margin": margin})

# Define colors
colors = ["#306998", "#FFD43B"]

# Shared theme for all plots - sized for 4800x2700 canvas
base_theme = theme_minimal() + theme(
    plot_title=element_text(size=22, face="bold", ha="center", margin={"b": 15}),
    axis_title=element_text(size=18),
    axis_text=element_text(size=14),
    legend_text=element_text(size=14),
    legend_title=element_text(size=16, face="bold"),
    panel_grid_major=element_line(color="#cccccc", alpha=0.3),
    panel_grid_minor=element_line(color="#eeeeee", alpha=0.2),
    panel_background=element_rect(fill="white"),
    plot_margin=0.02,
)

# Plot 1: Sales trend over time (Line chart)
p1 = (
    ggplot(df_timeseries, aes(x="day_num", y="sales", color="product"))
    + geom_line(size=1.5)
    + geom_point(size=3, alpha=0.7)
    + stat_smooth(method="lm", se=False, linetype="dashed", size=1.0)
    + scale_color_manual(values=colors)
    + labs(title="Sales Trend", x="Day", y="Sales (Units)", color="Product")
    + base_theme
    + theme(legend_position="right")
)

# Plot 2: Revenue by category (Bar chart)
p2 = (
    ggplot(df_category, aes(x="category", y="revenue", fill="category"))
    + geom_bar(stat="identity", width=0.7, show_legend=False)
    + scale_fill_manual(values=["#306998", "#4A8BBF", "#6BA3D6", "#FFD43B"])
    + labs(title="Quarterly Revenue", x="Quarter", y="Revenue (k$)")
    + base_theme
)

# Plot 3: Sales distribution histogram for Product A
df_hist = pd.DataFrame({"sales": df_prod_a.values})
p3 = (
    ggplot(df_hist, aes(x="sales"))
    + geom_histogram(bins=10, fill="#306998", color="white", alpha=0.8)
    + scale_x_continuous(breaks=[90, 105, 120])
    + labs(title="Sales Distribution (Product A)", x="Sales (Units)", y="Frequency")
    + base_theme
)

# Plot 4: Units vs Margin scatter plot
p4 = (
    ggplot(df_scatter, aes(x="units", y="margin"))
    + geom_point(size=4, color="#306998", alpha=0.7)
    + stat_smooth(method="lm", color="#FFD43B", se=True, fill="#FFD43B", alpha=0.2)
    + labs(title="Units vs Margin", x="Units Sold", y="Profit Margin (%)")
    + base_theme
)

# Compose into 2x2 grid using plotnine's composition operators
# | = beside (columns), / = stack (rows)
top_row = p1 | p2
bottom_row = p3 | p4
grid = top_row / bottom_row

# Draw the grid and add a main figure title using matplotlib's suptitle
fig = grid.draw()
# Resize figure with extra height for the main title (16:9 base + title space)
fig.set_size_inches(16, 11)
# Compress subplots significantly to make room for the main title at the top
fig.subplots_adjust(top=0.76, bottom=0.08, hspace=0.40, wspace=0.25)
# Add main title using suptitle positioned well above all subplot titles
fig.suptitle("subplot-grid · plotnine · pyplots.ai", fontsize=28, fontweight="bold", y=0.90)
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
