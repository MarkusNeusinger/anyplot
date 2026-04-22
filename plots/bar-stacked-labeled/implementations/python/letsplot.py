""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Quarterly revenue by product category (in millions)
data = {
    "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
    "Product": [
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
    ],
    "Revenue": [45, 32, 18, 52, 38, 22, 48, 41, 25, 58, 45, 28],
}
df = pd.DataFrame(data)

# Calculate totals for each quarter
totals = df.groupby("Quarter", sort=False)["Revenue"].sum().reset_index()
totals.columns = ["Quarter", "Total"]
totals["Label"] = totals["Total"].apply(lambda x: f"${x}M")

# Create stacked bar chart with total labels
plot = (
    ggplot()
    + geom_bar(
        data=df, mapping=aes(x="Quarter", y="Revenue", fill="Product"), stat="identity", position="stack", width=0.7
    )
    + geom_text(
        data=totals,
        mapping=aes(x="Quarter", y="Total", label="Label"),
        position="identity",
        vjust=-0.5,
        size=18,
        fontface="bold",
        color="#333333",
    )
    + scale_fill_manual(values=["#306998", "#FFD43B", "#5BA85B"])
    + labs(
        title="Quarterly Revenue by Product · bar-stacked-labeled · lets-plot · pyplots.ai",
        x="Quarter",
        y="Revenue (Millions USD)",
        fill="Product Category",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, "plot.html")

# Move files from lets-plot-images subdirectory to current directory (lets-plot quirk)
if os.path.exists("lets-plot-images"):
    for f in ["plot.png", "plot.html"]:
        src = os.path.join("lets-plot-images", f)
        if os.path.exists(src):
            shutil.move(src, f)
    shutil.rmtree("lets-plot-images")
