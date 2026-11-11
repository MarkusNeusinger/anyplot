"""anyplot.ai
hive-basic: Basic Hive Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-07
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Apply seaborn theme with theme-adaptive colors
sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
NODE = "Module"  # role: nodes
GROUP = "Module type"  # role: axis_attribute
DEGREE = "Degree (connections)"  # role: extra
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: extra

# Data: replace this block with your own tables, for example df = pd.read_csv("edges.csv")
# df is the edge list; nodes holds one row per module with its axis group and degree.
rng = np.random.default_rng(42)
nodes = pd.DataFrame(
    {
        NODE: [f"M{i}" for i in range(30)],
        GROUP: ["core"] * 10 + ["utility"] * 10 + ["interface"] * 10,
        DEGREE: rng.integers(1, 15, 30),
    }
)
df = pd.DataFrame(
    [
        # Core to utility connections
        ("M0", "M10"),
        ("M0", "M11"),
        ("M1", "M12"),
        ("M2", "M13"),
        ("M3", "M14"),
        ("M4", "M15"),
        ("M5", "M16"),
        ("M6", "M17"),
        ("M7", "M18"),
        ("M8", "M19"),
        # Utility to interface connections
        ("M10", "M20"),
        ("M11", "M21"),
        ("M12", "M22"),
        ("M13", "M23"),
        ("M14", "M24"),
        ("M15", "M25"),
        ("M16", "M26"),
        ("M17", "M27"),
        ("M18", "M28"),
        ("M19", "M29"),
        # Core to interface connections (direct)
        ("M0", "M20"),
        ("M1", "M23"),
        ("M3", "M25"),
        ("M5", "M27"),
        ("M9", "M29"),
        # Internal connections
        ("M0", "M1"),
        ("M2", "M3"),
        ("M10", "M11"),
        ("M20", "M21"),
    ],
    columns=[SOURCE, TARGET],
)

# Plot: reads only df, nodes and the constants above
groups = list(dict.fromkeys(nodes[GROUP]))
n_groups = len(groups)
axis_angles = {g: np.pi / 2 + 2 * np.pi * i / n_groups for i, g in enumerate(groups)}
axis_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

# Position along each axis: degree scaled within its group
nodes = nodes.copy()
group_min = nodes.groupby(GROUP)[DEGREE].transform("min")
group_span = (nodes.groupby(GROUP)[DEGREE].transform("max") - group_min).replace(0, np.nan)
nodes["radius"] = (0.3 + 0.7 * (nodes[DEGREE] - group_min) / group_span).fillna(0.65)
nodes["angle"] = nodes[GROUP].map(axis_angles)
nodes["x"] = nodes["radius"] * np.cos(nodes["angle"])
nodes["y"] = nodes["radius"] * np.sin(nodes["angle"])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Radial axes with group labels
for group, angle in axis_angles.items():
    ax.plot([0, 1.1 * np.cos(angle)], [0, 1.1 * np.sin(angle)], color=INK_SOFT, linewidth=1.2, alpha=0.3, zorder=1)
    ax.text(
        1.25 * np.cos(angle),
        1.25 * np.sin(angle),
        group.upper(),
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        color=axis_colors[group],
    )

# Edges as quadratic Bezier curves pulled toward the center
node_pos = nodes.set_index(NODE)[["x", "y"]]
t = np.linspace(0, 1, 50)
curves = []
for edge_id, (source, target) in enumerate(zip(df[SOURCE], df[TARGET], strict=True)):
    src_x, src_y = node_pos.loc[source]
    tgt_x, tgt_y = node_pos.loc[target]
    ctrl_x, ctrl_y = 0.1 * (src_x + tgt_x), 0.1 * (src_y + tgt_y)
    curves.append(
        pd.DataFrame(
            {
                "edge_id": edge_id,
                "x": (1 - t) ** 2 * src_x + 2 * (1 - t) * t * ctrl_x + t**2 * tgt_x,
                "y": (1 - t) ** 2 * src_y + 2 * (1 - t) * t * ctrl_y + t**2 * tgt_y,
            }
        )
    )
edge_curves = pd.concat(curves, ignore_index=True)

sns.lineplot(
    data=edge_curves,
    x="x",
    y="y",
    units="edge_id",
    estimator=None,
    color=INK_SOFT,
    alpha=0.25,
    linewidth=0.9,
    legend=False,
    ax=ax,
    zorder=2,
)

# Nodes on their group's axis
sns.scatterplot(
    data=nodes,
    x="x",
    y="y",
    hue=GROUP,
    hue_order=groups,
    palette=[axis_colors[g] for g in groups],
    s=130,
    alpha=0.9,
    edgecolor=PAGE_BG,
    linewidth=1,
    ax=ax,
    legend=False,
    zorder=3,
)

# Legend names the groups; its title names the position encoding
legend_handles = [mpatches.Patch(color=axis_colors[g], label=f"{g.title()} Modules") for g in groups]
ax.legend(
    handles=legend_handles,
    title=f"Distance from center = {DEGREE.lower()}",
    loc="lower center",
    fontsize=8,
    title_fontsize=8,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

# Style
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("hive-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.93)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
