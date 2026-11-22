""" anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per node type in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Apply seaborn theme
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Columns: set these to your table's column names
NODE = "Name"  # role: nodes
PARENT = "Parent"  # role: edges
LEVEL = "Depth level"  # role: level
KIND = "Entry type"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("tree.csv")
# One row per node; the parent column holds the parent's name (missing for the root).
df = pd.DataFrame(
    [
        ("project/", None, 0, "directory"),
        ("src/", "project/", 1, "directory"),
        ("config/", "project/", 1, "directory"),
        ("tests/", "project/", 1, "directory"),
        ("docs/", "project/", 1, "directory"),
        ("build/", "project/", 1, "directory"),
        ("components/", "src/", 2, "directory"),
        ("utils/", "src/", 2, "directory"),
        ("models/", "src/", 2, "directory"),
        ("settings.yaml", "config/", 2, "file"),
        ("env.json", "config/", 2, "file"),
        ("unit/", "tests/", 2, "directory"),
        ("integration/", "tests/", 2, "directory"),
        ("api/", "docs/", 2, "directory"),
        ("guide.md", "docs/", 2, "file"),
        ("button.py", "components/", 3, "file"),
        ("input.py", "components/", 3, "file"),
        ("form.py", "components/", 3, "file"),
        ("helpers.py", "utils/", 3, "file"),
        ("validators.py", "utils/", 3, "file"),
        ("user.py", "models/", 3, "file"),
        ("data.py", "models/", 3, "file"),
    ],
    columns=[NODE, PARENT, LEVEL, KIND],
)

# Plot: reads only df and the constants above
# Layout: one row per level, nodes spread evenly and centered within the row
Y_SPACING = 2.0
X_PER_NODE = 1.5
MIN_SPREAD = 6.0

pos_x = pd.Series(0.0, index=df.index)
for _, row_index in df.groupby(LEVEL, sort=True).groups.items():
    n = len(row_index)
    spread = max(n * X_PER_NODE, MIN_SPREAD)
    pos_x[row_index] = np.linspace(-spread / 2, spread / 2, n) if n > 1 else 0.0
df["x"] = pos_x
df["y"] = -df[LEVEL] * Y_SPACING

# Node size shrinks with depth
df["size"] = np.interp(df[LEVEL], [df[LEVEL].min(), df[LEVEL].max()], [300, 115])

kinds = list(df[KIND].unique())
kind_colors = {kind: IMPRINT_PALETTE[i] for i, kind in enumerate(kinds)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges first (underneath nodes): each node connects to its parent
coords = df.set_index(NODE)[["x", "y"]]
for name, parent in zip(df[NODE], df[PARENT], strict=True):
    if pd.isna(parent):
        continue
    x0, y0 = coords.loc[parent]
    x1, y1 = coords.loc[name]
    ax.plot([x0, x1], [y0, y1], color=INK_SOFT, linewidth=1.0, alpha=0.4, zorder=1)

# Nodes: color by entry type, size by depth
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue=KIND,
    palette=kind_colors,
    s=df["size"].to_numpy(),
    edgecolor=INK_SOFT,
    linewidth=1.0,
    alpha=0.85,
    legend=False,
    zorder=2,
    ax=ax,
)

# Node labels sit just below their node; the root is larger and bold
max_level = df[LEVEL].max()
for name, x, y, level in zip(df[NODE], df["x"], df["y"], df[LEVEL], strict=True):
    is_root = level == df[LEVEL].min()
    ax.annotate(
        name,
        (x, y),
        textcoords="offset points",
        xytext=(0, -14),
        ha="center",
        va="top",
        fontsize=9 if is_root else 8 if level == 1 else 7 if level < max_level else 6.5,
        fontweight="bold" if is_root else "normal",
        color=INK,
    )

# Style
ax.set_title("network-hierarchical · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10)
ax.set_xlabel("Directory/File Distribution", fontsize=10)
ax.set_ylabel("Directory Depth (Level)", fontsize=10)
ax.set_xticks([])
ax.set_yticks([])

x_padding = 1.5
y_padding = 1.0
ax.set_xlim(df["x"].min() - x_padding, df["x"].max() + x_padding)
ax.set_ylim(df["y"].min() - y_padding, df["y"].max() + y_padding)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(False)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
