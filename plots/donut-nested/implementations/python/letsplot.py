"""anyplot.ai
donut-nested: Nested Donut Chart
Library: letsplot 4.11.0 | Python 3.13.15
Quality: pending | Updated: 2026-08-18
"""

import colorsys
import math
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_pie,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Segment labels sit on top of the (theme-invariant) Imprint fill colors, not on the
# page background, so - unlike the center total label below, which does sit on the page
# background and stays theme-adaptive - they keep a fixed dark ink in both themes: every
# department/child hue here is light enough that a light, dark-theme-adaptive ink would
# lose contrast against it.
DATA_LABEL_INK = "#1A1A17"
DATA_LABEL_INK_SOFT = "#4A4A44"

# Imprint palette (first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Ring geometry (data units), with a gap between rings for visual separation.
# A generously sized center hole keeps the inner-ring labels clear of the total label.
R_INNER_1, R_OUTER_1 = 20, 38
R_INNER_2, R_OUTER_2 = 41, 64
# Biased toward the outer edge of the inner ring, not the midpoint: a horizontal label
# whose anchor sits at a diagonal angle can swing closer to the center than its anchor
# radius as it extends sideways, so the largest wedge needs the extra clearance.
INNER_LABEL_POS = 0.6
LIGHTEN_STEP = 0.14  # lightness added per size rank of a child within its department
LIGHTEN_MAX = 0.88
# geom_text size is in mm, unlike element_text size (pt) - convert the intended pt sizes
MM_PER_PT = 1 / 2.845
INNER_LABEL_MM = 12 * MM_PER_PT
OUTER_LABEL_MM = 10 * MM_PER_PT
CENTER_LABEL_MM = 18 * MM_PER_PT
# Helper columns of the ring tables built below the Data block
CX = "ring_x"
CY = "ring_y"
LABEL_X = "label_x"
LABEL_Y = "label_y"
PCT = "pct"
MID_ANGLE = "mid_angle"

# Columns: set these to your table's column names
LEVEL_1 = "Department"  # role: level_1
LEVEL_2 = "Expense category"  # role: level_2
VALUE = "Budget (million USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
df = pd.DataFrame(
    {
        LEVEL_1: ["Marketing"] * 3 + ["Operations"] * 3 + ["R&D"] * 2 + ["Sales"] * 2,
        LEVEL_2: [
            "Advertising",
            "Events",
            "Content",
            "Facilities",
            "IT Support",
            "Logistics",
            "Product Dev",
            "Research",
            "Field Sales",
            "Inside Sales",
        ],
        VALUE: [18, 8, 6, 12, 10, 8, 15, 10, 9, 4],
    }
)

# Plot
total_value = df[VALUE].sum()
level1_order = list(df[LEVEL_1].dropna().unique())
level2_order = list(df[LEVEL_2].dropna().unique())


def lighten(hex_color, amount):
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, lightness, s = colorsys.rgb_to_hls(r, g, b)
    lightness = min(LIGHTEN_MAX, lightness + amount)
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def ring_table(frame, label_radius):
    frame = frame.copy()
    frame[CX], frame[CY] = 0.0, 0.0
    frac = frame[VALUE] / total_value
    cum_end = frac.cumsum()
    mid_frac = cum_end - frac / 2
    frame[MID_ANGLE] = math.radians(90) - mid_frac * 2 * math.pi
    frame[LABEL_X] = label_radius * frame[MID_ANGLE].apply(math.cos)
    frame[LABEL_Y] = label_radius * frame[MID_ANGLE].apply(math.sin)
    return frame


# Both rings share a single fill scale, so both columns are cast to the same explicitly
# ordered categorical (department names first, then children grouped department-by-
# department) - a plain string column would fall back to alphabetical order and scramble
# both the wedge draw order and the color assignment.
all_categories = level1_order + level2_order

# Inner ring: one wedge per department, in the data's order
inner_df = df.groupby(LEVEL_1, as_index=False, sort=False)[VALUE].sum()
inner_df = ring_table(inner_df, R_INNER_1 + (R_OUTER_1 - R_INNER_1) * INNER_LABEL_POS)
inner_df[LEVEL_1] = pd.Categorical(inner_df[LEVEL_1], categories=all_categories, ordered=True)

# Outer ring: children, grouped department-by-department in the same order as the inner
# ring so that wedge boundaries between the two rings line up exactly.
outer_df = ring_table(df, (R_INNER_2 + R_OUTER_2) / 2)
outer_df[LEVEL_2] = pd.Categorical(outer_df[LEVEL_2], categories=all_categories, ordered=True)

# Color families: department gets the base Imprint hue, children of that department
# lighten in ranked order so the largest child stays closest to the parent hue and
# smaller children read as progressively lighter tints - a second, color-coded cue
# for the size hierarchy the wedge angles already encode.
color_by_dept = {dept: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, dept in enumerate(level1_order)}
child_colors = {}
for dept in level1_order:
    dept_children = df[df[LEVEL_1] == dept].sort_values(VALUE, ascending=False)
    for rank, child in enumerate(dept_children[LEVEL_2]):
        child_colors[child] = lighten(color_by_dept[dept], rank * LIGHTEN_STEP)

# scale_fill_manual takes a plain list matched positionally to all_categories - a dict
# keyed by name does not reliably resolve against a shared categorical fill scale.
all_colors = [color_by_dept[c] for c in level1_order] + [child_colors[c] for c in level2_order]

# Theme configuration
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    plot_title=element_text(size=16, color=INK, hjust=0.5),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    panel_grid=element_blank(),
    legend_position="none",
)

# geom_pie (lets-plot's native pie/donut geom, with no ggplot2 equivalent) draws each
# ring; two rings sharing the same start angle and direction, with values that both sum
# to the same grand total, keep the wedge boundaries radially aligned.
limit = R_OUTER_2 * 1.12
plot = (
    ggplot()
    + geom_pie(
        aes(x=CX, y=CY, slice=VALUE, fill=LEVEL_1),
        data=inner_df,
        stat="identity",
        size=2 * R_OUTER_1,
        size_unit="x",
        hole=R_INNER_1 / R_OUTER_1,
        start=0,
        direction=1,
        color=PAGE_BG,
        spacer_color=PAGE_BG,
        stroke=3,
    )
    + geom_pie(
        aes(x=CX, y=CY, slice=VALUE, fill=LEVEL_2),
        data=outer_df,
        stat="identity",
        size=2 * R_OUTER_2,
        size_unit="x",
        hole=R_INNER_2 / R_OUTER_2,
        start=0,
        direction=1,
        color=PAGE_BG,
        spacer_color=PAGE_BG,
        stroke=3,
    )
    + geom_text(
        aes(x=LABEL_X, y=LABEL_Y, label=LEVEL_1),
        data=inner_df,
        size=INNER_LABEL_MM,
        color=DATA_LABEL_INK,
        fontface="bold",
    )
    + geom_text(aes(x=LABEL_X, y=LABEL_Y, label=LEVEL_2), data=outer_df, size=OUTER_LABEL_MM, color=DATA_LABEL_INK_SOFT)
    + geom_text(x=0, y=0, label=f"Total\n${total_value}M", size=CENTER_LABEL_MM, color=INK, fontface="bold")
    + scale_fill_manual(values=all_colors)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-limit, limit))
    + scale_y_continuous(limits=(-limit, limit))
    + labs(title="donut-nested · python · letsplot · anyplot.ai")
    + anyplot_theme
)

# The fixed aspect leaves the rest of the canvas transparent; a one-panel grid in the
# page color paints the whole 2400 x 2400 canvas.
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
