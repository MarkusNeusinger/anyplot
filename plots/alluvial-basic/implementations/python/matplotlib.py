"""anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.path import Path


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIME_POINT = "Time point"  # role: time_point
NEXT_TIME_POINT = "Next time point"  # role: extra
CATEGORY = "Party"  # role: category
NEXT_CATEGORY = "Party at next time point"  # role: extra
VALUE = "Voters in party (thousand)"  # role: value
FLOW = "Flow (thousand voters)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# Voter migration between parties across four election cycles: one row per band,
# from (time point, party) to (next time point, party).
parties = ["Party A", "Party B", "Party C", "Independent"]
years = ["2012", "2016", "2020", "2024"]
flow_matrices = [
    [[380, 20, 30, 20], [25, 310, 25, 20], [10, 15, 80, 15], [5, 5, 15, 25]],
    [[340, 15, 45, 20], [20, 285, 30, 15], [15, 15, 105, 15], [5, 5, 20, 50]],
    [[310, 10, 40, 20], [20, 255, 30, 15], [15, 10, 160, 15], [5, 5, 20, 70]],
]
df = pd.DataFrame(
    [
        {
            TIME_POINT: years[k],
            NEXT_TIME_POINT: years[k + 1],
            CATEGORY: src,
            NEXT_CATEGORY: dst,
            VALUE: sum(matrix[i]),
            FLOW: matrix[i][j],
        }
        for k, matrix in enumerate(flow_matrices)
        for i, src in enumerate(parties)
        for j, dst in enumerate(parties)
    ]
)

# Plot: reads only df and the constants above
time_points = list(dict.fromkeys([*df[TIME_POINT], *df[NEXT_TIME_POINT]]))
categories = list(dict.fromkeys([*df[CATEGORY], *df[NEXT_CATEGORY]]))
colors = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(categories)}

# Block value per (time point, category): outflow, or inflow in the last column
out_sum = df.groupby([TIME_POINT, CATEGORY])[VALUE].first()
in_sum = df.groupby([NEXT_TIME_POINT, NEXT_CATEGORY])[FLOW].sum()
node_values = {
    (tp, cat): (out_sum if (tp, cat) in out_sum.index else in_sum).get((tp, cat), 0.0)
    for tp in time_points
    for cat in categories
}

# Layout: stacked blocks per column, heights proportional to value
x_positions = {tp: 2.0 + 2.0 * i for i, tp in enumerate(time_points)}
node_width = 0.9
total_height = 7.5
node_gap = 0.25
usable_height = total_height - (len(categories) - 1) * node_gap

node_bounds = {}
for tp in time_points:
    column_total = sum(node_values[(tp, cat)] for cat in categories)
    y = 0.5
    for cat in categories:
        height = node_values[(tp, cat)] / column_total * usable_height
        node_bounds[(tp, cat)] = (y, height)
        y += height + node_gap

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Bands between neighboring columns: width proportional to flow, bezier edges
from_offsets = dict.fromkeys(node_bounds, 0.0)
to_offsets = dict.fromkeys(node_bounds, 0.0)
for _, row in df.iterrows():
    tp_from, tp_to, cat_from, cat_to, flow = (
        row[TIME_POINT],
        row[NEXT_TIME_POINT],
        row[CATEGORY],
        row[NEXT_CATEGORY],
        row[FLOW],
    )
    from_total = sum(node_values[(tp_from, c)] for c in categories)
    to_total = sum(node_values[(tp_to, c)] for c in categories)
    from_height = flow / from_total * usable_height
    to_height = flow / to_total * usable_height

    x0 = x_positions[tp_from] + node_width / 2
    x1 = x_positions[tp_to] - node_width / 2
    mid_x = (x0 + x1) / 2

    y0_start = node_bounds[(tp_from, cat_from)][0] + from_offsets[(tp_from, cat_from)]
    y0_end = y0_start + from_height
    y1_start = node_bounds[(tp_to, cat_to)][0] + to_offsets[(tp_to, cat_to)]
    y1_end = y1_start + to_height

    verts = [
        (x0, y0_start),
        (mid_x, y0_start),
        (mid_x, y1_start),
        (x1, y1_start),
        (x1, y1_end),
        (mid_x, y1_end),
        (mid_x, y0_end),
        (x0, y0_end),
        (x0, y0_start),
    ]
    codes = [
        Path.MOVETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.CLOSEPOLY,
    ]
    ax.add_patch(mpatches.PathPatch(Path(verts, codes), facecolor=colors[cat_from], edgecolor="none", alpha=0.4))

    from_offsets[(tp_from, cat_from)] += from_height
    to_offsets[(tp_to, cat_to)] += to_height

# Blocks with category and value labels
for (tp, cat), (y_start, height) in node_bounds.items():
    x = x_positions[tp]
    ax.add_patch(
        mpatches.Rectangle(
            (x - node_width / 2, y_start), node_width, height, facecolor=colors[cat], edgecolor=INK_SOFT, linewidth=0.8
        )
    )
    ax.text(
        x,
        y_start + height / 2,
        f"{cat}{' ' if height < 0.5 else chr(10)}({node_values[(tp, cat)]:g}K)",
        ha="center",
        va="center",
        fontsize=7,
        fontweight="bold",
        color=INK,
    )

# Column headers
for tp in time_points:
    ax.text(
        x_positions[tp], total_height + 0.8, tp, ha="center", va="bottom", fontsize=12, fontweight="bold", color=INK
    )

# Legend
legend_handles = [mpatches.Patch(color=colors[cat], label=cat) for cat in categories]
leg = ax.legend(
    handles=legend_handles,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.0),
    ncol=len(categories),
    fontsize=8,
    framealpha=0.95,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
x_values = list(x_positions.values())
ax.set_xlim(min(x_values) - 1.2, max(x_values) + 1.2)
ax.set_ylim(-1.0, total_height + 1.5)
title = f"Voter Migration {time_points[0]}-{time_points[-1]} · alluvial-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.axis("off")

fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
