""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Style using seaborn's consolidated theme API
sns.set_theme(context="talk", style="white", font_scale=1.2, palette="colorblind")

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
        "y": 5.0,
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
        "y": 7.5,
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
        "y": 9.0,
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
        "y": 6.0,
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
        "y": 3.5,
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
        "y": 0.5,
    },
]

node_map = {n["id"]: n for n in tree}

# Build branch DataFrame for seaborn lineplot with units parameter
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
    branch_rows.append({"seg": seg_id, "x": px, "y": py, "style": style})
    branch_rows.append({"seg": seg_id, "x": mid_x, "y": ny, "style": style})
    branch_rows.append({"seg": seg_id, "x": nx, "y": ny, "style": style})

branch_df = pd.DataFrame(branch_rows)

# Build node DataFrame for seaborn scatterplot with hue/style mapping
node_rows = []
for node in tree:
    if node["type"] == "decision":
        category = "Decision"
    elif node["type"] == "chance":
        category = "Chance"
    else:
        category = "Positive Payoff" if node["payoff"] >= 0 else "Negative Payoff"
    node_rows.append({"x": node["x"], "y": node["y"], "category": category, "pruned": node["pruned"]})

node_df = pd.DataFrame(node_rows)

# Seaborn marker and palette mappings for node types
marker_map = {
    "Decision": "s",  # square for decision nodes
    "Chance": "o",  # circle for chance nodes
    "Positive Payoff": ">",  # right triangle for positive terminal
    "Negative Payoff": ">",  # right triangle for negative terminal
}
color_map = {
    "Decision": decision_color,
    "Chance": chance_color,
    "Positive Payoff": terminal_pos_color,
    "Negative Payoff": terminal_neg_color,
}

fig, ax = plt.subplots(figsize=(16, 9))

# Draw branches using sns.lineplot with units parameter (idiomatic seaborn)
optimal_branches = branch_df[branch_df["style"] == "optimal"]
pruned_branches = branch_df[branch_df["style"] == "pruned"]

sns.lineplot(
    data=optimal_branches,
    x="x",
    y="y",
    units="seg",
    estimator=None,
    color=branch_color,
    linewidth=2.5,
    sort=False,
    ax=ax,
    legend=False,
)
sns.lineplot(
    data=pruned_branches,
    x="x",
    y="y",
    units="seg",
    estimator=None,
    color=branch_color,
    linewidth=1.8,
    alpha=pruned_alpha,
    linestyle="--",
    sort=False,
    ax=ax,
    legend=False,
)

# Draw nodes using sns.scatterplot with hue/style mapping (replaces matplotlib patches)
active_nodes = node_df[~node_df["pruned"]]
pruned_node_df = node_df[node_df["pruned"]]

sns.scatterplot(
    data=active_nodes,
    x="x",
    y="y",
    hue="category",
    style="category",
    markers=marker_map,
    palette=color_map,
    s=5000,
    edgecolor="white",
    linewidth=3,
    ax=ax,
    legend=False,
    zorder=3,
)

sns.scatterplot(
    data=pruned_node_df,
    x="x",
    y="y",
    hue="category",
    style="category",
    markers=marker_map,
    palette=color_map,
    s=5000,
    edgecolor="white",
    linewidth=3,
    alpha=pruned_alpha,
    ax=ax,
    legend=False,
    zorder=3,
)

# Add EMV and payoff text labels
for node in tree:
    nx, ny = node["x"], node["y"]
    alpha = pruned_alpha if node["pruned"] else normal_alpha

    if node["type"] in ("decision", "chance"):
        node_color = decision_color if node["type"] == "decision" else chance_color
        if node["pruned"]:
            ax.text(
                nx,
                ny + 0.8,
                f"EMV ${node['emv']}K",
                fontsize=13,
                fontweight="bold",
                ha="center",
                va="bottom",
                color=node_color,
                alpha=max(alpha, 0.6),
                zorder=4,
            )
        else:
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

    elif node["type"] == "terminal":
        color = terminal_pos_color if node["payoff"] >= 0 else terminal_neg_color
        sign = "+" if node["payoff"] >= 0 else ""
        ax.text(
            nx + 0.65,
            ny,
            f"${sign}{node['payoff']}K",
            fontsize=15,
            fontweight="bold",
            ha="left",
            va="center",
            color=color,
            alpha=alpha,
            zorder=4,
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
ax.set_ylim(-1.0, 10.5)
ax.axis("off")
sns.despine(left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
