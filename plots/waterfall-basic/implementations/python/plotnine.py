""" anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-06
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - quarterly financial breakdown
categories = ["Starting Balance", "Q1 Sales", "Operating Costs", "R&D Investment", "Tax Payment", "Ending Balance"]
values = [1000, 450, -280, -120, -150, 900]

# Calculate waterfall positions
df = pd.DataFrame({"category": categories, "value": values})
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Calculate cumulative positions for waterfall
running_total = 0
starts = []
ends = []
bar_types = []

for i, val in enumerate(values):
    if i == 0:
        starts.append(0)
        ends.append(val)
        bar_types.append("total")
        running_total = val
    elif i == len(values) - 1:
        starts.append(0)
        ends.append(running_total)
        bar_types.append("total")
    else:
        if val >= 0:
            starts.append(running_total)
            ends.append(running_total + val)
            bar_types.append("positive")
        else:
            starts.append(running_total + val)
            ends.append(running_total)
            bar_types.append("negative")
        running_total += val

df["start"] = starts
df["end"] = ends
df["bar_type"] = bar_types
df["x_pos"] = range(len(categories))

# Create connector lines
connectors = []
for i in range(len(df) - 1):
    if i < len(df) - 2:
        connectors.append(
            {"x_start": df.iloc[i]["x_pos"] + 0.4, "x_end": df.iloc[i + 1]["x_pos"] - 0.4, "y": df.iloc[i]["end"]}
        )
connector_df = pd.DataFrame(connectors) if connectors else pd.DataFrame()

# Colors: green for positive, red for negative, gray for totals
colors = {"total": INK_SOFT, "positive": "#2ecc71", "negative": "#e74c3c"}

# Create plot
plot = ggplot() + geom_rect(
    df, aes(xmin="x_pos - 0.35", xmax="x_pos + 0.35", ymin="start", ymax="end", fill="bar_type")
)

if not connector_df.empty:
    plot = plot + geom_segment(
        connector_df, aes(x="x_start", xend="x_end", y="y", yend="y"), color=INK_SOFT, size=0.5, alpha=0.5
    )

plot = (
    plot
    + geom_text(df, aes(x="x_pos", y="end", label="value"), size=10, color=INK)
    + scale_fill_manual(
        values=colors, name="Category", labels={"total": "Total", "positive": "Increase", "negative": "Decrease"}
    )
    + scale_x_continuous(breaks=list(range(len(categories))), labels=categories, limits=(-0.6, len(categories) - 0.4))
    + labs(x="", y="Amount ($1K)", title="Quarterly Financial Summary · waterfall-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.1, linewidth=0.8),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT, angle=45, ha="right"),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK, face="medium"),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT, size=0.5),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_position="top",
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
