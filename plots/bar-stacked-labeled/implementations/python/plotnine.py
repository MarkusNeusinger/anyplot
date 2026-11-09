""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_label,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    position_stack,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per component in the data's order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: segment-label ink per Imprint position, the higher-contrast of near-black and cream on that fill
SEGMENT_INK = ["#1A1A17", "#1A1A17", "#FFFDF6", "#1A1A17", "#FFFDF6", "#1A1A17", "#FFFDF6", "#1A1A17"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT = "Product"  # role: component
REVENUE = "Revenue ($ thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1"] * 3 + ["Q2"] * 3 + ["Q3"] * 3 + ["Q4"] * 3,
        PRODUCT: ["Software", "Hardware", "Services"] * 4,
        REVENUE: [120, 85, 45, 145, 92, 58, 168, 78, 72, 195, 105, 88],
    }
)

# Plot: reads only df and the constants above
quarters = df[QUARTER].dropna().unique().tolist()
components = df[PRODUCT].dropna().unique().tolist()
stacked = df.copy()
stacked[PRODUCT] = pd.Categorical(stacked[PRODUCT], categories=components)
totals = df.groupby(QUARTER, sort=False)[REVENUE].sum(min_count=1).reset_index()
top = totals[REVENUE].max()

title = "Quarterly Revenue by Product · bar-stacked-labeled · python · plotnine · anyplot.ai"
title_size = round(12 * 67 / len(title)) if len(title) > 67 else 12

plot = (
    ggplot(stacked, aes(x=QUARTER, y=REVENUE, fill=PRODUCT))
    + geom_col(position=position_stack(reverse=True), width=0.68, color=PAGE_BG, size=0.4)
    + geom_text(
        aes(label=REVENUE, color=PRODUCT),
        position=position_stack(vjust=0.5, reverse=True),
        format_string="{:.0f}",
        size=9,
        fontweight="bold",
        show_legend=False,
    )
    # Totals sit on a page-coloured box, so a gridline never runs through the digits
    + geom_label(
        aes(x=QUARTER, y=REVENUE, label=REVENUE),
        data=totals,
        inherit_aes=False,
        format_string="{:.0f}",
        va="bottom",
        nudge_y=top * 0.015,
        size=10.5,
        fontweight="bold",
        color=INK,
        fill=PAGE_BG,
        label_size=0,
        label_padding=0.2,
    )
    + scale_x_discrete(limits=quarters)
    + scale_y_continuous(limits=(0, top * 1.14), expand=(0, 0))
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=components)
    + scale_color_manual(values=SEGMENT_INK, limits=components, guide=None)
    + guides(fill=guide_legend(reverse=True))
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=title_size, weight="bold", color=INK),
        plot_title_position="plot",
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
