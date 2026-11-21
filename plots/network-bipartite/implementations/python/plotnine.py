"""anyplot.ai
network-bipartite: Bipartite Network Graph
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_size_continuous,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per node set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AIRLINE = "Airline"  # role: source
AIRPORT = "Airport"  # role: target

# Data: replace this block with your own edge list, for example df = pd.read_csv("routes.csv")
routes = {
    "Delta": ["ATL", "JFK", "LAX", "SEA", "BOS", "MIA"],
    "United": ["ORD", "DEN", "SFO", "LAX", "JFK", "FRA"],
    "American": ["DFW", "ORD", "MIA", "JFK", "LAX"],
    "Southwest": ["DEN", "LAX", "ORD", "ATL"],
    "JetBlue": ["JFK", "BOS", "MIA"],
    "Alaska": ["SEA", "SFO", "LAX"],
    "Lufthansa": ["FRA", "JFK", "ORD", "SFO"],
    "Emirates": ["DXB", "JFK", "LAX"],
}
df = pd.DataFrame(
    [(airline, airport) for airline, airports in routes.items() for airport in airports], columns=[AIRLINE, AIRPORT]
)

# Plot: reads only df and the constants above
sources = df[AIRLINE].unique().tolist()
targets = df[AIRPORT].unique().tolist()
node_sets = [AIRLINE, AIRPORT]

# Layout: one column per set, first node of each set at the top
source_nodes = pd.DataFrame(
    {
        "label": sources,
        "x": 0.0,
        "y": np.linspace(1, 0, len(sources)),
        "node_set": AIRLINE,
        "degree": df[AIRLINE].value_counts().reindex(sources).to_numpy(),
    }
)
target_nodes = pd.DataFrame(
    {
        "label": targets,
        "x": 1.0,
        "y": np.linspace(1, 0, len(targets)),
        "node_set": AIRPORT,
        "degree": df[AIRPORT].value_counts().reindex(targets).to_numpy(),
    }
)
nodes = pd.concat([source_nodes, target_nodes], ignore_index=True)

src_pos = source_nodes.set_index("label")["y"]
tgt_pos = target_nodes.set_index("label")["y"]
edges = pd.DataFrame({"x": 0.0, "y": df[AIRLINE].map(src_pos), "xend": 1.0, "yend": df[AIRPORT].map(tgt_pos)})

title = "network-bipartite · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=edges, color=INK_SOFT, alpha=0.35, size=0.4)
    + geom_point(aes(x="x", y="y", color="node_set", size="degree"), data=nodes)
    + geom_text(
        aes(x="x", y="y", label="label", color="node_set"),
        data=source_nodes,
        ha="right",
        nudge_x=-0.06,
        size=11,
        show_legend=False,
    )
    + geom_text(
        aes(x="x", y="y", label="label", color="node_set"),
        data=target_nodes,
        ha="left",
        nudge_x=0.07,
        size=11,
        show_legend=False,
    )
    + scale_color_manual(values=IMPRINT_PALETTE, limits=node_sets, name="Node set")
    + scale_size_continuous(range=(3, 9), name="Routes")
    + guides(size=guide_legend(override_aes={"color": INK_SOFT}))
    + scale_x_continuous(limits=(-0.5, 1.5), breaks=[0, 1], labels=node_sets)
    + scale_y_continuous(limits=(-0.06, 1.06))
    + labs(title=title, x="", y="")
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text_x=element_text(color=INK, size=11, face="bold"),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_ticks_minor_y=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(color=INK_SOFT, size=9),
        legend_title=element_text(color=INK, size=9),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
