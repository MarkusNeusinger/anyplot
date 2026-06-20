"""anyplot.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "#E0DFD8" if THEME == "light" else "#2A2A27"

# Imprint palette — canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # brand green — bars contributing to 80%
CUMLINE_COLOR = IMPRINT_PALETTE[1]  # lavender — cumulative percentage line
THRESHOLD_COLOR = "#DDCC77"  # amber — warning/caution semantic anchor

# Data — manufacturing defect types sorted by frequency (descending)
categories = ["Scratches", "Dents", "Misalignment", "Cracks", "Discoloration", "Burrs", "Warping", "Contamination"]
counts = [186, 145, 98, 72, 54, 38, 27, 16]

df = pd.DataFrame({"category": categories, "count": counts})

# Cumulative percentage
total = sum(counts)
cumulative_pct = np.cumsum(counts) / total * 100

# Scale cumulative percentages to share the primary y-axis
max_count = max(counts)
y_max = int(max_count * 1.25)
scale_factor = y_max / 100

cumulative_scaled = cumulative_pct * scale_factor
threshold_80_scaled = 80 * scale_factor

# Semantic bar colors: brand green for ≤80% threshold, muted for the tail
bar_colors = [BRAND if cumulative_pct[i] <= 80 else INK_MUTED for i in range(len(categories))]
df["bar_color"] = bar_colors

# Segments to draw cumulative line across discrete x-axis
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

# Simulated secondary y-axis tick labels (right of last bar)
sec_ticks = [20, 40, 60, 80, 100]
sec_labels_df = pd.DataFrame(
    {
        "category": [categories[-1]] * len(sec_ticks),
        "y": [t * scale_factor for t in sec_ticks],
        "label": [f"{t}%" for t in sec_ticks],
    }
)

# Title with dynamic font size (16px baseline for ~67-char title)
title = "bar-pareto · python · letsplot · anyplot.ai"
n = len(title)
title_size = round(16 * 67 / n) if n > 67 else 16
title_size = max(title_size, 11)

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
    # Cumulative percentage line (segments span discrete axis positions)
    + geom_segment(  # noqa: F405
        data=seg_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color=CUMLINE_COLOR,
        size=2.0,
        inherit_aes=False,
    )
    # Cumulative line markers
    + geom_point(  # noqa: F405
        data=df_points,
        mapping=aes(x="category", y="cumulative_scaled"),  # noqa: F405
        color=CUMLINE_COLOR,
        fill=PAGE_BG,
        size=5,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Cumulative|@cumulative_pct"),  # noqa: F405
    )
    # 80% threshold reference line (amber warning anchor)
    + geom_hline(yintercept=threshold_80_scaled, color=THRESHOLD_COLOR, size=1.0, linetype="dashed")  # noqa: F405
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"category": [categories[0]], "y": [threshold_80_scaled], "label": ["80%"]}),
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color=THRESHOLD_COLOR,
        size=9,
        hjust=0.0,
        vjust=-0.7,
        fontface="bold",
        inherit_aes=False,
    )
    # Simulated secondary y-axis labels (right of last category)
    + geom_text(  # noqa: F405
        data=sec_labels_df[sec_labels_df["label"] != "100%"],
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color=CUMLINE_COLOR,
        size=11,
        hjust=-1.6,
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        data=sec_labels_df[sec_labels_df["label"] == "100%"],
        mapping=aes(x="category", y="y", label="label"),  # noqa: F405
        color=CUMLINE_COLOR,
        size=11,
        hjust=-1.6,
        vjust=1.8,
        fontface="bold",
        inherit_aes=False,
    )
    # Cumulative percentage annotations on first 3 points
    + geom_text(  # noqa: F405
        data=df_points.iloc[:3],
        mapping=aes(x="category", y="cumulative_scaled", label="cumulative_pct"),  # noqa: F405
        color=CUMLINE_COLOR,
        size=9,
        vjust=-1.5,
        fontface="bold",
        inherit_aes=False,
    )
    + scale_x_discrete(limits=categories)  # noqa: F405
    + scale_y_continuous(limits=[0, y_max], expand=[0, 0, 0.05, 0])  # noqa: F405
    + labs(  # noqa: F405
        x="Defect Type", y="Frequency (Count)", title=title, caption="Line: cumulative %  ·  Dashed: 80% threshold"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text_x=element_text(angle=45, hjust=1, size=16, color=INK_SOFT),  # noqa: F405
        axis_text_y=element_text(size=16, color=INK_SOFT),  # noqa: F405
        axis_title=element_text(size=20, color=INK),  # noqa: F405
        plot_title=element_text(size=title_size, hjust=0.5, face="bold", color=INK),  # noqa: F405
        plot_caption=element_text(size=14, color=INK_SOFT, hjust=0.5),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.3),  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT),  # noqa: F405
        plot_margin=[20, 90, 10, 10],
    )
    + ggsize(800, 450)  # noqa: F405
)

# Save — scale=4 yields 3200×1800 px from the 800×450 base
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
