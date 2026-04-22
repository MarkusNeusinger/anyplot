""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Sales funnel example
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

# Calculate percentages and build funnel geometry
max_value = values[0]
n_stages = len(stages)

# Build polygon data for trapezoid shapes
polygons = []
y_top = 0
stage_height = 1.0

for i, (stage, value) in enumerate(zip(stages, values, strict=True)):
    # Calculate widths proportional to max value
    width = value / max_value

    # Next stage width (minimum 15% to keep readable shape)
    if i < n_stages - 1:
        next_width = max(values[i + 1] / max_value, 0.15)
    else:
        next_width = max(width * 0.5, 0.10)  # Wider base for final stage

    y_bottom = y_top + stage_height

    # Trapezoid vertices (clockwise from top-left)
    half_w_top = width / 2
    half_w_bottom = next_width / 2

    polygons.append({"stage": stage, "x": -half_w_top, "y": y_top, "order": 0})
    polygons.append({"stage": stage, "x": half_w_top, "y": y_top, "order": 1})
    polygons.append({"stage": stage, "x": half_w_bottom, "y": y_bottom, "order": 2})
    polygons.append({"stage": stage, "x": -half_w_bottom, "y": y_bottom, "order": 3})

    y_top = y_bottom

df_poly = pd.DataFrame(polygons)

# Label positions (center of each trapezoid)
labels = []
y_pos = 0.5
for stage, value in zip(stages, values, strict=True):
    pct = value / max_value * 100
    labels.append({"stage": stage, "x": 0, "y": y_pos, "label": f"{stage}\n{value:,} ({pct:.0f}%)"})
    y_pos += stage_height

df_labels = pd.DataFrame(labels)

# Colors for each stage - Python blue as primary with variations
colors = ["#306998", "#4A90D9", "#FFD43B", "#F5A623", "#D45D00"]

# Create plot
plot = (
    ggplot()  # noqa: F405
    + geom_polygon(  # noqa: F405
        aes(x="x", y="y", fill="stage", group="stage"),  # noqa: F405
        data=df_poly,
        color="white",
        size=2,
        alpha=0.9,
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=df_labels,
        size=12,
        color="white",
        fontface="bold",
    )
    + scale_fill_manual(values=colors)  # noqa: F405
    + scale_y_reverse()  # noqa: F405  # Top to bottom
    + labs(title="funnel-basic · letsplot · pyplots.ai", x="", y="")  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5, face="bold"),  # noqa: F405
        legend_position="none",
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save outputs to current directory
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
