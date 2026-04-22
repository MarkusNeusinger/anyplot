""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: plotnine 0.15.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-14
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
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


# Data - quarterly financial breakdown
categories = ["Revenue", "Product Costs", "Marketing", "Operations", "R&D", "Admin", "Taxes", "Net Profit"]
values = [500, -150, -60, -45, -35, -30, -40, 140]

# Calculate waterfall positions
df = pd.DataFrame({"category": categories, "value": values})
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Calculate cumulative positions for waterfall
running_total = 0
starts = []
ends = []
bar_types = []

for i, (_cat, val) in enumerate(zip(categories, values, strict=True)):
    if i == 0:
        # First bar: starts at 0, ends at value
        starts.append(0)
        ends.append(val)
        bar_types.append("total")
        running_total = val
    elif i == len(categories) - 1:
        # Last bar: total bar starting from 0
        starts.append(0)
        ends.append(running_total)
        bar_types.append("total")
    else:
        # Middle bars: changes
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

# Create connector line data (from end of one bar to start of next)
connectors = []
for i in range(len(df) - 1):
    if i < len(df) - 2:  # Don't connect to the final total bar
        connectors.append(
            {"x_start": df.iloc[i]["x_pos"] + 0.4, "x_end": df.iloc[i + 1]["x_pos"] - 0.4, "y": df.iloc[i]["end"]}
        )
connector_df = pd.DataFrame(connectors)

# Add labels for values
df["label_y"] = df.apply(lambda row: row["end"] + 10 if row["end"] >= row["start"] else row["start"] + 10, axis=1)
df["label_text"] = df.apply(
    lambda row: f"+{int(row['value'])}" if row["value"] > 0 and row["bar_type"] != "total" else str(int(row["value"])),
    axis=1,
)

# Colors: blue for totals, green for positive, red for negative
colors = {"total": "#306998", "positive": "#2ECC71", "negative": "#E74C3C"}

# Create plot
plot = (
    ggplot()
    + geom_rect(df, aes(xmin="x_pos - 0.4", xmax="x_pos + 0.4", ymin="start", ymax="end", fill="bar_type"))
    + geom_segment(
        connector_df, aes(x="x_start", xend="x_end", y="y", yend="y"), color="#666666", size=0.5, linetype="dashed"
    )
    + geom_text(df, aes(x="x_pos", y="label_y", label="label_text"), size=12, color="#333333")
    + scale_fill_manual(
        values=colors, name="Type", labels={"total": "Total", "positive": "Increase", "negative": "Decrease"}
    )
    + labs(x="", y="Amount ($K)", title="Quarterly Financials · waterfall-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=16, rotation=30, ha="right"),
        axis_text_y=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_minor=element_blank(),
    )
)

# Add x-axis labels
plot = plot + scale_x_continuous(breaks=list(range(len(categories))), labels=categories)

plot.save("plot.png", dpi=300)
