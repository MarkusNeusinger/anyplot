"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_histogram,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    stat_smooth,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
PANEL = "Panel"  # role: extra
X = "x"  # role: x
Y = "y"  # role: y
GROUP = "Group"  # role: extra

# Data: replace this block with your own long table, for example df = pd.read_csv("dashboard.csv")
np.random.seed(42)
n_days = 40
frames = []
for product, base, slope in [("A", 100, 0.5), ("B", 85, 0.8)]:
    sales = base + np.arange(n_days) * slope + np.random.randn(n_days) * 10
    frames.append(pd.DataFrame({PANEL: "trend", X: np.arange(n_days), Y: sales, GROUP: product}))
quarters = ["Q1", "Q2", "Q3", "Q4"]
frames.append(pd.DataFrame({PANEL: "bar", X: np.arange(4), Y: [45, 32, 28, 18], GROUP: quarters}))
units = np.random.uniform(100, 500, 60)
margin = 20 + 0.03 * units + np.random.randn(60) * 5
frames.append(pd.DataFrame({PANEL: "scatter", X: units, Y: margin, GROUP: ""}))
df = pd.concat(frames, ignore_index=True)

# Plot
panels = df[PANEL].unique().tolist()  # data order: trend, bar, scatter
trend, bars, scatter = (df[df[PANEL] == panels[i % len(panels)]] for i in range(3))
hist = trend[trend[GROUP] == trend[GROUP].iloc[0]]
groups = trend[GROUP].unique().tolist()
bar_labels = bars[GROUP].tolist()

# Shared theme for all plots - sized for the 3200x1800 canvas
base_theme = theme_minimal() + theme(
    plot_title=element_text(size=22, face="bold", ha="center", color=INK, margin={"b": 10}),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, face="bold", color=INK),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_background=element_rect(fill=PAGE_BG, color=None),
    plot_background=element_rect(fill=PAGE_BG, color=None),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    plot_margin=0.01,
    plot_margin_top=0.01,
)

# Plot 1: Sales trend over time (Line chart)
p1 = (
    ggplot(trend, aes(x=X, y=Y, color=GROUP))
    + geom_line(size=1.2)
    + geom_point(size=3, alpha=0.8)
    + stat_smooth(method="lm", se=False, linetype="dashed", size=0.8, color=INK_SOFT)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_y_continuous(limits=(trend[Y].min(), trend[Y].max() * 1.22))
    + labs(title="Sales Trend", x="Day", y="Sales (Units)", color="Product")
    + base_theme
    + theme(legend_position="inside", legend_position_inside=(0.02, 0.99), legend_direction="horizontal")
)

# Plot 2: Revenue by category (Bar chart)
p2 = (
    ggplot(bars, aes(x=X, y=Y, fill=GROUP))
    + geom_col(width=0.7, show_legend=False)
    + scale_x_continuous(breaks=bars[X].tolist(), labels=bar_labels)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=bar_labels)
    + labs(title="Quarterly Revenue", x="Quarter", y="Revenue (k$)")
    + base_theme
)

# Plot 3: Sales distribution histogram for the first product
p3 = (
    ggplot(hist, aes(x=Y))
    + geom_histogram(bins=10, fill=BRAND, color=PAGE_BG, alpha=0.8)
    + scale_x_continuous(breaks=np.linspace(hist[Y].min(), hist[Y].max(), len(groups) + 1).round(-1).tolist())
    + labs(title=f"Sales Distribution (Product {groups[0]})", x="Sales (Units)", y="Frequency")
    + base_theme
)

# Plot 4: Units vs Margin scatter plot
p4 = (
    ggplot(scatter, aes(x=X, y=Y))
    + geom_point(size=4, color=BRAND, alpha=0.7)
    + stat_smooth(method="lm", color=IMPRINT_PALETTE[1], se=True, fill=IMPRINT_PALETTE[1], alpha=0.15, size=0.8)
    + labs(title="Units vs Margin", x="Units Sold", y="Profit Margin (%)")
    + base_theme
)

# Compose into 2x2 grid using plotnine's composition operators
top_margin = theme(plot_margin_top=0.06)
top_row = (p1 + top_margin) | (p2 + top_margin)
bottom_row = p3 | p4
grid = top_row / bottom_row

# Draw the grid and customize overall layout
fig = grid.draw()
fig.set_size_inches(16, 9)
fig.patch.set_facecolor(PAGE_BG)

# Add main title with better positioning
fig.suptitle("subplot-grid · python · plotnine · anyplot.ai", fontsize=28, fontweight="bold", y=0.985, color=INK)

fig.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
