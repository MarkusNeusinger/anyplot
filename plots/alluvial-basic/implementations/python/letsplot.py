""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Voter migration data across three election cycles
elections = ["2016", "2020", "2024"]
parties = ["Democrats", "Republicans", "Independents", "Non-Voters"]

# Initial distribution in 2016 (millions of voters)
initial_2016 = {"Democrats": 65, "Republicans": 63, "Independents": 8, "Non-Voters": 95}

# Flows from 2016 to 2020 (from_party -> to_party: millions)
flows_2016_2020 = [
    ("Democrats", "Democrats", 58),
    ("Democrats", "Republicans", 3),
    ("Democrats", "Independents", 2),
    ("Democrats", "Non-Voters", 2),
    ("Republicans", "Democrats", 5),
    ("Republicans", "Republicans", 54),
    ("Republicans", "Independents", 2),
    ("Republicans", "Non-Voters", 2),
    ("Independents", "Democrats", 3),
    ("Independents", "Republicans", 2),
    ("Independents", "Independents", 2),
    ("Independents", "Non-Voters", 1),
    ("Non-Voters", "Democrats", 15),
    ("Non-Voters", "Republicans", 12),
    ("Non-Voters", "Independents", 4),
    ("Non-Voters", "Non-Voters", 64),
]

# Flows from 2020 to 2024 (from_party -> to_party: millions)
flows_2020_2024 = [
    ("Democrats", "Democrats", 72),
    ("Democrats", "Republicans", 4),
    ("Democrats", "Independents", 3),
    ("Democrats", "Non-Voters", 2),
    ("Republicans", "Democrats", 3),
    ("Republicans", "Republicans", 63),
    ("Republicans", "Independents", 2),
    ("Republicans", "Non-Voters", 3),
    ("Independents", "Democrats", 4),
    ("Independents", "Republicans", 3),
    ("Independents", "Independents", 2),
    ("Independents", "Non-Voters", 1),
    ("Non-Voters", "Democrats", 6),
    ("Non-Voters", "Republicans", 8),
    ("Non-Voters", "Independents", 3),
    ("Non-Voters", "Non-Voters", 52),
]

# Calculate totals at each time point
totals_2016 = initial_2016.copy()
totals_2020 = dict.fromkeys(parties, 0)
for _, to_party, val in flows_2016_2020:
    totals_2020[to_party] += val

totals_2024 = dict.fromkeys(parties, 0)
for _, to_party, val in flows_2020_2024:
    totals_2024[to_party] += val

time_totals = [totals_2016, totals_2020, totals_2024]

# Layout parameters
x_positions = [0.15, 0.5, 0.85]
node_width = 0.03
node_gap = 0.02
total_flow = sum(totals_2016.values())

# Colors for parties - used for both nodes and flows
party_colors = {"Democrats": "#306998", "Republicans": "#DC2626", "Independents": "#FFD43B", "Non-Voters": "#9CA3AF"}

# Blended colors for transitions (source -> destination)
# Create color mapping for each flow combination
blend_colors = {}
for src in parties:
    for dst in parties:
        if src == dst:
            # Same party - use solid color
            blend_colors[f"{src}_{dst}"] = party_colors[src]
        else:
            # Different parties - use destination color with lower saturation
            # to indicate the transition direction
            blend_colors[f"{src}_{dst}"] = party_colors[dst]


# Calculate node positions at each time point
def calculate_node_positions(totals, x_pos):
    positions = {}
    y_offset = 0.05
    for party in parties:
        height = totals.get(party, 0) / total_flow * 0.85
        positions[party] = {"y0": y_offset, "y1": y_offset + height, "x": x_pos}
        y_offset += height + node_gap
    return positions


node_positions = [
    calculate_node_positions(totals_2016, x_positions[0]),
    calculate_node_positions(totals_2020, x_positions[1]),
    calculate_node_positions(totals_2024, x_positions[2]),
]

# Build flow polygons between time points
flow_data = []


def add_flows(flows, time_idx, src_positions, tgt_positions, x_left, x_right):
    src_offsets = dict.fromkeys(parties, 0)
    tgt_offsets = dict.fromkeys(parties, 0)

    for from_party, to_party, val in flows:
        flow_height = val / total_flow * 0.85

        src_y0 = src_positions[from_party]["y0"] + src_offsets[from_party]
        src_y1 = src_y0 + flow_height
        src_offsets[from_party] += flow_height

        tgt_y0 = tgt_positions[to_party]["y0"] + tgt_offsets[to_party]
        tgt_y1 = tgt_y0 + flow_height
        tgt_offsets[to_party] += flow_height

        n_points = 40
        x_vals_top = []
        y_vals_top = []
        x_vals_bottom = []
        y_vals_bottom = []

        for i in range(n_points + 1):
            t = i / n_points
            x = x_left + t * (x_right - x_left)
            ease = t * t * (3 - 2 * t)
            y_top = src_y1 + ease * (tgt_y1 - src_y1)
            y_bottom = src_y0 + ease * (tgt_y0 - src_y0)

            x_vals_top.append(x)
            y_vals_top.append(y_top)
            x_vals_bottom.append(x)
            y_vals_bottom.append(y_bottom)

        x_polygon = x_vals_top + x_vals_bottom[::-1]
        y_polygon = y_vals_top + y_vals_bottom[::-1]

        # Use destination party for coloring to show where voters went
        flow_id = f"t{time_idx}_{from_party}_{to_party}"
        flow_color_key = f"{from_party}_{to_party}"
        for x, y in zip(x_polygon, y_polygon, strict=False):
            flow_data.append(
                {
                    "x": x,
                    "y": y,
                    "flow_id": flow_id,
                    "flow_color": flow_color_key,
                    "from_party": from_party,
                    "to_party": to_party,
                }
            )


# Add flows for 2016->2020
add_flows(
    flows_2016_2020,
    0,
    node_positions[0],
    node_positions[1],
    x_positions[0] + node_width / 2,
    x_positions[1] - node_width / 2,
)

# Add flows for 2020->2024
add_flows(
    flows_2020_2024,
    1,
    node_positions[1],
    node_positions[2],
    x_positions[1] + node_width / 2,
    x_positions[2] - node_width / 2,
)

df_flows = pd.DataFrame(flow_data)

# Build node rectangles
node_rects = []
for time_idx, positions in enumerate(node_positions):
    for party in parties:
        pos = positions[party]
        node_rects.append(
            {
                "xmin": pos["x"] - node_width / 2,
                "xmax": pos["x"] + node_width / 2,
                "ymin": pos["y0"],
                "ymax": pos["y1"],
                "party": party,
                "time_idx": time_idx,
            }
        )

df_nodes = pd.DataFrame(node_rects)

# Build labels
labels = []

# Time point labels (column headers)
for i, election in enumerate(elections):
    labels.append({"x": x_positions[i], "y": 0.96, "label": election, "type": "header", "hjust": 0.5})

# Party labels at first column (left side)
for party in parties:
    pos = node_positions[0][party]
    labels.append(
        {
            "x": x_positions[0] - node_width - 0.02,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": party,
            "type": "party_left",
            "hjust": 1,
        }
    )

# Value labels at last column (right side)
for party in parties:
    pos = node_positions[2][party]
    val = totals_2024[party]
    labels.append(
        {
            "x": x_positions[2] + node_width + 0.02,
            "y": (pos["y0"] + pos["y1"]) / 2,
            "label": f"{party}\n({val}M)",
            "type": "party_right",
            "hjust": 0,
        }
    )

df_labels = pd.DataFrame(labels)

# Create the plot - flows colored by destination to show where voters went
plot = (
    ggplot()
    + geom_polygon(
        aes(x="x", y="y", group="flow_id", fill="to_party"), data=df_flows, alpha=0.55, color="white", size=0.1
    )
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="party"), data=df_nodes, color="#1A1A1A", size=1
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_labels[df_labels["type"] == "header"],
        size=18,
        hjust=0.5,
        fontface="bold",
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels[df_labels["type"] == "party_left"], size=13, hjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels[df_labels["type"] == "party_right"], size=12, hjust=0)
    + scale_fill_manual(
        values={
            "Democrats": party_colors["Democrats"],
            "Republicans": party_colors["Republicans"],
            "Independents": party_colors["Independents"],
            "Non-Voters": party_colors["Non-Voters"],
        }
    )
    + labs(title="alluvial-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + scale_x_continuous(limits=[-0.05, 1.05])
    + scale_y_continuous(limits=[-0.02, 1.02])
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
