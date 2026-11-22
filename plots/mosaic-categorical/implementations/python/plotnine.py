""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CLASS = "Passenger class"  # role: category_1
OUTCOME = "Outcome"  # role: category_2
COUNT = "Passengers"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("titanic_counts.csv")
df = pd.DataFrame(
    {
        CLASS: ["First", "First", "Second", "Second", "Third", "Third"],
        OUTCOME: ["Survived", "Did Not Survive"] * 3,
        COUNT: [203, 122, 118, 167, 178, 528],
    }
)

# Plot: reads only df and the constants above
GAP = 0.02  # white space between tiles, in axes fractions
classes = df[CLASS].unique().tolist()
outcomes = df[OUTCOME].unique().tolist()

# Mosaic geometry: widths follow the class share, heights the conditional outcome share
class_totals = df.groupby(CLASS, sort=False)[COUNT].sum().reindex(classes)
widths = class_totals / class_totals.sum()
x_starts = widths.cumsum() - widths

rects = []
for cls in classes:
    cell = df[df[CLASS] == cls].set_index(OUTCOME)[COUNT].reindex(outcomes)
    heights = cell / cell.sum() * (1 - GAP)
    y_starts = heights.cumsum() - heights + GAP / 2 * pd.Series(range(len(outcomes)), index=outcomes)
    for outcome in outcomes:
        rects.append(
            {
                "xmin": x_starts[cls],
                "xmax": x_starts[cls] + widths[cls] - GAP,
                "ymin": y_starts[outcome],
                "ymax": y_starts[outcome] + heights[outcome],
                OUTCOME: outcome,
                COUNT: cell[outcome],
            }
        )
rect_df = pd.DataFrame(rects)
rect_df["x_center"] = (rect_df["xmin"] + rect_df["xmax"]) / 2
rect_df["y_center"] = (rect_df["ymin"] + rect_df["ymax"]) / 2

# Class names and survival rate of the first outcome level below each column
column_x = (x_starts + (widths - GAP) / 2).tolist()
rates = [df[(df[CLASS] == cls) & (df[OUTCOME] == outcomes[0])][COUNT].sum() / class_totals[cls] for cls in classes]
label_y = -0.055
class_labels = pd.DataFrame({"x": column_x, "y": label_y, "label": classes})
rate_labels = pd.DataFrame(
    {"x": column_x, "y": label_y * 2.1, "label": [f"{r:.0%} {outcomes[0].lower()}" for r in rates]}
)

best, worst = max(rates), min(rates)
subtitle = (
    f"{classes[rates.index(best)]} class: {best:.0%} {outcomes[0].lower()}, vs {worst:.0%} in "
    f"{classes[rates.index(worst)]} class ({best / worst:.1f}× higher)"
)

plot = (
    ggplot(rect_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill=OUTCOME), color=PAGE_BG, size=0.8)
    + geom_text(aes(x="x_center", y="y_center", label=COUNT), color="white", size=9, fontweight="bold")
    + geom_text(data=class_labels, mapping=aes(x="x", y="y", label="label"), size=10, color=INK, fontweight="bold")
    + geom_text(data=rate_labels, mapping=aes(x="x", y="y", label="label"), size=8.5, color=INK_SOFT)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=outcomes)
    + scale_x_continuous(expand=(0, 0.01), limits=(0, 1.01))
    + scale_y_continuous(expand=(0, 0), limits=(label_y * 3.1, 1.04))
    + labs(
        title="mosaic-categorical · python · plotnine · anyplot.ai",
        subtitle=subtitle,
        y=f"Share of {CLASS.lower()} by {OUTCOME.lower()}",
        fill=OUTCOME,
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.3),
        axis_line_y=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=12, ha="center", color=INK, fontweight="bold"),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT),
        axis_title_x=element_blank(),
        axis_title_y=element_text(size=10, color=INK),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
