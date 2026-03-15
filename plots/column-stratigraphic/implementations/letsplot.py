""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-15
"""
# ruff: noqa: F405

import os
import shutil

import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - synthetic sedimentary section with 10 layers (depth increasing downward)
layers = pd.DataFrame(
    {
        "top": [0, 15, 35, 55, 80, 110, 135, 165, 195, 230],
        "bottom": [15, 35, 55, 80, 110, 135, 165, 195, 230, 260],
        "lithology": [
            "Sandstone",
            "Shale",
            "Limestone",
            "Siltstone",
            "Sandstone",
            "Conglomerate",
            "Shale",
            "Limestone",
            "Siltstone",
            "Sandstone",
        ],
        "formation": [
            "Basal Sand Fm",
            "Dark Shale Mbr",
            "Reef Limestone Fm",
            "Gray Silt Mbr",
            "Channel Sand Fm",
            "Gravel Bed Fm",
            "Marine Shale Fm",
            "Platform Carb Fm",
            "Tidal Flat Mbr",
            "Upper Sand Fm",
        ],
        "age": [
            "Triassic",
            "Triassic",
            "Jurassic",
            "Jurassic",
            "Jurassic",
            "Cretaceous",
            "Cretaceous",
            "Cretaceous",
            "Paleogene",
            "Paleogene",
        ],
    }
)

layers["thickness"] = layers["bottom"] - layers["top"]
layers["xmin"] = 0.0
layers["xmax"] = 1.0

# Lithology color palette (earthy geological tones)
lithology_colors = {
    "Sandstone": "#F2CC6B",
    "Shale": "#8B8B8B",
    "Limestone": "#5B9BD5",
    "Siltstone": "#B5A48B",
    "Conglomerate": "#D4726A",
}
lithology_order = ["Sandstone", "Shale", "Limestone", "Siltstone", "Conglomerate"]

# Build label data: formation names (right) + age labels (left)
label_rows = []
for _, row in layers.iterrows():
    mid_depth = (row["top"] + row["bottom"]) / 2
    label_rows.append({"x": 1.12, "y": mid_depth, "label": row["formation"]})

age_spans = {"Triassic": (0, 35), "Jurassic": (35, 110), "Cretaceous": (110, 195), "Paleogene": (195, 260)}
for age_name, (age_top, age_bottom) in age_spans.items():
    label_rows.append({"x": -0.12, "y": (age_top + age_bottom) / 2, "label": age_name})

labels_df = pd.DataFrame(label_rows)

# Age boundary dashed lines
age_boundary_depths = [35, 110, 195]
boundaries_df = pd.DataFrame(
    {"x": [-0.02] * 3, "y": age_boundary_depths, "xend": [1.02] * 3, "yend": age_boundary_depths}
)

# Plot
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="top", ymax="bottom", fill="lithology"),
        data=layers,
        color="black",
        size=0.8,
        alpha=0.85,
        tooltips=layer_tooltips()
        .line("@lithology")
        .line("Depth: @top\u2013@bottom m")
        .line("Thickness: @thickness m")
        .line("Formation: @formation")
        .line("Age: @age"),
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=boundaries_df,
        linetype="dashed",
        color="#888888",
        size=0.7,
        show_legend=False,
    )
    + geom_text(aes(x="x", y="y", label="label"), data=labels_df, size=10, color="#333333")
    + scale_fill_manual(values=lithology_colors, name="Lithology", limits=lithology_order)
    + scale_y_reverse()
    + scale_x_continuous(limits=[-0.35, 1.85])
    + labs(title="column-stratigraphic \u00b7 letsplot \u00b7 pyplots.ai", y="Depth (m)", x="")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_y=element_text(size=20),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        legend_position="bottom",
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(size=0.3, color="#dddddd"),
        panel_grid_minor_y=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
