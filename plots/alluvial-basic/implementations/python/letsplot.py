""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SNAPSHOT = "Snapshot"  # role: time_point
NEXT_SNAPSHOT = "Next snapshot"  # role: extra
PLAN = "Plan"  # role: category
NEXT_PLAN = "Next plan"  # role: extra
ACCOUNTS = "Accounts (thousands)"  # role: value
MOVED = "Accounts moved (thousands)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("plan_transitions.csv")
plans = ["Annual plan", "Monthly plan", "Free trial", "Inactive"]
moves_first = [[58, 3, 2, 2], [5, 54, 2, 2], [3, 2, 2, 1], [15, 12, 4, 64]]
moves_second = [[72, 4, 3, 2], [3, 63, 2, 3], [4, 3, 2, 1], [6, 8, 3, 52]]
rows = []
for (start, end), moves in [(("Jan 2024", "Jul 2024"), moves_first), (("Jul 2024", "Jan 2025"), moves_second)]:
    for i, source in enumerate(plans):
        for j, target in enumerate(plans):
            rows.append({SNAPSHOT: start, NEXT_SNAPSHOT: end, PLAN: source, NEXT_PLAN: target, MOVED: moves[i][j]})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
flows = df.dropna(subset=[SNAPSHOT, NEXT_SNAPSHOT, PLAN, NEXT_PLAN, MOVED])
snapshots = list(pd.unique(pd.concat([flows[SNAPSHOT], flows[NEXT_SNAPSHOT]]).astype(str)))
categories = list(pd.unique(pd.concat([flows[PLAN], flows[NEXT_PLAN]]).astype(str)))
rank = {name: k for k, name in enumerate(categories)}
colors = {name: IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)] for k, name in enumerate(categories)}

# Block heights: the larger of a block's incoming and outgoing totals, so both band stacks fit inside it
outgoing = flows.groupby([flows[SNAPSHOT].astype(str), flows[PLAN].astype(str)], sort=False)[MOVED].sum()
incoming = flows.groupby([flows[NEXT_SNAPSHOT].astype(str), flows[NEXT_PLAN].astype(str)], sort=False)[MOVED].sum()
outgoing.index.names = incoming.index.names = [SNAPSHOT, PLAN]
totals = pd.concat([outgoing, incoming], axis=1).max(axis=1)
nodes = totals.rename(ACCOUNTS).reset_index()
nodes = nodes.assign(order=nodes[PLAN].map(rank)).sort_values("order", kind="stable")

# Layout in a unit square: columns spread evenly, blocks stacked with a fixed gap
x_positions = dict(zip(snapshots, np.linspace(0.14, 0.86, len(snapshots)), strict=True))
node_width = 0.032
node_gap = 0.025
column_max = nodes.groupby(SNAPSHOT, sort=False)[ACCOUNTS].sum().max()
unit = (0.86 - node_gap * (len(categories) - 1)) / column_max

nodes["xmin"] = nodes[SNAPSHOT].map(x_positions) - node_width / 2
nodes["xmax"] = nodes[SNAPSHOT].map(x_positions) + node_width / 2
nodes["height"] = nodes[ACCOUNTS] * unit
nodes["ymax"] = 0.91 - nodes.groupby(SNAPSHOT, sort=False)["height"].cumsum() + nodes["height"]
nodes["ymax"] -= nodes.groupby(SNAPSHOT, sort=False).cumcount() * node_gap
nodes["ymin"] = nodes["ymax"] - nodes["height"]
block_top = nodes.set_index([SNAPSHOT, PLAN])["ymax"]

# Bands: stack each flow inside its source block by target order and inside its target block by source order
flows = flows.assign(
    src=flows[SNAPSHOT].astype(str),
    dst=flows[NEXT_SNAPSHOT].astype(str),
    src_cat=flows[PLAN].astype(str),
    dst_cat=flows[NEXT_PLAN].astype(str),
    width=flows[MOVED] * unit,
)
flows["src_rank"] = flows["src_cat"].map(rank)
flows["dst_rank"] = flows["dst_cat"].map(rank)
flows = flows.sort_values(["src", "src_rank", "dst_rank"], kind="stable")
flows["src_top"] = [block_top[key] for key in zip(flows["src"], flows["src_cat"], strict=True)]
flows["src_top"] -= flows.groupby(["src", "src_cat"], sort=False)["width"].cumsum() - flows["width"]
flows = flows.sort_values(["dst", "dst_rank", "src_rank"], kind="stable")
flows["dst_top"] = [block_top[key] for key in zip(flows["dst"], flows["dst_cat"], strict=True)]
flows["dst_top"] -= flows.groupby(["dst", "dst_cat"], sort=False)["width"].cumsum() - flows["width"]

t = np.linspace(0, 1, 41)
ease = t * t * (3 - 2 * t)
band_parts = []
for band_id, flow in enumerate(flows.itertuples(index=False)):
    x_left = x_positions[flow.src] + node_width / 2
    x_right = x_positions[flow.dst] - node_width / 2
    xs = x_left + t * (x_right - x_left)
    top = flow.src_top + ease * (flow.dst_top - flow.src_top)
    band_parts.append(
        pd.DataFrame(
            {
                "x": np.concatenate([xs, xs[::-1]]),
                "y": np.concatenate([top, (top - flow.width)[::-1]]),
                "band": band_id,
                PLAN: flow.dst_cat,
            }
        )
    )
bands = pd.concat(band_parts, ignore_index=True)

# Labels at every block: left of the first column, right of every other column
nodes["label"] = nodes[PLAN] + " · " + nodes[ACCOUNTS].map(lambda v: f"{v:,.0f}k")
nodes["label_y"] = (nodes["ymin"] + nodes["ymax"]) / 2
first = nodes[nodes[SNAPSHOT] == snapshots[0]].assign(label_x=lambda d: d["xmin"] - 0.012)
others = nodes[nodes[SNAPSHOT] != snapshots[0]].assign(label_x=lambda d: d["xmax"] + 0.008)
headers = pd.DataFrame({"x": list(x_positions.values()), "y": 0.975, "label": snapshots})

title = "alluvial-basic · python · letsplot · anyplot.ai"
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="band", fill=PLAN), data=bands, alpha=0.55, color=PAGE_BG, size=0.15)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill=PLAN), data=nodes, color=INK_SOFT, size=0.4
    )
    + geom_text(aes(x="x", y="y", label="label"), data=headers, size=6, fontface="bold", color=INK)
    + geom_text(aes(x="label_x", y="label_y", label="label"), data=first, size=4, hjust=1, color=INK_SOFT)
    + geom_label(
        aes(x="label_x", y="label_y", label="label"),
        data=others,
        size=4,
        hjust=0,
        color=INK_SOFT,
        fill=PAGE_BG,
        alpha=0.85,
        label_size=0,
        label_padding=0.15,
    )
    + scale_fill_manual(values=colors)
    + scale_x_continuous(limits=[0, 1], expand=[0, 0])
    + scale_y_continuous(limits=[0, 1], expand=[0, 0])
    + labs(title=title)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=round(16 * min(1.0, 67 / len(title))), face="bold", color=INK),
        axis_title=element_blank(),
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
