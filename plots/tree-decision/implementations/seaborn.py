""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, RegularPolygon


# Style
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")

# Decision tree data (two-stage investment decision)
# Structure: id, type, parent, branch_label, probability, payoff, emv, pruned, x, y
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

# Colors
decision_color = "#306998"
chance_color = "#E8833A"
terminal_pos_color = "#2ecc71"
terminal_neg_color = "#e74c3c"
pruned_alpha = 0.35
normal_alpha = 1.0

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

node_size_decision = 0.50
node_size_chance = 0.45
node_size_terminal = 0.35

# Draw branches first (behind nodes)
for node in tree:
    if node["parent"] is None:
        continue
    parent = node_map[node["parent"]]
    px, py = parent["x"], parent["y"]
    nx, ny = node["x"], node["y"]
    alpha = pruned_alpha if node["pruned"] else normal_alpha
    linestyle = "--" if node["pruned"] else "-"
    linewidth = 2.5 if not node["pruned"] else 1.8

    # Draw right-angle branch: horizontal then vertical
    mid_x = px + (nx - px) * 0.4
    ax.plot(
        [px, mid_x, nx],
        [py, ny, ny],
        color="#555555",
        linewidth=linewidth,
        alpha=alpha,
        linestyle=linestyle,
        solid_capstyle="round",
        zorder=1,
    )

    # Branch label
    label_x = (px + mid_x) / 2 + 0.15
    label_y = (py + ny) / 2
    branch_text = node["label"]
    if node["prob"] is not None:
        branch_text = f"{node['label']}\n(p={node['prob']:.1f})"
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

    # Pruned mark
    if node["pruned"]:
        mark_x = mid_x - 0.15
        mark_y = ny
        ax.plot(
            [mark_x - 0.12, mark_x + 0.12],
            [mark_y - 0.18, mark_y + 0.18],
            color="#c0392b",
            linewidth=2.5,
            alpha=0.7,
            zorder=5,
        )
        ax.plot(
            [mark_x - 0.12, mark_x + 0.12],
            [mark_y + 0.18, mark_y - 0.18],
            color="#c0392b",
            linewidth=2.5,
            alpha=0.7,
            zorder=5,
        )

# Draw nodes
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
        emv_text = f"EMV\n${node['emv']}K"
        ax.text(
            nx,
            ny,
            emv_text,
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
        emv_text = f"EMV\n${node['emv']}K"
        ax.text(
            nx,
            ny,
            emv_text,
            fontsize=13,
            fontweight="bold",
            ha="center",
            va="center",
            color="white",
            alpha=alpha,
            zorder=4,
        )

    elif node["type"] == "terminal":
        payoff = node["payoff"]
        color = terminal_pos_color if payoff >= 0 else terminal_neg_color
        triangle = RegularPolygon(
            (nx, ny),
            numVertices=3,
            radius=node_size_terminal,
            orientation=0,
            facecolor=color,
            edgecolor="white",
            linewidth=2.5,
            alpha=alpha,
            zorder=3,
        )
        ax.add_patch(triangle)
        sign = "+" if payoff >= 0 else ""
        ax.text(
            nx + 0.65,
            ny,
            f"${sign}{payoff}K",
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
    plt.Line2D([0], [0], color="#555", linestyle="--", linewidth=2, alpha=0.5, label="Pruned Branch"),
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
