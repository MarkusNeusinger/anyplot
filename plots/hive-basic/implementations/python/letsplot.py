"""anyplot.ai
hive-basic: Basic Hive Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_size,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
R_MIN, R_MAX = 0.3, 0.95  # radial span of the nodes on each axis, as a share of the axis length
AXIS_START, AXIS_END = 0.2, 1.0  # radial span of the drawn axis lines
CURVE_PULL = 0.15  # Bezier control point sits this share of the way from the center to the endpoints' sum

# Columns: set these to your table's column names
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: extra
SOURCE_TYPE = "Source type"  # role: axis_attribute
TARGET_TYPE = "Target type"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("dependencies.csv")
# Each row is one edge with the axis group of both of its end nodes; the degree is counted from the edges.
module_info = {
    "core_main": "Core",
    "core_data": "Core",
    "core_config": "Core",
    "core_logger": "Core",
    "core_cache": "Core",
    "util_parser": "Utility",
    "util_validator": "Utility",
    "util_formatter": "Utility",
    "util_crypto": "Utility",
    "util_compress": "Utility",
    "util_encode": "Utility",
    "api_rest": "Interface",
    "api_graphql": "Interface",
    "api_websocket": "Interface",
    "api_grpc": "Interface",
}
edge_pairs = [
    ("core_main", "core_data"),
    ("core_main", "core_config"),
    ("core_main", "core_logger"),
    ("core_data", "core_cache"),
    ("core_config", "core_logger"),
    ("util_parser", "core_data"),
    ("util_validator", "core_config"),
    ("util_formatter", "core_logger"),
    ("util_crypto", "core_main"),
    ("util_compress", "core_cache"),
    ("util_encode", "util_parser"),
    ("util_validator", "util_formatter"),
    ("api_rest", "core_main"),
    ("api_rest", "util_parser"),
    ("api_rest", "util_validator"),
    ("api_graphql", "core_data"),
    ("api_graphql", "util_parser"),
    ("api_websocket", "core_main"),
    ("api_websocket", "util_formatter"),
    ("api_grpc", "core_config"),
    ("api_grpc", "util_crypto"),
    ("api_rest", "api_graphql"),
    ("util_formatter", "util_encode"),
]
df = pd.DataFrame(
    {
        SOURCE: [s for s, _ in edge_pairs],
        TARGET: [t for _, t in edge_pairs],
        SOURCE_TYPE: [module_info[s] for s, _ in edge_pairs],
        TARGET_TYPE: [module_info[t] for _, t in edge_pairs],
    }
)

# Plot: axis angles are fixed by group order, node distance from the center is fixed by degree
nodes = pd.concat(
    [
        df[[SOURCE, SOURCE_TYPE]].set_axis(["module", "group"], axis=1),
        df[[TARGET, TARGET_TYPE]].set_axis(["module", "group"], axis=1),
    ]
).drop_duplicates("module")
nodes["degree"] = nodes["module"].map(pd.concat([df[SOURCE], df[TARGET]]).value_counts())
groups = list(dict.fromkeys(nodes["group"]))
angles = {g: i * 2 * np.pi / len(groups) for i, g in enumerate(groups)}
# Distance from the center: rank by degree within each axis, ties in name order, so equal degrees do not stack
nodes = nodes.sort_values(["degree", "module"])
rank = nodes.groupby("group").cumcount()
rank_span = (rank.max()) or 1

nodes["radius"] = R_MIN + (R_MAX - R_MIN) * rank / rank_span
nodes["x"] = nodes["radius"] * np.cos(nodes["group"].map(angles))
nodes["y"] = nodes["radius"] * np.sin(nodes["group"].map(angles))
lookup = nodes.set_index("module")

# Edges as quadratic Bezier curves pulled toward the center
t = np.linspace(0, 1, 24)
curves = []
for source, target in zip(df[SOURCE], df[TARGET], strict=True):
    sx, sy = lookup.loc[source, ["x", "y"]]
    tx, ty = lookup.loc[target, ["x", "y"]]
    cx, cy = (sx + tx) * CURVE_PULL, (sy + ty) * CURVE_PULL
    curves.append(
        pd.DataFrame(
            {
                "x": (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t**2 * tx,
                "y": (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t**2 * ty,
                "edge": f"{source}-{target}",
            }
        )
    )
edges = pd.concat(curves, ignore_index=True)

axis_lines = pd.concat(
    [
        pd.DataFrame(
            {
                "x": np.array([AXIS_START, AXIS_END]) * np.cos(a),
                "y": np.array([AXIS_START, AXIS_END]) * np.sin(a),
                "group": g,
            }
        )
        for g, a in angles.items()
    ],
    ignore_index=True,
)
labels = pd.DataFrame(
    {
        "x": [1.1 * np.cos(a) for a in angles.values()],
        "y": [1.1 * np.sin(a) for a in angles.values()],
        "label": list(angles),
    }
)

reach = 1.35

plot = (
    ggplot()
    + geom_path(aes(x="x", y="y", group="group"), data=axis_lines, color=INK_SOFT, size=0.8, alpha=0.5)
    + geom_path(aes(x="x", y="y", group="edge"), data=edges, color=INK_SOFT, size=0.5, alpha=0.5)
    + geom_point(
        aes(x="x", y="y", fill="group", size="degree"), data=nodes, color=INK_SOFT, stroke=0.6, shape=21, alpha=0.9
    )
    + geom_text(aes(x="x", y="y", label="label"), data=labels, size=7, fontface="bold", color=INK, show_legend=False)
    + scale_fill_manual(values=IMPRINT_PALETTE, breaks=groups)
    + scale_size(range=[3, 8])
    + guides(size=guide_legend(override_aes={"fill": INK_SOFT}))
    + coord_fixed(ratio=1, xlim=(-reach, reach), ylim=(-reach, reach))
    + labs(
        title="hive-basic · python · letsplot · anyplot.ai",
        fill="Module type",
        size="Connections (node size)",
        caption="Distance from the center: rank by connections within each axis",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_caption=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[20, 20, 20, 20],
    )
)
# The one-panel grid paints the whole square canvas; the plot keeps its equal axes
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
