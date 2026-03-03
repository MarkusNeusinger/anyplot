"""pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-03
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Opinion survey tracking 1000 respondents across 4 waves
# Shows gradual polarization: moderate positions erode toward extremes
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
cat_order = {cat: i for i, cat in enumerate(categories)}
wave_labels = ["Wave 1", "Wave 2", "Wave 3", "Wave 4"]

# Transition matrices (rows=source category, cols=target category)
# Wave 1→2: mostly stable, small initial shifts
m12 = np.array([[155, 18, 5, 2, 0], [22, 195, 28, 5, 0], [3, 20, 138, 22, 7], [0, 5, 18, 155, 22], [0, 3, 5, 15, 157]])

# Wave 2→3: accelerating polarization
m23 = np.array([[155, 15, 8, 2, 0], [30, 175, 25, 8, 3], [5, 18, 128, 30, 13], [0, 5, 12, 150, 32], [0, 2, 5, 10, 169]])

# Wave 3→4: strong polarization, neutral collapses
m34 = np.array([[168, 15, 5, 2, 0], [35, 148, 22, 8, 2], [3, 12, 98, 42, 23], [0, 3, 8, 142, 47], [0, 2, 3, 12, 200]])

# Build transitions DataFrame
rows = []
for matrix, (fw, tw) in zip([m12, m23, m34], [(0, 1), (1, 2), (2, 3)], strict=True):
    for i, from_cat in enumerate(categories):
        for j, to_cat in enumerate(categories):
            count = int(matrix[i, j])
            if count > 0:
                rows.append(
                    {
                        "from_wave": fw,
                        "to_wave": tw,
                        "from_cat": from_cat,
                        "to_cat": to_cat,
                        "count": count,
                        "is_stable": i == j,
                    }
                )

transitions = pd.DataFrame(rows)
transitions["from_ord"] = transitions["from_cat"].map(cat_order)
transitions["to_ord"] = transitions["to_cat"].map(cat_order)
transitions = transitions.sort_values(
    ["from_wave", "from_ord", "is_stable", "to_ord"], ascending=[True, True, False, True]
).reset_index(drop=True)

# Diverging color palette (colorblind-safe)
cat_colors = {
    "Strongly Agree": "#306998",
    "Agree": "#6BAED6",
    "Neutral": "#969696",
    "Disagree": "#E8915A",
    "Strongly Disagree": "#C0392B",
}

# Layout
x_positions = {0: 0.14, 1: 0.38, 2: 0.62, 3: 0.86}
node_width = 0.055
node_gap = 0.02
total_height = 0.78
y_start = 0.88

# Calculate node sizes at each wave
node_positions = {}
for w in range(4):
    if w == 0:
        totals = transitions[transitions["from_wave"] == 0].groupby("from_cat")["count"].sum()
    else:
        totals = transitions[transitions["to_wave"] == w].groupby("to_cat")["count"].sum()

    total_n = totals.sum()
    current_y = y_start

    for cat in categories:
        n = totals.get(cat, 0)
        height = (n / total_n) * total_height

        node_positions[(w, cat)] = {
            "x": x_positions[w],
            "y_top": current_y,
            "y_bottom": current_y - height,
            "height": height,
            "count": int(n),
            "offset_out": 0.0,
            "offset_in": 0.0,
        }
        current_y -= height + node_gap

# Node rectangles
node_data = []
for (w, cat), pos in node_positions.items():
    node_data.append(
        {
            "wave": w,
            "category": cat,
            "xmin": pos["x"] - node_width / 2,
            "xmax": pos["x"] + node_width / 2,
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_x": pos["x"],
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "count": pos["count"],
        }
    )
nodes_df = pd.DataFrame(node_data)

# Build flow polygons with separate in/out offset tracking
stable_polys = []
changer_polys = []
min_flow = 2

for _, row in transitions.iterrows():
    fw, tw = row["from_wave"], row["to_wave"]
    fc, tc = row["from_cat"], row["to_cat"]
    count = row["count"]
    is_stable = row["is_stable"]

    src = node_positions[(fw, fc)]
    tgt = node_positions[(tw, tc)]

    src_total = transitions[(transitions["from_wave"] == fw) & (transitions["from_cat"] == fc)]["count"].sum()
    fh_src = (count / src_total) * src["height"] if src_total > 0 else 0

    tgt_total = transitions[(transitions["to_wave"] == tw) & (transitions["to_cat"] == tc)]["count"].sum()
    fh_tgt = (count / tgt_total) * tgt["height"] if tgt_total > 0 else 0

    if count < min_flow:
        src["offset_out"] += fh_src
        tgt["offset_in"] += fh_tgt
        continue

    # Source y (right side of source node)
    src_y_top = src["y_top"] - src["offset_out"]
    src_y_bottom = src_y_top - fh_src
    src["offset_out"] += fh_src

    # Target y (left side of target node)
    tgt_y_top = tgt["y_top"] - tgt["offset_in"]
    tgt_y_bottom = tgt_y_top - fh_tgt
    tgt["offset_in"] += fh_tgt

    # Curved polygon via cubic interpolation
    x_left = x_positions[fw] + node_width / 2
    x_right = x_positions[tw] - node_width / 2
    n_pts = 40

    t_param = np.linspace(0, 1, n_pts)
    xt = x_left + (x_right - x_left) * t_param
    yt = src_y_top + (tgt_y_top - src_y_top) * (3 * t_param**2 - 2 * t_param**3)

    xb = x_right + (x_left - x_right) * t_param
    yb = tgt_y_bottom + (src_y_bottom - tgt_y_bottom) * (3 * t_param**2 - 2 * t_param**3)

    x_poly = np.concatenate([xt, xb])
    y_poly = np.concatenate([yt, yb])

    flow_id = f"{fw}_{tw}_{fc}_{tc}"
    target_list = stable_polys if is_stable else changer_polys

    for k in range(len(x_poly)):
        target_list.append({"x": x_poly[k], "y": y_poly[k], "flow_id": flow_id, "from_cat": fc})

stable_df = pd.DataFrame(stable_polys)
changer_df = pd.DataFrame(changer_polys)

# Plot - changers drawn first (low opacity), stable on top (high opacity)
plot = (
    ggplot()
    + geom_polygon(changer_df, aes(x="x", y="y", group="flow_id", fill="from_cat"), alpha=0.18)
    + geom_polygon(stable_df, aes(x="x", y="y", group="flow_id", fill="from_cat"), alpha=0.55)
    + geom_rect(
        nodes_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category"), color="white", size=0.5
    )
    + geom_text(
        nodes_df,
        aes(x="label_x", y="label_y", label="count"),
        ha="center",
        va="center",
        size=10,
        color="white",
        fontweight="bold",
    )
    + scale_fill_manual(values=cat_colors, name="Opinion", breaks=categories)
    + labs(title="alluvial-opinion-flow · plotnine · pyplots.ai", x="", y="")
    + coord_cartesian(xlim=(0, 1), ylim=(-0.02, 1.0))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
    )
)

# Wave column headers
for w, label in enumerate(wave_labels):
    plot = plot + annotate(
        "text", x=x_positions[w], y=0.95, label=label, size=16, color="#333333", fontweight="bold", ha="center"
    )

# Category labels on left of first column
for cat in categories:
    pos = node_positions[(0, cat)]
    ly = (pos["y_top"] + pos["y_bottom"]) / 2
    plot = plot + annotate(
        "text",
        x=x_positions[0] - node_width / 2 - 0.012,
        y=ly,
        label=cat,
        size=8,
        color="#333333",
        fontweight="bold",
        ha="right",
        va="center",
    )

# Category labels on right of last column
for cat in categories:
    pos = node_positions[(3, cat)]
    ly = (pos["y_top"] + pos["y_bottom"]) / 2
    plot = plot + annotate(
        "text",
        x=x_positions[3] + node_width / 2 + 0.012,
        y=ly,
        label=cat,
        size=8,
        color="#333333",
        fontweight="bold",
        ha="left",
        va="center",
    )

# Save
plot.save("plot.png", dpi=300, verbose=False)
