""" pyplots.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_bar,
    geom_histogram,
    geom_point,
    geom_rect,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    ggtitle,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Multivariate dataset with numeric and categorical columns
np.random.seed(42)
n = 200

# Create 4 clusters with different characteristics
categories = np.repeat(["Cluster A", "Cluster B", "Cluster C", "Cluster D"], n // 4)
cluster_centers_x = {"Cluster A": 25, "Cluster B": 60, "Cluster C": 35, "Cluster D": 70}
cluster_centers_y = {"Cluster A": 70, "Cluster B": 30, "Cluster C": 45, "Cluster D": 65}

x = np.array([cluster_centers_x[c] + np.random.randn() * 8 for c in categories])
y = np.array([cluster_centers_y[c] + np.random.randn() * 8 for c in categories])
value = x * 0.8 + np.random.randn(n) * 10 + 40

# Define brush selection region - selects Cluster A and part of Cluster C
brush_xmin, brush_xmax = 15, 45
brush_ymin, brush_ymax = 55, 85

# Determine which points are selected by the brush
selected = (x >= brush_xmin) & (x <= brush_xmax) & (y >= brush_ymin) & (y <= brush_ymax)
point_alpha = np.where(selected, 0.9, 0.2)

df = pd.DataFrame(
    {"x": x, "y": y, "category": categories, "value": value, "selected": selected, "point_alpha": point_alpha}
)

# Colors - colorblind-friendly palette with distinct hues
colors = ["#E69F00", "#56B4E9", "#009E73", "#CC79A7"]  # Orange, Sky Blue, Teal, Pink

n_selected = selected.sum()
n_total = len(df)

# Common theme scaled for 4800x2700 output
common_theme = theme_minimal() + theme(
    axis_title=element_text(size=18),
    axis_text=element_text(size=14),
    plot_title=element_text(size=20, face="bold"),
    legend_text=element_text(size=14),
    legend_title=element_text(size=16),
    panel_grid_major=element_line(color="#E5E5E5", size=0.5),
    panel_grid_minor=element_blank(),
)

# Brush rectangle data
brush_df = pd.DataFrame({"xmin": [brush_xmin], "xmax": [brush_xmax], "ymin": [brush_ymin], "ymax": [brush_ymax]})

# Tooltips for scatter plot
tooltips = (
    layer_tooltips()
    .title("@category")
    .line("X: @x")
    .line("Y: @y")
    .line("Value: @value")
    .line("Selected: @selected")
    .format("x", ".1f")
    .format("y", ".1f")
    .format("value", ".1f")
)

# 1. SCATTER PLOT with brush selection rectangle
scatter = (
    ggplot(df, aes("x", "y"))
    # Brush selection rectangle
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=brush_df,
        inherit_aes=False,
        fill="#3B82F6",
        alpha=0.12,
        color="#3B82F6",
        linetype="dashed",
        size=1.5,
    )
    # Points with selection-based alpha
    + geom_point(aes(color="category", alpha="point_alpha"), size=6, tooltips=tooltips)
    + scale_color_manual(values=colors)
    + scale_alpha_identity()
    + labs(x="Measurement X", y="Measurement Y", title=f"Scatter Plot ({n_selected}/{n_total} selected)")
    + common_theme
    + theme(legend_position="none")
    + ggsize(750, 550)
)

# 2. HISTOGRAM with linked selection highlighting
# Create separate data for selected and unselected, stacking selected on top
df_hist_unselected = df[~df["selected"]].copy()
df_hist_unselected["selection_state"] = "Unselected"
df_hist_selected = df[df["selected"]].copy()
df_hist_selected["selection_state"] = "Selected"

# Plot unselected first (gray, low alpha), then selected (colored, high alpha)
histogram = (
    ggplot(df_hist_unselected, aes("value"))
    + geom_histogram(bins=20, fill="#CCCCCC", alpha=0.5, color="white", size=0.3)
    + geom_histogram(aes("value"), data=df_hist_selected, bins=20, fill="#3B82F6", alpha=0.85, color="white", size=0.3)
    + labs(x="Value", y="Count", title="Value Distribution")
    + common_theme
    + theme(legend_position="none")
    + ggsize(750, 550)
)

# 3. BAR CHART with linked selection highlighting
# Calculate counts per category, split by selection state
category_counts_all = df.groupby("category").size().reset_index(name="total")
category_counts_selected = df[df["selected"]].groupby("category").size().reset_index(name="selected_count")
category_counts = category_counts_all.merge(category_counts_selected, on="category", how="left").fillna(0)
category_counts["unselected_count"] = category_counts["total"] - category_counts["selected_count"]

# Create stacked bar data
bar_data = []
for _, row in category_counts.iterrows():
    cat = row["category"]
    bar_data.append({"category": cat, "count": row["unselected_count"], "state": "Unselected"})
    bar_data.append({"category": cat, "count": row["selected_count"], "state": "Selected"})
bar_df = pd.DataFrame(bar_data)

bar = (
    ggplot(bar_df, aes("category", "count", fill="state"))
    + geom_bar(stat="identity", position="stack", alpha=0.85, width=0.7)
    + scale_fill_manual(values={"Selected": "#3B82F6", "Unselected": "#CCCCCC"}, name="Selection")
    + labs(x="Category", y="Count", title="Category Distribution")
    + common_theme
    + theme(legend_position="bottom")
    + ggsize(750, 550)
)

# 4. SUMMARY panel with selection information and legend
summary_data = []
for i, (cat, color) in enumerate(zip(["Cluster A", "Cluster B", "Cluster C", "Cluster D"], colors, strict=True)):
    cat_selected = df[(df["category"] == cat) & df["selected"]].shape[0]
    cat_total = df[df["category"] == cat].shape[0]
    summary_data.append(
        {"category": cat, "x": 1, "y": 4 - i, "label": f"{cat}: {cat_selected}/{cat_total}", "color": color}
    )

summary_df = pd.DataFrame(summary_data)

summary_panel = (
    ggplot(summary_df, aes("x", "y", color="category"))
    + geom_point(size=12)
    + geom_text(aes(label="label"), hjust=0, nudge_x=0.12, size=14)
    + scale_color_manual(values=colors)
    + scale_x_continuous(limits=[0.5, 3])
    + scale_y_continuous(limits=[0, 5])
    + labs(title=f"Selection Summary\n{n_selected} of {n_total} points")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=18, face="bold"),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + ggsize(500, 550)
)

# Combine all plots using gggrid for linked views layout
combined = gggrid([scatter, histogram, bar, summary_panel], ncol=2, align=True)

# Add overall title
combined = (
    combined
    + ggtitle("linked-views-selection · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(plot_title=element_text(size=26, face="bold"))
)

# Save as PNG (scaled 3x for 4800x2700 px)
ggsave(combined, "plot.png", path=".", scale=3)

# Save as HTML (interactive version)
ggsave(combined, "plot.html", path=".")
