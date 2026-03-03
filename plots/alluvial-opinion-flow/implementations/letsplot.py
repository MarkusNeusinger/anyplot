"""pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: letsplot 4.8.2 | Python 3.14.3
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_ribbon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Survey data: 1000 respondents tracked across 4 quarterly waves
np.random.seed(42)

waves = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]

# Initial distribution at Q1 (1000 total respondents)
initial_counts = {"Strongly Agree": 120, "Agree": 250, "Neutral": 280, "Disagree": 220, "Strongly Disagree": 130}

# Flows between waves - showing gradual polarization (neutral shrinks, extremes grow)
flows_q1_q2 = [
    ("Strongly Agree", "Strongly Agree", 110),
    ("Strongly Agree", "Agree", 8),
    ("Strongly Agree", "Neutral", 2),
    ("Agree", "Strongly Agree", 25),
    ("Agree", "Agree", 195),
    ("Agree", "Neutral", 20),
    ("Agree", "Disagree", 10),
    ("Neutral", "Strongly Agree", 10),
    ("Neutral", "Agree", 45),
    ("Neutral", "Neutral", 170),
    ("Neutral", "Disagree", 40),
    ("Neutral", "Strongly Disagree", 15),
    ("Disagree", "Agree", 8),
    ("Disagree", "Neutral", 18),
    ("Disagree", "Disagree", 170),
    ("Disagree", "Strongly Disagree", 24),
    ("Strongly Disagree", "Neutral", 5),
    ("Strongly Disagree", "Disagree", 10),
    ("Strongly Disagree", "Strongly Disagree", 115),
]

flows_q2_q3 = [
    ("Strongly Agree", "Strongly Agree", 135),
    ("Strongly Agree", "Agree", 10),
    ("Agree", "Strongly Agree", 30),
    ("Agree", "Agree", 205),
    ("Agree", "Neutral", 15),
    ("Agree", "Disagree", 6),
    ("Neutral", "Strongly Agree", 8),
    ("Neutral", "Agree", 35),
    ("Neutral", "Neutral", 130),
    ("Neutral", "Disagree", 32),
    ("Neutral", "Strongly Disagree", 10),
    ("Disagree", "Agree", 5),
    ("Disagree", "Neutral", 12),
    ("Disagree", "Disagree", 185),
    ("Disagree", "Strongly Disagree", 28),
    ("Strongly Disagree", "Neutral", 3),
    ("Strongly Disagree", "Disagree", 8),
    ("Strongly Disagree", "Strongly Disagree", 143),
]

flows_q3_q4 = [
    ("Strongly Agree", "Strongly Agree", 165),
    ("Strongly Agree", "Agree", 8),
    ("Agree", "Strongly Agree", 35),
    ("Agree", "Agree", 198),
    ("Agree", "Neutral", 12),
    ("Agree", "Disagree", 5),
    ("Neutral", "Strongly Agree", 5),
    ("Neutral", "Agree", 28),
    ("Neutral", "Neutral", 100),
    ("Neutral", "Disagree", 25),
    ("Neutral", "Strongly Disagree", 7),
    ("Disagree", "Agree", 4),
    ("Disagree", "Neutral", 8),
    ("Disagree", "Disagree", 185),
    ("Disagree", "Strongly Disagree", 33),
    ("Strongly Disagree", "Neutral", 2),
    ("Strongly Disagree", "Disagree", 5),
    ("Strongly Disagree", "Strongly Disagree", 174),
]

all_flows = [flows_q1_q2, flows_q2_q3, flows_q3_q4]

# Calculate totals at each wave
wave_totals = [initial_counts.copy()]
for wave_flows in all_flows:
    totals = dict.fromkeys(categories, 0)
    for _, to_cat, val in wave_flows:
        totals[to_cat] += val
    wave_totals.append(totals)

# Layout parameters
x_positions = [0.10, 0.37, 0.63, 0.90]
node_width = 0.025
node_gap = 0.015
total_respondents = sum(initial_counts.values())

# Colors per opinion category - cohesive palette anchored on Python Blue
category_colors = {
    "Strongly Agree": "#306998",
    "Agree": "#5B9BD5",
    "Neutral": "#9CA3AF",
    "Disagree": "#E8915A",
    "Strongly Disagree": "#C0392B",
}

# Calculate node positions at each wave
node_positions = []
for wave_idx, totals in enumerate(wave_totals):
    positions = {}
    y_offset = 0.06
    for cat in categories:
        height = totals.get(cat, 0) / total_respondents * 0.82
        positions[cat] = {"y0": y_offset, "y1": y_offset + height, "x": x_positions[wave_idx]}
        y_offset += height + node_gap
    node_positions.append(positions)

# Build flow ribbons using geom_ribbon (x, ymin, ymax) instead of manual polygon vertices
ribbon_data = []
n_points = 40

for wave_idx, wave_flows in enumerate(all_flows):
    src_positions = node_positions[wave_idx]
    tgt_positions = node_positions[wave_idx + 1]
    x_left = x_positions[wave_idx] + node_width / 2
    x_right = x_positions[wave_idx + 1] - node_width / 2
    src_offsets = dict.fromkeys(categories, 0.0)
    tgt_offsets = dict.fromkeys(categories, 0.0)

    for from_cat, to_cat, val in wave_flows:
        flow_height = val / total_respondents * 0.82
        is_stable = from_cat == to_cat

        src_y0 = src_positions[from_cat]["y0"] + src_offsets[from_cat]
        src_y1 = src_y0 + flow_height
        src_offsets[from_cat] += flow_height

        tgt_y0 = tgt_positions[to_cat]["y0"] + tgt_offsets[to_cat]
        tgt_y1 = tgt_y0 + flow_height
        tgt_offsets[to_cat] += flow_height

        flow_id = f"w{wave_idx}_{from_cat}_{to_cat}"
        stability = "stable" if is_stable else "changed"

        for i in range(n_points + 1):
            t = i / n_points
            x = x_left + t * (x_right - x_left)
            ease = t * t * (3 - 2 * t)
            ymin_val = src_y0 + ease * (tgt_y0 - src_y0)
            ymax_val = src_y1 + ease * (tgt_y1 - src_y1)

            ribbon_data.append(
                {
                    "x": x,
                    "ymin": ymin_val,
                    "ymax": ymax_val,
                    "flow_id": flow_id,
                    "category": from_cat,
                    "stability": stability,
                    "from_cat": from_cat,
                    "to_cat": to_cat,
                    "count": str(val),
                }
            )

df_ribbons = pd.DataFrame(ribbon_data)
df_stable = df_ribbons[df_ribbons["stability"] == "stable"]
df_changed = df_ribbons[df_ribbons["stability"] == "changed"]

# Build node rectangles with metadata for tooltips
node_rects = []
for wave_idx, positions in enumerate(node_positions):
    for cat in categories:
        pos = positions[cat]
        node_rects.append(
            {
                "xmin": pos["x"] - node_width / 2,
                "xmax": pos["x"] + node_width / 2,
                "ymin": pos["y0"],
                "ymax": pos["y1"],
                "category": cat,
                "wave": waves[wave_idx],
                "count": str(wave_totals[wave_idx][cat]),
            }
        )

df_nodes = pd.DataFrame(node_rects)

# Build labels
label_rows = []

# Wave headers
for i, wave in enumerate(waves):
    label_rows.append({"x": x_positions[i], "y": 0.97, "label": wave, "type": "header"})

# Category labels and counts on left side of first wave
for cat in categories:
    pos = node_positions[0][cat]
    count = initial_counts[cat]
    label_rows.append(
        {
            "x": x_positions[0] - node_width - 0.015,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{cat}\n({count})",
            "type": "left_label",
        }
    )

# Category labels with counts and net change on right side of last wave
for cat in categories:
    pos = node_positions[3][cat]
    count = wave_totals[3][cat]
    change = count - initial_counts[cat]
    if change > 0:
        change_str = f", +{change}"
    elif change < 0:
        change_str = f", {change}"
    else:
        change_str = ""
    label_rows.append(
        {
            "x": x_positions[3] + node_width + 0.015,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{cat}\n({count}{change_str})",
            "type": "right_label",
        }
    )

# Count labels inside nodes for middle waves
for wave_idx in [1, 2]:
    for cat in categories:
        pos = node_positions[wave_idx][cat]
        count = wave_totals[wave_idx][cat]
        height = pos["y1"] - pos["y0"]
        if height > 0.03:
            label_rows.append(
                {
                    "x": x_positions[wave_idx],
                    "y": (pos["y0"] + pos["y1"]) / 2,
                    "label": str(count),
                    "type": "node_count",
                }
            )

df_labels = pd.DataFrame(label_rows)

# Assemble plot with geom_ribbon for flows and layer_tooltips for interactivity
plot = (
    ggplot()
    + geom_ribbon(
        aes(x="x", ymin="ymin", ymax="ymax", group="flow_id", fill="category"),
        data=df_changed,
        alpha=0.35,
        color="white",
        size=0.05,
        tooltips=layer_tooltips().line("@from_cat -> @to_cat").line("@count respondents (changed)"),
    )
    + geom_ribbon(
        aes(x="x", ymin="ymin", ymax="ymax", group="flow_id", fill="category"),
        data=df_stable,
        alpha=0.6,
        color="white",
        size=0.05,
        tooltips=layer_tooltips().line("@from_cat (stable)").line("@count respondents"),
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category"),
        data=df_nodes,
        color="#2A2A2A",
        size=0.8,
        tooltips=layer_tooltips().line("@category").line("Wave: @wave").line("Count: @count"),
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_labels[df_labels["type"] == "header"], size=17, fontface="bold"
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels[df_labels["type"] == "left_label"], size=13, hjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels[df_labels["type"] == "right_label"], size=13, hjust=0)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["type"] == "node_count"],
        size=11,
        color="white",
        fontface="bold",
    )
    + scale_fill_manual(values=category_colors)
    + labs(
        title="alluvial-opinion-flow \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Polarization trend: Neutral shrinks 280\u2192122 as extreme positions grow",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + scale_x_continuous(limits=[-0.08, 1.08])
    + scale_y_continuous(limits=[-0.02, 1.04])
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
