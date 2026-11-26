"""anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-07-26
"""

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
    geom_polygon,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_identity,
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
DARK_INK = "#1A1A17"  # wedge fills are theme-invariant, so labels on them are too
LIGHT_INK = "#FFFFFF"

# Imprint palette: one position per top-level branch, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RING_BOUNDS = [(0, 28), (31, 52), (55, 80)]  # inner and outer radius of each ring, with gaps between rings
TINTS = [0.0, 0.4, 0.7]  # share of white mixed into the branch color, per ring
LUMINANCE_SPLIT = 0.5  # fills darker than this carry white labels
ARC_POINTS = 40  # vertices per arc edge
LABEL_SIZES = [6, 5.5, 4.5]  # geom_text size in mm, per ring

# Columns: set these to your table's column names
LEVEL_1 = "Department"  # role: level_1
LEVEL_2 = "Team"  # role: level_2
LEVEL_3 = "Project"  # role: level_3
VALUE = "Budget ($K)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
df = pd.DataFrame(
    {
        LEVEL_1: ["Eng"] * 4 + ["Sales"] * 3 + ["Mktg"] * 3,
        LEVEL_2: ["Backend"] * 2 + ["Frontend"] * 2 + ["North"] * 2 + ["South"] + ["Digital"] * 2 + ["Brand"],
        LEVEL_3: ["API", "Database", "Web App", "Mobile", "Enterprise", "SMB", "Retail", "SEO", "Ads", "Events"],
        VALUE: [15, 10, 12, 8, 18, 7, 9, 6, 8, 7],
    }
)

# Plot: reads only df and the constants above
SEGMENT, RING, FILL, ANGLE, X, Y, GROUP, LABEL_COLOR = "Segment", "Ring", "Fill", "Angle", "x", "y", "group", "ink"
LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3]
TOTAL = df[VALUE].sum()

# Keep each branch contiguous, in the data's order, so a parent's arc covers its children's arcs
branch_rank = {name: i for i, name in enumerate(df[LEVEL_1].unique())}
df = df.sort_values(LEVEL_1, key=lambda s: s.map(branch_rank), kind="stable").reset_index(drop=True)


def mix_with_white(hex_color, share):
    """The hex color with `share` of white blended in."""
    channels = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(c + (255 - c) * share):02X}" for c in channels)


def luminance(hex_color):
    """Relative luminance of a hex color."""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wedge(inner_r, outer_r, start, end):
    """Polygon vertices of an annular sector between two angles."""
    angles = [start + (end - start) * i / ARC_POINTS for i in range(ARC_POINTS + 1)]
    outer = [(outer_r * math.cos(a), outer_r * math.sin(a)) for a in angles]
    inner = [(inner_r * math.cos(a), inner_r * math.sin(a)) for a in reversed(angles)]
    return outer + inner


polygon_rows, label_rows = [], []
for ring, (inner_r, outer_r) in enumerate(RING_BOUNDS):
    segments = df.groupby(LEVELS[: ring + 1], sort=False)[VALUE].sum().reset_index()
    sweeps = segments[VALUE] / TOTAL * 2 * math.pi
    starts = math.pi / 2 - sweeps.cumsum() + sweeps  # clockwise from twelve o'clock
    for seg_id, (row, start, sweep) in enumerate(zip(segments.itertuples(index=False), starts, sweeps, strict=True)):
        branch_color = IMPRINT_PALETTE[branch_rank[row[0]] % len(IMPRINT_PALETTE)]
        fill = mix_with_white(branch_color, TINTS[ring])
        name = row[ring]
        seg_key = ring * 1000 + seg_id
        for px, py in wedge(inner_r, outer_r, start, start - sweep):
            polygon_rows.append(
                {X: px, Y: py, GROUP: seg_key, SEGMENT: name, FILL: fill, VALUE: row[len(LEVELS[: ring + 1])]}
            )
        mid = start - sweep / 2
        mid_r = (inner_r + outer_r) / 2 if ring else outer_r * 0.55
        on_dark_fill = ring == 0 and luminance(fill) < LUMINANCE_SPLIT
        label_rows.append(
            {
                X: mid_r * math.cos(mid),
                Y: mid_r * math.sin(mid),
                SEGMENT: name,
                RING: ring,
                LABEL_COLOR: LIGHT_INK if on_dark_fill else DARK_INK,
            }
        )

polygons = pd.DataFrame(polygon_rows)
polygons[ANGLE] = (polygons[VALUE] / TOTAL * 100).round(1).astype(str) + "%"
labels = pd.DataFrame(label_rows)
limit = RING_BOUNDS[-1][1] * 1.1

plot = (
    ggplot(polygons)
    + geom_polygon(
        aes(x=X, y=Y, fill=FILL, group=GROUP),
        color=PAGE_BG,
        size=0.75,
        tooltips=layer_tooltips()
        .line(f"@{{{SEGMENT}}}")
        .line(f"{VALUE}|@{{{VALUE}}}")
        .line(f"Share of total|@{{{ANGLE}}}"),
    )
    + scale_fill_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-limit, limit))
    + scale_y_continuous(limits=(-limit, limit))
    + labs(
        title="sunburst-basic · python · letsplot · anyplot.ai",
        subtitle=f"Budget allocation by {LEVEL_1.lower()}, {LEVEL_2.lower()} and {LEVEL_3.lower()} {VALUE.split(' ', 1)[1]}",
    )
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, hjust=0.5, color=INK, face="bold"),
        plot_subtitle=element_text(size=11, hjust=0.5, color=INK),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_border=element_blank(),
    )
)
for ring, size in enumerate(LABEL_SIZES):
    ring_labels = labels[labels[RING] == ring]
    for ink in ring_labels[LABEL_COLOR].unique():
        plot += geom_text(
            aes(x=X, y=Y, label=SEGMENT),
            data=ring_labels[ring_labels[LABEL_COLOR] == ink],
            size=size,
            color=ink,
            fontface="bold" if ring == 0 else "plain",
        )

# The one-panel grid paints the whole square canvas, because coord_fixed leaves strips transparent
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
