""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-03
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path


# Data: Employee engagement survey tracking 1000 staff across 4 quarterly waves
np.random.seed(42)

waves = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
colors = {
    "Strongly Agree": "#306998",
    "Agree": "#5BA865",
    "Neutral": "#95A5A6",
    "Disagree": "#E67E22",
    "Strongly Disagree": "#C0392B",
}

# Respondent counts per category at each wave
node_values = {
    "Q1 2025": {"Strongly Agree": 180, "Agree": 250, "Neutral": 220, "Disagree": 200, "Strongly Disagree": 150},
    "Q2 2025": {"Strongly Agree": 200, "Agree": 230, "Neutral": 190, "Disagree": 210, "Strongly Disagree": 170},
    "Q3 2025": {"Strongly Agree": 220, "Agree": 210, "Neutral": 160, "Disagree": 220, "Strongly Disagree": 190},
    "Q4 2025": {"Strongly Agree": 240, "Agree": 190, "Neutral": 140, "Disagree": 230, "Strongly Disagree": 200},
}

# Flow matrices between consecutive waves (source_cat -> target_cat: count)
flows = [
    # Q1 -> Q2: moderate shifts toward poles
    {
        ("Strongly Agree", "Strongly Agree"): 155,
        ("Strongly Agree", "Agree"): 20,
        ("Strongly Agree", "Neutral"): 5,
        ("Strongly Agree", "Disagree"): 0,
        ("Strongly Agree", "Strongly Disagree"): 0,
        ("Agree", "Strongly Agree"): 30,
        ("Agree", "Agree"): 185,
        ("Agree", "Neutral"): 25,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 0,
        ("Neutral", "Strongly Agree"): 10,
        ("Neutral", "Agree"): 20,
        ("Neutral", "Neutral"): 145,
        ("Neutral", "Disagree"): 35,
        ("Neutral", "Strongly Disagree"): 10,
        ("Disagree", "Strongly Agree"): 5,
        ("Disagree", "Agree"): 5,
        ("Disagree", "Neutral"): 15,
        ("Disagree", "Disagree"): 150,
        ("Disagree", "Strongly Disagree"): 25,
        ("Strongly Disagree", "Strongly Agree"): 0,
        ("Strongly Disagree", "Agree"): 0,
        ("Strongly Disagree", "Neutral"): 0,
        ("Strongly Disagree", "Disagree"): 15,
        ("Strongly Disagree", "Strongly Disagree"): 135,
    },
    # Q2 -> Q3: accelerating polarization
    {
        ("Strongly Agree", "Strongly Agree"): 175,
        ("Strongly Agree", "Agree"): 20,
        ("Strongly Agree", "Neutral"): 5,
        ("Strongly Agree", "Disagree"): 0,
        ("Strongly Agree", "Strongly Disagree"): 0,
        ("Agree", "Strongly Agree"): 35,
        ("Agree", "Agree"): 165,
        ("Agree", "Neutral"): 20,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 0,
        ("Neutral", "Strongly Agree"): 5,
        ("Neutral", "Agree"): 20,
        ("Neutral", "Neutral"): 120,
        ("Neutral", "Disagree"): 35,
        ("Neutral", "Strongly Disagree"): 10,
        ("Disagree", "Strongly Agree"): 5,
        ("Disagree", "Agree"): 5,
        ("Disagree", "Neutral"): 15,
        ("Disagree", "Disagree"): 155,
        ("Disagree", "Strongly Disagree"): 30,
        ("Strongly Disagree", "Strongly Agree"): 0,
        ("Strongly Disagree", "Agree"): 0,
        ("Strongly Disagree", "Neutral"): 0,
        ("Strongly Disagree", "Disagree"): 20,
        ("Strongly Disagree", "Strongly Disagree"): 150,
    },
    # Q3 -> Q4: continued polarization, neutral shrinks further
    {
        ("Strongly Agree", "Strongly Agree"): 195,
        ("Strongly Agree", "Agree"): 20,
        ("Strongly Agree", "Neutral"): 5,
        ("Strongly Agree", "Disagree"): 0,
        ("Strongly Agree", "Strongly Disagree"): 0,
        ("Agree", "Strongly Agree"): 35,
        ("Agree", "Agree"): 150,
        ("Agree", "Neutral"): 15,
        ("Agree", "Disagree"): 10,
        ("Agree", "Strongly Disagree"): 0,
        ("Neutral", "Strongly Agree"): 5,
        ("Neutral", "Agree"): 15,
        ("Neutral", "Neutral"): 105,
        ("Neutral", "Disagree"): 25,
        ("Neutral", "Strongly Disagree"): 10,
        ("Disagree", "Strongly Agree"): 5,
        ("Disagree", "Agree"): 5,
        ("Disagree", "Neutral"): 15,
        ("Disagree", "Disagree"): 165,
        ("Disagree", "Strongly Disagree"): 30,
        ("Strongly Disagree", "Strongly Agree"): 0,
        ("Strongly Disagree", "Agree"): 0,
        ("Strongly Disagree", "Neutral"): 0,
        ("Strongly Disagree", "Disagree"): 30,
        ("Strongly Disagree", "Strongly Disagree"): 160,
    },
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

x_positions = [2.0, 4.5, 7.0, 9.5]
node_width = 0.8
total_height = 7.5
node_gap = 0.22

# Calculate node positions
node_bounds = {}
for t_idx, wave in enumerate(waves):
    values = [node_values[wave][cat] for cat in categories]
    total = sum(values)
    usable_height = total_height - (len(categories) - 1) * node_gap
    heights = [v / total * usable_height for v in values]

    y = 0.5
    for c_idx, cat in enumerate(categories):
        h = heights[c_idx]
        node_bounds[(wave, cat)] = {"x": x_positions[t_idx], "y_start": y, "height": h}
        y += h + node_gap

# Track the largest cross-category flows for net flow highlighting
cross_flows = []

# Draw flows between consecutive waves
for t_idx in range(len(waves) - 1):
    wave_from = waves[t_idx]
    wave_to = waves[t_idx + 1]

    from_offsets = dict.fromkeys(categories, 0.0)
    to_offsets = dict.fromkeys(categories, 0.0)

    flow_data = flows[t_idx]
    for from_cat in categories:
        for to_cat in categories:
            flow_val = flow_data.get((from_cat, to_cat), 0)
            if flow_val <= 0:
                continue

            from_node = node_bounds[(wave_from, from_cat)]
            to_node = node_bounds[(wave_to, to_cat)]

            from_total = sum(node_values[wave_from].values())
            to_total = sum(node_values[wave_to].values())

            usable_height = total_height - (len(categories) - 1) * node_gap
            from_height = flow_val / from_total * usable_height
            to_height = flow_val / to_total * usable_height

            x0 = from_node["x"] + node_width / 2
            x1 = to_node["x"] - node_width / 2
            mid_x = (x0 + x1) / 2

            y0_start = from_node["y_start"] + from_offsets[from_cat]
            y0_end = y0_start + from_height
            y1_start = to_node["y_start"] + to_offsets[to_cat]
            y1_end = y1_start + to_height

            # Stable flows (same category) get higher opacity, changers get lower
            is_stable = from_cat == to_cat
            alpha = 0.6 if is_stable else 0.25

            # Highlight the largest cross-category flows with a subtle edge
            is_major_cross = (not is_stable) and flow_val >= 25
            edge_color = colors[from_cat] if is_major_cross else "none"
            edge_alpha = 0.5 if is_major_cross else 0
            edge_lw = 1.0 if is_major_cross else 0

            verts = [
                (x0, y0_start),
                (mid_x, y0_start),
                (mid_x, y1_start),
                (x1, y1_start),
                (x1, y1_end),
                (mid_x, y1_end),
                (mid_x, y0_end),
                (x0, y0_end),
                (x0, y0_start),
            ]
            codes = [
                Path.MOVETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.LINETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.CLOSEPOLY,
            ]
            path = Path(verts, codes)
            patch = mpatches.PathPatch(
                path, facecolor=colors[from_cat], edgecolor=edge_color, alpha=alpha, linewidth=edge_lw
            )
            if is_major_cross:
                patch.set_path_effects([patheffects.withStroke(linewidth=1.5, foreground=colors[from_cat], alpha=0.4)])
            ax.add_patch(patch)

            # Track cross-category flows for annotation
            if not is_stable and flow_val >= 30:
                cross_flows.append(
                    {
                        "from": from_cat,
                        "to": to_cat,
                        "val": flow_val,
                        "mid_x": mid_x,
                        "mid_y": (y0_start + y0_end + y1_start + y1_end) / 4,
                    }
                )

            from_offsets[from_cat] += from_height
            to_offsets[to_cat] += to_height

# Draw nodes with FancyBboxPatch for rounded corners
shadow_effect = [patheffects.withSimplePatchShadow(offset=(1.5, -1.5), shadow_rgbFace="#00000015")]
for wave in waves:
    for cat in categories:
        node = node_bounds[(wave, cat)]
        rect = mpatches.FancyBboxPatch(
            (node["x"] - node_width / 2, node["y_start"]),
            node_width,
            node["height"],
            boxstyle="round,pad=0.02",
            facecolor=colors[cat],
            edgecolor="white",
            linewidth=2.5,
            path_effects=shadow_effect,
        )
        ax.add_patch(rect)

        # Label with category abbreviation and respondent count
        count = node_values[wave][cat]
        short = {
            "Strongly Agree": "Str.\nAgree",
            "Agree": "Agree",
            "Neutral": "Neutral",
            "Disagree": "Disagree",
            "Strongly Disagree": "Str.\nDisagree",
        }
        label = f"{short[cat]}\nn={count}"
        text_color = "white" if cat != "Neutral" else "#1a1a1a"
        ax.text(
            node["x"],
            node["y_start"] + node["height"] / 2,
            label,
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color=text_color,
            path_effects=[patheffects.withStroke(linewidth=1.5, foreground="#00000022")],
        )

# Wave column headers
for t_idx, wave in enumerate(waves):
    ax.text(
        x_positions[t_idx],
        total_height + 0.9,
        wave,
        ha="center",
        va="bottom",
        fontsize=20,
        fontweight="bold",
        color="#333333",
    )

# Annotate net polarization trend
# Calculate net change from Q1 to Q4 for key categories
q1_neutral = node_values["Q1 2025"]["Neutral"]
q4_neutral = node_values["Q4 2025"]["Neutral"]
q1_strong = node_values["Q1 2025"]["Strongly Agree"] + node_values["Q1 2025"]["Strongly Disagree"]
q4_strong = node_values["Q4 2025"]["Strongly Agree"] + node_values["Q4 2025"]["Strongly Disagree"]

ax.annotate(
    f"Neutral: {q1_neutral} \u2192 {q4_neutral}  (\u2013{q1_neutral - q4_neutral})",
    xy=(
        x_positions[-1] + node_width / 2 + 0.15,
        node_bounds[("Q4 2025", "Neutral")]["y_start"] + node_bounds[("Q4 2025", "Neutral")]["height"] / 2,
    ),
    fontsize=16,
    fontweight="medium",
    color="#666666",
    va="center",
)
ax.annotate(
    f"Strong opinions: {q1_strong} \u2192 {q4_strong}  (+{q4_strong - q1_strong})",
    xy=(
        x_positions[-1] + node_width / 2 + 0.15,
        node_bounds[("Q4 2025", "Strongly Agree")]["y_start"]
        + node_bounds[("Q4 2025", "Strongly Agree")]["height"] / 2,
    ),
    fontsize=16,
    fontweight="medium",
    color="#306998",
    va="center",
)

# Legend distinguishing stable vs changing flows
legend_elements = [
    mpatches.Patch(facecolor="#306998", alpha=0.6, edgecolor="#333333", linewidth=1.5, label="Stable (same opinion)"),
    mpatches.Patch(facecolor="#306998", alpha=0.25, edgecolor="#333333", linewidth=1.5, label="Changed opinion"),
]
for cat in categories:
    legend_elements.append(mpatches.Patch(facecolor=colors[cat], label=cat))

ax.legend(
    handles=legend_elements,
    loc="lower left",
    bbox_to_anchor=(0.0, -0.02),
    fontsize=16,
    framealpha=0.9,
    edgecolor="none",
    ncol=4,
)

# Style
ax.set_xlim(0.5, 14.0)
ax.set_ylim(-0.8, total_height + 2.6)
ax.set_title("alluvial-opinion-flow \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=30)
ax.text(
    0.5,
    1.015,
    "Neutral opinion declines as views polarize toward strong agreement and disagreement",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=18,
    fontstyle="italic",
    color="#666666",
)
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
