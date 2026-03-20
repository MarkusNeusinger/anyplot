"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — manufacturing defect types sorted by frequency (descending)
categories = ["Scratches", "Dents", "Misalignment", "Cracks", "Discoloration", "Burrs", "Warping", "Contamination"]
counts = [186, 145, 98, 72, 54, 38, 27, 16]

df = pd.DataFrame({"category": categories, "count": counts})

# Cumulative percentage
total = sum(counts)
cumulative_pct = np.cumsum(counts) / total * 100

# Scale cumulative percentage to share y-axis with counts
max_count = max(counts)
y_max = int(max_count * 1.30)
scale_factor = max_count / 100  # 100% maps to max_count, leaving headroom above
cumulative_scaled = cumulative_pct * scale_factor

# 80% threshold line (scaled)
threshold_80_scaled = 80 * scale_factor

# Segments for cumulative line (geom_segment works on discrete x-axis)
seg_df = pd.DataFrame(
    {
        "x": categories[:-1],
        "xend": categories[1:],
        "y": cumulative_scaled[:-1].tolist(),
        "yend": cumulative_scaled[1:].tolist(),
    }
)

# Points for cumulative line markers
df_points = pd.DataFrame(
    {
        "category": categories,
        "cumulative_scaled": cumulative_scaled.tolist(),
        "cumulative_pct": [f"{p:.0f}%" for p in cumulative_pct],
    }
)

# Secondary y-axis tick labels (manual annotation on right side)
sec_ticks = [20, 40, 60, 80, 100]
sec_labels_df = pd.DataFrame(
    {
        "category": [categories[-1]] * len(sec_ticks),
        "y": [t * scale_factor for t in sec_ticks],
        "label": [f"{t}%" for t in sec_ticks],
    }
)

# Highlight bars contributing to the 80% threshold
colors = ["#1E4F72" if cumulative_pct[i] <= 80 else "#306998" for i in range(len(categories))]
df["bar_color"] = colors

# Plot
plot = (
    ggplot(df, aes(x="category", y="count"))  # noqa: F405
    + geom_bar(  # noqa: F405
        aes(fill="bar_color"),  # noqa: F405
        stat="identity",
        width=0.7,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@category")
        .line("Count|@count")
        .format("count", "d"),
        show_legend=False,
    )
    + scale_fill_identity()  # noqa: F405
    # Cumulative percentage line (segments for discrete axis compatibility)
    + geom_segment(  # noqa: F405
        data=seg_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color="#CC5500",
        size=2.0,
        inherit_aes=False,
    )
    # Cumulative line markers
    + geom_point(  # noqa: F405
        data=df_points,
        mapping=aes(x="category", y="cumulative_scaled"),  # noqa: F405
        color="#CC5500",
        fill="white",
        size=5,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Cumulative|@cumulative_pct"),  # noqa: F405
    )
    # 80% threshold horizontal line
    + geom_hline(yintercept=threshold_80_scaled, color="#999999", size=1.0, linetype="dashed")  # noqa: F405
    # Secondary y-axis labels (right side)
    + geom_text(  # noqa: F405
        data=sec_labels_df,
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color="#CC5500",
        size=11,
        hjust=-1.0,
        inherit_aes=False,
    )
    + scale_x_discrete(limits=categories)  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        limits=[0, y_max], expand=[0, 0, 0.05, 0]
    )
    + labs(  # noqa: F405
        x="Defect Type",
        y="Frequency (Count)",
        title="bar-pareto · letsplot · pyplots.ai",
        caption="Orange line = Cumulative %  ·  Dashed line = 80% threshold",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text_x=element_text(angle=45, hjust=1, size=16),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5, face="bold"),  # noqa: F405
        plot_caption=element_text(size=14, color="#777777", hjust=0.5),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4),  # noqa: F405
        plot_background=element_rect(fill="white", color="white"),  # noqa: F405
        plot_margin=[20, 100, 10, 10],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
