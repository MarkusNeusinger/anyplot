""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Quarterly sales by product category
data = {
    "quarter": ["Q1", "Q2", "Q3", "Q4"] * 4,
    "product": ["Electronics"] * 4 + ["Furniture"] * 4 + ["Clothing"] * 4 + ["Accessories"] * 4,
    "sales": [
        120,
        145,
        165,
        190,  # Electronics
        85,
        92,
        78,
        110,  # Furniture
        65,
        88,
        95,
        72,  # Clothing
        45,
        52,
        48,
        58,  # Accessories
    ],
}
df = pd.DataFrame(data)

# Calculate totals for each quarter (for labels)
totals = df.groupby("quarter")["sales"].sum().reset_index()
totals.columns = ["quarter", "total"]
totals["label"] = totals["total"].astype(str)
# Add y position for labels (slightly above total)
totals["y_pos"] = totals["total"] + 15

# Colorblind-safe palette (Python Blue first, then accessible colors)
colors = ["#306998", "#FFD43B", "#8B5CF6", "#F59E0B"]

# Create stacked bar chart with tooltips
plot = (
    ggplot(df, aes(x="quarter", y="sales", fill="product"))
    + geom_bar(
        stat="identity",
        position="stack",
        width=0.7,
        alpha=0.9,
        tooltips=layer_tooltips().title("@product").line("@|@sales K$").format("sales", ".0f"),
    )
    # Add total labels above each stack
    + geom_text(
        data=totals,
        mapping=aes(x="quarter", y="y_pos", label="label"),
        size=16,
        fontface="bold",
        color="#333333",
        inherit_aes=False,
    )
    + scale_fill_manual(values=colors)
    + labs(title="bar-stacked · letsplot · pyplots.ai", x="Quarter", y="Sales (Thousands $)", fill="Product Category")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=18),
        legend_position="right",
        legend_background=element_rect(fill="#F8F9FA", color="#E5E7EB", size=1),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
