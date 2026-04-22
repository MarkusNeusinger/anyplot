""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

# Fix import conflict: script named plotnine.py shadows the plotnine package
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Sales funnel with 5 stages showing clear progression
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

df = pd.DataFrame({"stage": stages, "value": values})

# Calculate funnel geometry - centered bars with widths proportional to values
max_value = df["value"].max()
df["width"] = df["value"] / max_value  # Normalize widths (0-1 scale)
df["y"] = range(len(df), 0, -1)  # Y positions (top to bottom)
df["xmin"] = -df["width"] / 2
df["xmax"] = df["width"] / 2
df["ymin"] = df["y"] - 0.4
df["ymax"] = df["y"] + 0.4

# Labels with values and percentages
df["label"] = df.apply(lambda row: f"{row['stage']}\n{row['value']:,} ({row['value'] / max_value * 100:.0f}%)", axis=1)

# Stage as ordered categorical for legend order
df["stage"] = pd.Categorical(df["stage"], categories=stages, ordered=True)

# Colors - Python Blue to lighter shades for progression
colors = ["#306998", "#4A7FA8", "#6495B8", "#7EABC8", "#98C1D8"]

# Create funnel plot using rectangles
plot = (
    ggplot(df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="stage"))
    + geom_rect(color="white", size=0.5)
    + geom_text(aes(x=0, y="y", label="label"), color="white", size=14, fontweight="bold")
    + scale_fill_manual(values=colors)
    + labs(title="funnel-basic · plotnine · pyplots.ai", x="", y="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
