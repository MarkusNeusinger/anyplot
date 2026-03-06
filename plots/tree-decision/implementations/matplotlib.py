""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


# Data — two-stage investment decision tree
# Structure: (node_id, node_type, parent_id, branch_label, probability, payoff, emv, pruned)
# EMV rollback: D2=max(1.2M,800K)=1.2M, C1=0.6*1.2M+0.4*100K=760K, D1=max(760K,0)=760K
nodes = [
    ("D1", "decision", None, None, None, None, 760000, False),
    ("C1", "chance", "D1", "Invest", None, None, 760000, False),
    ("T1", "terminal", "D1", "Don't Invest", None, 0, None, True),
    ("D2", "decision", "C1", "High Demand (0.6)", 0.6, None, 1200000, False),
    ("T2", "terminal", "C1", "Low Demand (0.4)", 0.4, 100000, None, False),
    ("T3", "terminal", "D2", "Expand", None, 1200000, None, False),
    ("T4", "terminal", "D2", "Maintain", None, 800000, None, True),
]

# Layout — manual left-to-right positions, spread to fill canvas
positions = {
    "D1": (0.8, 4.6),
    "C1": (3.5, 6.8),
    "T1": (3.5, 2.2),
    "D2": (6.2, 8.2),
    "T2": (6.2, 4.3),
    "T3": (9.0, 9.2),
    "T4": (9.0, 7.2),
}

# Colors — refined palette
decision_color = "#306998"
chance_color = "#D4682A"
terminal_color = "#2A9D8F"
pruned_color = "#B0B0B0"
bg_color = "#FAFAFA"
branch_color = "#444444"

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg_color)
ax.set_facecolor(bg_color)

# Draw branches with FancyArrowPatch for refined connectors
for node in nodes:
    nid, ntype, parent_id, label, prob, payoff, emv, pruned = node
    if parent_id is None:
        continue
    px, py = positions[parent_id]
    cx, cy = positions[nid]

    line_color = pruned_color if pruned else branch_color
    line_style = "dashed" if pruned else "solid"
    lw = 2.0 if pruned else 2.8

    arrow = FancyArrowPatch(
        (px, py),
        (cx, cy),
        arrowstyle="-",
        color=line_color,
        linestyle=line_style,
        linewidth=lw,
        zorder=1,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)

    # Pruned marker
    if pruned:
        mx, my = (px + cx) / 2, (py + cy) / 2
        ax.plot(mx, my, marker="x", markersize=16, color="#CC3333", markeredgewidth=3.5, zorder=5)

    # Branch label
    if label:
        mx, my = px + (cx - px) * 0.35, py + (cy - py) * 0.35
        offset_y = 0.55 if cy >= py else -0.55
        ax.text(
            mx,
            my + offset_y,
            label,
            fontsize=16,
            ha="center",
            va="center",
            color=pruned_color if pruned else "#555555",
            fontweight="normal",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "#DDDDDD",
                "alpha": 0.92,
                "linewidth": 0.8,
            },
            zorder=6,
        )

# Draw nodes
node_size = 0.45
for node in nodes:
    nid, ntype, parent_id, label, prob, payoff, emv, pruned = node
    x, y = positions[nid]

    shadow_fx = [pe.SimplePatchShadow(offset=(3, -3), shadow_rgbFace="black", alpha=0.15), pe.Normal()]

    if ntype == "decision":
        rect = FancyBboxPatch(
            (x - node_size, y - node_size),
            node_size * 2,
            node_size * 2,
            boxstyle="round,pad=0.03",
            facecolor=decision_color,
            edgecolor="white",
            linewidth=2.5,
            zorder=3,
        )
        rect.set_path_effects(shadow_fx)
        ax.add_patch(rect)
        if emv is not None:
            emv_text = f"${emv / 1e6:.1f}M" if emv >= 1e6 else f"${emv / 1e3:.0f}K"
            ax.text(
                x,
                y + 0.06,
                "EMV",
                fontsize=16,
                ha="center",
                va="bottom",
                color="white",
                fontweight="bold",
                zorder=4,
                alpha=0.85,
            )
            ax.text(
                x, y - 0.06, emv_text, fontsize=18, ha="center", va="top", color="white", fontweight="bold", zorder=4
            )

    elif ntype == "chance":
        circle = plt.Circle((x, y), node_size, facecolor=chance_color, edgecolor="white", linewidth=2.5, zorder=3)
        circle.set_path_effects(shadow_fx)
        ax.add_patch(circle)
        if emv is not None:
            emv_text = f"${emv / 1e6:.1f}M" if emv >= 1e6 else f"${emv / 1e3:.0f}K"
            ax.text(
                x,
                y + 0.06,
                "EMV",
                fontsize=16,
                ha="center",
                va="bottom",
                color="white",
                fontweight="bold",
                zorder=4,
                alpha=0.85,
            )
            ax.text(
                x, y - 0.06, emv_text, fontsize=18, ha="center", va="top", color="white", fontweight="bold", zorder=4
            )

    elif ntype == "terminal":
        triangle_size = node_size * 0.95
        tri_color = terminal_color if not pruned else pruned_color
        triangle = plt.Polygon(
            [
                (x - triangle_size * 0.6, y - triangle_size),
                (x - triangle_size * 0.6, y + triangle_size),
                (x + triangle_size, y),
            ],
            facecolor=tri_color,
            edgecolor="white",
            linewidth=2.5,
            zorder=3,
        )
        triangle.set_path_effects(shadow_fx)
        ax.add_patch(triangle)
        if payoff is not None:
            payoff_text = f"${payoff / 1e6:.1f}M" if payoff >= 1e6 else f"${payoff / 1e3:.0f}K"
            ax.text(
                x + triangle_size + 0.2,
                y,
                payoff_text,
                fontsize=20,
                ha="left",
                va="center",
                fontweight="bold",
                color=tri_color,
                zorder=4,
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
        markeredgewidth=2.5,
        markersize=12,
        label="Pruned Branch",
        linewidth=1.5,
        markerfacecolor="#CC3333",
    ),
]
legend = ax.legend(
    handles=legend_handles,
    fontsize=16,
    loc="lower right",
    framealpha=0.95,
    edgecolor="#CCCCCC",
    fancybox=True,
    shadow=True,
    borderpad=1.0,
)
legend.get_frame().set_facecolor("white")

# Style
ax.set_title("tree-decision · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20, color="#333333")
ax.set_xlim(-0.3, 11.0)
ax.set_ylim(0.8, 10.5)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=bg_color)
