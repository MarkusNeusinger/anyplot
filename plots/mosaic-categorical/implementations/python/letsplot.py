"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 0.8  # horizontal gap between columns, in percent of the plot width
TILE_GAP = 0.3  # vertical gap between tiles, in percent of the plot height

# Columns: set these to your table's column names
CLASS = "Passenger class"  # role: category_1
STATUS = "Survival status"  # role: category_2
COUNT = "Passengers"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("titanic.csv")
df = pd.DataFrame(
    {
        CLASS: ["First Class"] * 2 + ["Second Class"] * 2 + ["Third Class"] * 2 + ["Crew"] * 2,
        STATUS: ["Survived", "Did Not Survive"] * 4,
        COUNT: [202, 123, 118, 167, 178, 528, 212, 673],
    }
)

# Plot: reads only df and the constants above
# One rectangle per contingency cell: widths follow the class marginals, heights the conditional shares
XMIN, XMAX, YMIN, YMAX = "xmin", "xmax", "ymin", "ymax"
X_CENTER, Y_CENTER, LABEL, SHARE = "x_center", "y_center", "label", "Share"

classes = list(dict.fromkeys(df[CLASS]))
statuses = list(dict.fromkeys(df[STATUS]))
class_totals = df.groupby(CLASS, sort=False)[COUNT].sum()
col_widths = class_totals / class_totals.sum() * 100

rows = []
x_start = 0.0
for cls in classes:
    y_start = 0.0
    for status in statuses:
        count = df.loc[(df[CLASS] == cls) & (df[STATUS] == status), COUNT].sum()
        height = count / class_totals[cls] * 100
        share = round(height)
        rows.append(
            {
                CLASS: cls,
                STATUS: status,
                COUNT: count,
                SHARE: f"{share}%",
                LABEL: f"{count}\n({share}%)",
                XMIN: x_start + GAP / 2,
                XMAX: x_start + col_widths[cls] - GAP / 2,
                YMIN: y_start + TILE_GAP,
                YMAX: y_start + height - TILE_GAP,
                X_CENTER: x_start + col_widths[cls] / 2,
                Y_CENTER: y_start + height / 2,
            }
        )
        y_start += height
    x_start += col_widths[cls]

tiles = pd.DataFrame(rows)
x_breaks = tiles.groupby(CLASS, sort=False)[X_CENTER].first().tolist()

# Headline from the data: survival rate of the first class against the class with the lowest rate
first_status = statuses[0]
rate = tiles[tiles[STATUS] == first_status].set_index(CLASS)[COUNT] / class_totals
best, worst = rate.idxmax(), rate.idxmin()
subtitle = f"{best} passengers were {rate[best] / rate[worst]:.1f}× more likely to survive than {worst} passengers"

# Interactive tooltips: letsplot-distinctive feature for the HTML output
tooltips = (
    layer_tooltips()
    .line(f"Class|@{{{CLASS}}}")
    .line(f"Status|@{{{STATUS}}}")
    .line(f"Count|@{{{COUNT}}}")
    .line(f"Share|@{SHARE}")
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_blank(),
    axis_title=element_text(color=INK, size=13),
    axis_text=element_text(color=INK_SOFT, size=11),
    plot_title=element_text(color=INK, size=16, hjust=0.5, face="bold"),
    plot_subtitle=element_text(color=INK_SOFT, size=11, hjust=0.5),
    legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    legend_text=element_text(color=INK_SOFT, size=11),
    legend_title=element_text(color=INK, size=12),
    legend_position="right",
)

plot = (
    ggplot(tiles)
    + geom_rect(
        aes(xmin=XMIN, xmax=XMAX, ymin=YMIN, ymax=YMAX, fill=STATUS), color=PAGE_BG, size=0.5, tooltips=tooltips
    )
    + geom_text(aes(x=X_CENTER, y=Y_CENTER, label=LABEL), size=5.5, color="white", fontface="bold")
    + scale_fill_manual(values=IMPRINT_PALETTE, breaks=statuses, name=STATUS)
    + scale_x_continuous(name=f"{CLASS}  (width ∝ count)", breaks=x_breaks, labels=classes, limits=[0, 100])
    + scale_y_continuous(name="Share within class (%)", limits=[0, 100], breaks=[0, 25, 50, 75, 100])
    + labs(title="mosaic-categorical · python · letsplot · anyplot.ai", subtitle=subtitle)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
