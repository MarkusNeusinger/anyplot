"""anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: letsplot | Python 3.13
Quality: 91/100 | Created: 2025-12-23
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C7BF" if THEME == "light" else "#333330"

# Okabe-Ito colors: position 1 (increase), position 2 (decrease)
COLOR_INCREASE = "#009E73"
COLOR_DECREASE = "#D55E00"

# Data - Sales figures for 10 products comparing Q1 vs Q4
data = {
    "entity": [
        "Product A",
        "Product B",
        "Product C",
        "Product D",
        "Product E",
        "Product F",
        "Product G",
        "Product H",
        "Product I",
        "Product J",
    ],
    "Q1": [80, 210, 120, 155, 140, 195, 55, 175, 105, 90],
    "Q4": [130, 175, 160, 120, 185, 215, 95, 140, 150, 60],
}
df = pd.DataFrame(data)

# Calculate change direction for color coding
df["change"] = df["Q4"] - df["Q1"]
df["direction"] = df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")

# Prepare long-form data for points
df_long = pd.DataFrame(
    {
        "entity": df["entity"].tolist() * 2,
        "period": ["Q1"] * 10 + ["Q4"] * 10,
        "value": df["Q1"].tolist() + df["Q4"].tolist(),
        "x": [0] * 10 + [1] * 10,
    }
)

# Segment data for connecting lines
df_segments = pd.DataFrame(
    {
        "entity": df["entity"],
        "x_start": [0] * 10,
        "x_end": [1] * 10,
        "y_start": df["Q1"],
        "y_end": df["Q4"],
        "direction": df["direction"],
    }
)

# Merge direction for point coloring
df_long = df_long.merge(df[["entity", "direction"]], on="entity")

# Plot
plot = (
    ggplot()
    + geom_segment(
        data=df_segments,
        mapping=aes(x="x_start", y="y_start", xend="x_end", yend="y_end", color="direction"),
        size=2.5,
        alpha=0.85,
    )
    + geom_point(data=df_long, mapping=aes(x="x", y="value", color="direction"), size=7)
    + geom_text(
        data=df_long[df_long["x"] == 0],
        mapping=aes(x="x", y="value", label="entity"),
        hjust=1.15,
        size=13,
        color=INK_SOFT,
    )
    + geom_text(
        data=df_long[df_long["x"] == 1],
        mapping=aes(x="x", y="value", label="entity"),
        hjust=-0.15,
        size=13,
        color=INK_SOFT,
    )
    + scale_color_manual(values={"Increase": COLOR_INCREASE, "Decrease": COLOR_DECREASE})
    + scale_x_continuous(breaks=[0, 1], labels=["Q1 Sales ($K)", "Q4 Sales ($K)"], limits=[-0.6, 1.6])
    + labs(title="slope-basic · letsplot · anyplot.ai", x="", y="Sales ($K)", color="Change")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=28, color=INK),
        axis_title_y=element_text(size=22, color=INK),
        axis_title_x=element_blank(),
        axis_text_x=element_text(size=20, color=INK_SOFT),
        axis_text_y=element_text(size=18, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=20, color=INK),
        legend_text=element_text(size=18, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x → 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
