"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


# Data — two-stage investment decision tree
# Structure: (node_id, node_type, parent_id, branch_label, probability, payoff, emv, pruned)
nodes = [
    ("D1", "decision", None, None, None, None, 600000, False),
    ("C1", "chance", "D1", "Invest", None, None, 600000, False),
    ("T1", "terminal", "D1", "Don't Invest", None, 0, None, True),
    ("D2", "decision", "C1", "High Demand (0.6)", 0.6, None, 800000, False),
    ("T2", "terminal", "C1", "Low Demand (0.4)", 0.4, 100000, None, False),
    ("T3", "terminal", "D2", "Expand", None, 1200000, None, False),
    ("T4", "terminal", "D2", "Maintain", None, 800000, None, True),
]

# Layout — manual left-to-right positions
positions = {
    "D1": (0.5, 5.0),
    "C1": (3.0, 6.5),
    "T1": (3.0, 3.5),
    "D2": (5.5, 8.0),
    "T2": (5.5, 5.0),
    "T3": (8.0, 9.0),
    "T4": (8.0, 7.0),
}

# Colors
decision_color = "#306998"
chance_color = "#E8793A"
terminal_color = "#5A9E6F"
pruned_color = "#B0B0B0"

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw branches first (behind nodes)
for node in nodes:
    nid, ntype, parent_id, label, prob, payoff, emv, pruned = node
    if parent_id is None:
        continue
    px, py = positions[parent_id]
    cx, cy = positions[nid]

    line_color = pruned_color if pruned else "#555555"
    line_style = "--" if pruned else "-"
    line_width = 2.0 if pruned else 2.5

    ax.plot([px, cx], [py, cy], color=line_color, linestyle=line_style, linewidth=line_width, zorder=1)

    # Pruned marker
    if pruned:
        mx, my = (px + cx) / 2, (py + cy) / 2
        ax.plot(mx, my, marker="x", markersize=14, color="#CC3333", markeredgewidth=3, zorder=5)

    # Branch label
    if label:
        mx, my = px + (cx - px) * 0.45, py + (cy - py) * 0.45
        offset_y = 0.3 if cy >= py else -0.3
        ax.text(
            mx,
            my + offset_y,
            label,
            fontsize=13,
            ha="center",
            va="center",
            color=line_color if pruned else "#333333",
            fontweight="medium",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
        )

# Draw nodes
node_size = 0.35
for node in nodes:
    nid, ntype, parent_id, label, prob, payoff, emv, pruned = node
    x, y = positions[nid]

    if ntype == "decision":
        rect = FancyBboxPatch(
            (x - node_size, y - node_size),
            node_size * 2,
            node_size * 2,
            boxstyle="square,pad=0",
            facecolor=decision_color,
            edgecolor="white",
            linewidth=2,
            zorder=3,
        )
        ax.add_patch(rect)
        if emv is not None:
            ax.text(
                x,
                y,
                f"EMV\n${emv / 1e6:.1f}M",
                fontsize=12,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                zorder=4,
            )

    elif ntype == "chance":
        circle = plt.Circle((x, y), node_size, facecolor=chance_color, edgecolor="white", linewidth=2, zorder=3)
        ax.add_patch(circle)
        if emv is not None:
            ax.text(
                x,
                y,
                f"EMV\n${emv / 1e6:.1f}M",
                fontsize=12,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                zorder=4,
            )

    elif ntype == "terminal":
        triangle_size = node_size * 0.9
        triangle = plt.Polygon(
            [
                (x - triangle_size * 0.6, y - triangle_size),
                (x - triangle_size * 0.6, y + triangle_size),
                (x + triangle_size, y),
            ],
            facecolor=terminal_color if not pruned else pruned_color,
            edgecolor="white",
            linewidth=2,
            zorder=3,
        )
        ax.add_patch(triangle)
        if payoff is not None:
            ax.text(
                x + triangle_size + 0.15,
                y,
                f"${payoff / 1e6:.1f}M" if payoff >= 1e6 else f"${payoff / 1e3:.0f}K",
                fontsize=14,
                ha="left",
                va="center",
                fontweight="bold",
                color=terminal_color if not pruned else pruned_color,
            )

# Legend
legend_handles = [
    mpatches.Patch(facecolor=decision_color, edgecolor="white", label="Decision Node"),
    mpatches.Patch(facecolor=chance_color, edgecolor="white", label="Chance Node"),
    mpatches.Patch(facecolor=terminal_color, edgecolor="white", label="Terminal Node"),
    plt.Line2D(
        [0],
        [0],
        color="#CC3333",
        marker="x",
        linestyle="--",
        markeredgewidth=2,
        markersize=10,
        label="Pruned Branch",
        linewidth=1.5,
        markerfacecolor="#CC3333",
    ),
]
ax.legend(handles=legend_handles, fontsize=14, loc="lower right", framealpha=0.9, edgecolor="#CCCCCC")

# Style
ax.set_title("tree-decision · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlim(-0.5, 9.5)
ax.set_ylim(2.5, 10.5)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
