"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: letsplot 4.9.0 | Python 3.14.4
Quality: pending | Updated: 2026-04-26
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_reverse,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Value"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
n_stages = len(df)
max_value = df[VALUE].iloc[0]
gap = 0.06

polygons = []
labels = []
for i, (stage, value) in enumerate(zip(df[STAGE], df[VALUE], strict=True)):
    w_top = value / max_value
    w_bot = df[VALUE].iloc[i + 1] / max_value if i + 1 < n_stages else w_top
    y_top = i + gap / 2
    y_bot = (i + 1) - gap / 2
    polygons.extend(
        [
            {STAGE: stage, "x": -w_top / 2, "y": y_top},
            {STAGE: stage, "x": w_top / 2, "y": y_top},
            {STAGE: stage, "x": w_bot / 2, "y": y_bot},
            {STAGE: stage, "x": -w_bot / 2, "y": y_bot},
        ]
    )
    labels.append({"x": 0, "y": (y_top + y_bot) / 2, "label": f"{stage}\n{value:,}  ·  {value / max_value * 100:.0f}%"})

df_poly = pd.DataFrame(polygons)
df_poly[STAGE] = pd.Categorical(df_poly[STAGE], categories=df[STAGE], ordered=True)
df_labels = pd.DataFrame(labels)

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill=STAGE, group=STAGE), data=df_poly, color=PAGE_BG, size=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, size=6, fontface="bold", color="white")
    + scale_fill_manual(values=IMPRINT_PALETTE, guide="none")
    + scale_y_reverse()
    + labs(title="funnel-basic · python · letsplot · anyplot.ai", x="", y="")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, color=INK, face="bold", hjust=0.5),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
