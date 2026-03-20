"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
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
y_max = int(max_count * 1.20)
scale_factor = y_max / 120  # Map 100% well below y_max to avoid top collision

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

# Secondary y-axis tick labels — use a dummy x position past the last category
# Position labels at a fixed numeric offset beyond the last bar
sec_ticks = [20, 40, 60, 80, 100]
sec_labels_df = pd.DataFrame(
    {
        "category": [categories[-1]] * len(sec_ticks),
        "y": [t * scale_factor for t in sec_ticks],
        "label": [f"{t}%" for t in sec_ticks],
    }
)

# Highlight bars contributing to the 80% threshold with distinct colors
colors = ["#1B3A4B" if cumulative_pct[i] <= 80 else "#7EB8DA" for i in range(len(categories))]
df["bar_color"] = colors

# Plot
plot = (
    ggplot(df, aes(x="category", y="count"))  # noqa: F405
    + geom_bar(  # noqa: F405
        aes(fill="bar_color"),  # noqa: F405
        stat="identity",
        width=0.72,
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
        color="#D35400",
        size=2.0,
        inherit_aes=False,
    )
    # Cumulative line markers
    + geom_point(  # noqa: F405
        data=df_points,
        mapping=aes(x="category", y="cumulative_scaled"),  # noqa: F405
        color="#D35400",
        fill="white",
        size=5,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Cumulative|@cumulative_pct"),  # noqa: F405
    )
    # 80% threshold horizontal line
    + geom_hline(yintercept=threshold_80_scaled, color="#888888", size=0.8, linetype="dashed")  # noqa: F405
    # 80% threshold label
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"category": [categories[0]], "y": [threshold_80_scaled], "label": ["80% threshold"]}),
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color="#888888",
        size=9,
        hjust=0.0,
        vjust=-0.7,
        inherit_aes=False,
    )
    # Secondary y-axis labels (right side) — exclude 100% to avoid overlap with last point
    + geom_text(  # noqa: F405
        data=sec_labels_df[sec_labels_df["label"] != "100%"],
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color="#D35400",
        size=11,
        hjust=-1.8,
        fontface="bold",
        inherit_aes=False,
    )
    # 100% label offset vertically to avoid cumulative point marker
    + geom_text(  # noqa: F405
        data=sec_labels_df[sec_labels_df["label"] == "100%"],
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color="#D35400",
        size=11,
        hjust=-1.8,
        vjust=1.8,
        fontface="bold",
        inherit_aes=False,
    )
    # Cumulative percentage annotations on the line points (top 3 only to avoid clutter)
    + geom_text(  # noqa: F405
        data=df_points.iloc[:3],
        mapping=aes(x="category", y="cumulative_scaled", label="cumulative_pct"),  # noqa: F405
        color="#D35400",
        size=9,
        vjust=-1.5,
        fontface="bold",
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
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
        plot_background=element_rect(fill="white", color="white"),  # noqa: F405
        plot_margin=[20, 130, 10, 10],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
