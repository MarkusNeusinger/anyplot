""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data: Quarterly sales figures (in thousands) comparing Q1 vs Q4
entities = [
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
]
q1_sales = [120, 85, 200, 150, 95, 175, 110, 140, 65, 180]
q4_sales = [165, 70, 230, 135, 145, 190, 85, 160, 110, 155]

# Calculate change direction for color coding
changes = ["Increase" if q4 >= q1 else "Decrease" for q1, q4 in zip(q1_sales, q4_sales, strict=True)]

# Create long-format DataFrame for lines
df_long = pd.DataFrame(
    {
        "entity": entities * 2,
        "x": [1] * len(entities) + [2] * len(entities),
        "value": q1_sales + q4_sales,
        "change": changes * 2,
    }
)

# Create label DataFrames
df_labels_left = pd.DataFrame(
    {
        "entity": entities,
        "x": [1] * len(entities),
        "value": q1_sales,
        "change": changes,
        "label": [f"{e} ({v})" for e, v in zip(entities, q1_sales, strict=True)],
    }
)

df_labels_right = pd.DataFrame(
    {
        "entity": entities,
        "x": [2] * len(entities),
        "value": q4_sales,
        "change": changes,
        "label": [str(v) for v in q4_sales],
    }
)

# Plot
plot = (
    ggplot(df_long, aes(x="x", y="value", group="entity", color="change"))
    + geom_line(size=1.5, alpha=0.8)
    + geom_point(size=5)
    # Left labels (entity name + value)
    + geom_text(aes(label="label"), data=df_labels_left, ha="right", nudge_x=-0.08, size=10)
    # Right labels (value only)
    + geom_text(aes(label="label"), data=df_labels_right, ha="left", nudge_x=0.08, size=10)
    + scale_color_manual(values={"Increase": "#306998", "Decrease": "#FFD43B"})
    + scale_x_continuous(breaks=[1, 2], labels=["Q1", "Q4"], limits=(0.3, 2.7))
    + labs(
        x="",
        y="Sales (thousands $)",
        title="Product Sales Q1 vs Q4 · slope-basic · plotnine · pyplots.ai",
        color="Change Direction",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=18),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
