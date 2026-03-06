"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-06
"""

import math

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, RegularPolygon


# Style
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")

# Colorblind-safe palette via seaborn
cb_palette = sns.color_palette("colorblind", 6)
decision_color = "#306998"  # Python Blue for decision nodes
chance_color = cb_palette[1]  # orange from colorblind palette
terminal_pos_color = cb_palette[0]  # blue for positive payoffs
terminal_neg_color = cb_palette[5]  # brown/dark for negative payoffs
branch_color = "#555555"
prune_mark_color = cb_palette[3]  # red-ish from colorblind palette

pruned_alpha = 0.35
normal_alpha = 1.0

# Decision tree data (two-stage investment decision)
tree = [
    {
        "id": "D1",
        "type": "decision",
        "parent": None,
        "label": "",
        "prob": None,
        "payoff": None,
        "emv": 130,
        "pruned": False,
        "x": 1.0,
        "y": 4.5,
    },
    {
        "id": "C1",
        "type": "chance",
        "parent": "D1",
        "label": "Invest",
        "prob": None,
        "payoff": None,
        "emv": 130,
        "pruned": False,
        "x": 5.5,
        "y": 7.0,
    },
    {
        "id": "C2",
        "type": "chance",
        "parent": "D1",
        "label": "Partner",
        "prob": None,
        "payoff": None,
        "emv": 80,
        "pruned": True,
        "x": 5.5,
        "y": 2.0,
    },
    {
        "id": "T1",
        "type": "terminal",
        "parent": "C1",
        "label": "High Demand",
        "prob": 0.6,
        "payoff": 300,
        "emv": None,
        "pruned": False,
        "x": 11.0,
        "y": 8.2,
    },
    {
        "id": "T2",
        "type": "terminal",
        "parent": "C1",
        "label": "Low Demand",
        "prob": 0.4,
        "payoff": -125,
        "emv": None,
        "pruned": False,
        "x": 11.0,
        "y": 5.8,
    },
    {
        "id": "T3",
        "type": "terminal",
        "parent": "C2",
        "label": "High Demand",
        "prob": 0.6,
        "payoff": 150,
        "emv": None,
        "pruned": True,
        "x": 11.0,
        "y": 3.2,
    },
    {
        "id": "T4",
        "type": "terminal",
        "parent": "C2",
        "label": "Low Demand",
        "prob": 0.4,
        "payoff": -25,
        "emv": None,
        "pruned": True,
        "x": 11.0,
        "y": 0.8,
    },
]

node_map = {n["id"]: n for n in tree}

# Build DataFrames for seaborn plotting
branch_rows = []
for node in tree:
    if node["parent"] is None:
        continue
    parent = node_map[node["parent"]]
    px, py = parent["x"], parent["y"]
    nx, ny = node["x"], node["y"]
    mid_x = px + (nx - px) * 0.4
    seg_id = f"{parent['id']}-{node['id']}"
    style = "pruned" if node["pruned"] else "optimal"
    # Segment 1: horizontal from parent to mid, then down/up to child y
    branch_rows.append({"seg": seg_id, "x": px, "y": py, "style": style})
    branch_rows.append({"seg": seg_id, "x": mid_x, "y": ny, "style": style})
    branch_rows.append({"seg": seg_id, "x": nx, "y": ny, "style": style})

branch_df = pd.DataFrame(branch_rows)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw branches using seaborn lineplot with DataFrame
for style, group_df in branch_df.groupby("style"):
    alpha = pruned_alpha if style == "pruned" else normal_alpha
    lw = 1.8 if style == "pruned" else 2.5
    ls = "--" if style == "pruned" else "-"
    for _seg_id, seg_df in group_df.groupby("seg"):
        sns.lineplot(
            data=seg_df,
            x="x",
            y="y",
            color=branch_color,
            linewidth=lw,
            alpha=alpha,
            linestyle=ls,
            sort=False,
            ax=ax,
            legend=False,
        )

# Branch labels and pruned marks
for node in tree:
    if node["parent"] is None:
        continue
    parent = node_map[node["parent"]]
    px, py = parent["x"], parent["y"]
    nx, ny = node["x"], node["y"]
    alpha = pruned_alpha if node["pruned"] else normal_alpha
    mid_x = px + (nx - px) * 0.4

    branch_text = node["label"]
    if node["prob"] is not None:
        branch_text = f"{node['label']}\n(p={node['prob']:.1f})"
    label_x = (px + mid_x) / 2 + 0.15
    label_y = (py + ny) / 2
    ax.text(
        label_x,
        label_y,
        branch_text,
        fontsize=13,
        fontweight="bold",
        ha="center",
        va="center",
        alpha=alpha,
        color="#333333",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.8 * alpha},
    )

    # Pruned mark (X)
    if node["pruned"]:
        mark_x = mid_x - 0.15
        mark_y = ny
        ax.plot(
            [mark_x - 0.12, mark_x + 0.12],
            [mark_y - 0.18, mark_y + 0.18],
            color=prune_mark_color,
            linewidth=2.5,
            alpha=0.7,
            zorder=5,
        )
        ax.plot(
            [mark_x - 0.12, mark_x + 0.12],
            [mark_y + 0.18, mark_y - 0.18],
            color=prune_mark_color,
            linewidth=2.5,
            alpha=0.7,
            zorder=5,
        )

# Build node DataFrame for seaborn scatterplot (terminal nodes)
terminal_rows = []
for node in tree:
    if node["type"] == "terminal":
        payoff = node["payoff"]
        terminal_rows.append(
            {
                "x": node["x"],
                "y": node["y"],
                "payoff_type": "Positive" if payoff >= 0 else "Negative",
                "pruned": node["pruned"],
                "payoff": payoff,
            }
        )

terminal_df = pd.DataFrame(terminal_rows)

# Draw decision and chance nodes (these need custom patches)
node_size_decision = 0.50
node_size_chance = 0.45

for node in tree:
    nx, ny = node["x"], node["y"]
    alpha = pruned_alpha if node["pruned"] else normal_alpha

    if node["type"] == "decision":
        rect = FancyBboxPatch(
            (nx - node_size_decision, ny - node_size_decision),
            node_size_decision * 2,
            node_size_decision * 2,
            boxstyle="square,pad=0",
            facecolor=decision_color,
            edgecolor="white",
            linewidth=3,
            alpha=alpha,
            zorder=3,
        )
        ax.add_patch(rect)
        ax.text(
            nx,
            ny,
            f"EMV\n${node['emv']}K",
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="center",
            color="white",
            alpha=alpha,
            zorder=4,
        )

    elif node["type"] == "chance":
        circle = plt.Circle(
            (nx, ny), node_size_chance, facecolor=chance_color, edgecolor="white", linewidth=3, alpha=alpha, zorder=3
        )
        ax.add_patch(circle)
        # Offset EMV text above node for pruned nodes to avoid overlap with X marks
        if node["pruned"]:
            ax.text(
                nx,
                ny + 0.65,
                f"EMV ${node['emv']}K",
                fontsize=13,
                fontweight="bold",
                ha="center",
                va="bottom",
                color=chance_color,
                alpha=max(alpha, 0.6),
                zorder=4,
            )
        else:
            ax.text(
                nx,
                ny,
                f"EMV\n${node['emv']}K",
                fontsize=13,
                fontweight="bold",
                ha="center",
                va="center",
                color="white",
                alpha=alpha,
                zorder=4,
            )

# Draw terminal nodes using seaborn scatterplot for positive/negative payoffs
palette_map = {"Positive": terminal_pos_color, "Negative": terminal_neg_color}

# Use sns.scatterplot for terminal node markers
for payoff_type, sub_df in terminal_df.groupby("payoff_type"):
    color = palette_map[payoff_type]
    for _, row in sub_df.iterrows():
        alpha = pruned_alpha if row["pruned"] else normal_alpha
        # Right-pointing triangle: orientation = -pi/2
        triangle = RegularPolygon(
            (row["x"], row["y"]),
            numVertices=3,
            radius=0.35,
            orientation=-math.pi / 2,
            facecolor=color,
            edgecolor="white",
            linewidth=2.5,
            alpha=alpha,
            zorder=3,
        )
        ax.add_patch(triangle)
        sign = "+" if row["payoff"] >= 0 else ""
        ax.text(
            row["x"] + 0.65,
            row["y"],
            f"${sign}{row['payoff']}K",
            fontsize=15,
            fontweight="bold",
            ha="left",
            va="center",
            color=color,
            alpha=alpha,
            zorder=4,
        )

# Legend
legend_elements = [
    mpatches.Patch(facecolor=decision_color, edgecolor="white", label="Decision Node"),
    mpatches.Patch(facecolor=chance_color, edgecolor="white", label="Chance Node"),
    mpatches.Patch(facecolor=terminal_pos_color, edgecolor="white", label="Positive Payoff"),
    mpatches.Patch(facecolor=terminal_neg_color, edgecolor="white", label="Negative Payoff"),
    plt.Line2D([0], [0], color=branch_color, linestyle="--", linewidth=2, alpha=0.5, label="Pruned Branch"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=13, framealpha=0.9, edgecolor="#cccccc", fancybox=True)

# Title and styling
ax.set_title("tree-decision \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlim(-0.5, 14.5)
ax.set_ylim(-0.5, 9.5)
ax.axis("off")
sns.despine(left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
