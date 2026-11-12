""" anyplot.ai
hive-basic: Basic Hive Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-12
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
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
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
SOURCE_DEGREE = "Source connections"  # role: extra
TARGET_DEGREE = "Target connections"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("dependencies.csv")
# Each row is one edge with the axis group and degree of both of its end nodes.
module_info = {
    "core_main": ("Core", 8),
    "core_data": ("Core", 6),
    "core_config": ("Core", 5),
    "core_logger": ("Core", 4),
    "core_cache": ("Core", 3),
    "util_parser": ("Utility", 5),
    "util_validator": ("Utility", 4),
    "util_formatter": ("Utility", 6),
    "util_crypto": ("Utility", 3),
    "util_compress": ("Utility", 2),
    "util_encode": ("Utility", 7),
    "api_rest": ("Interface", 7),
    "api_graphql": ("Interface", 5),
    "api_websocket": ("Interface", 4),
    "api_grpc": ("Interface", 3),
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
        SOURCE_TYPE: [module_info[s][0] for s, _ in edge_pairs],
        TARGET_TYPE: [module_info[t][0] for _, t in edge_pairs],
        SOURCE_DEGREE: [module_info[s][1] for s, _ in edge_pairs],
        TARGET_DEGREE: [module_info[t][1] for _, t in edge_pairs],
    }
)

# Plot: axis angles are fixed by group order, node distance from the center is fixed by degree
nodes = pd.concat(
    [
        df[[SOURCE, SOURCE_TYPE, SOURCE_DEGREE]].set_axis(["module", "group", "degree"], axis=1),
        df[[TARGET, TARGET_TYPE, TARGET_DEGREE]].set_axis(["module", "group", "degree"], axis=1),
    ]
).drop_duplicates("module")
groups = list(dict.fromkeys(nodes["group"]))
angles = {g: i * 2 * np.pi / len(groups) for i, g in enumerate(groups)}
degree_span = (nodes["degree"].max() - nodes["degree"].min()) or 1

nodes["radius"] = R_MIN + (R_MAX - R_MIN) * (nodes["degree"] - nodes["degree"].min()) / degree_span
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
    same_group = lookup.loc[source, "group"] == lookup.loc[target, "group"]
    curves.append(
        pd.DataFrame(
            {
                "x": (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t**2 * tx,
                "y": (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t**2 * ty,
                "edge": f"{source}-{target}",
                "Edge type": f"Within {lookup.loc[source, 'group']}" if same_group else "Between axes",
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
        "x": [1.22 * np.cos(a) for a in angles.values()],
        "y": [1.22 * np.sin(a) for a in angles.values()],
        "label": list(angles),
    }
)

edge_colors = {f"Within {g}": IMPRINT_PALETTE[i] for i, g in enumerate(groups)}
edge_colors["Between axes"] = INK_SOFT
reach = 1.45

plot = (
    ggplot()
    + geom_path(aes(x="x", y="y", group="group"), data=axis_lines, color=INK_SOFT, size=0.8, alpha=0.5)
    + geom_path(aes(x="x", y="y", group="edge", color="Edge type"), data=edges, size=0.5, alpha=0.5)
    + geom_point(
        aes(x="x", y="y", fill="group", size="degree"), data=nodes, color=INK_SOFT, stroke=0.6, shape=21, alpha=0.9
    )
    + geom_text(aes(x="x", y="y", label="label"), data=labels, size=7, fontface="bold", color=INK, show_legend=False)
    + scale_fill_manual(values=IMPRINT_PALETTE, breaks=groups)
    + scale_color_manual(values=edge_colors)
    + scale_size(range=[3, 7])
    + coord_fixed(ratio=1, xlim=(-reach, reach), ylim=(-reach, reach))
    + labs(
        title="hive-basic · python · letsplot · anyplot.ai",
        fill="Module type",
        size="Connections (distance from center)",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[20, 20, 20, 20],
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")
