""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.path import Path


# Set seaborn style for consistent aesthetics
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data: Voter migration across 4 election cycles
np.random.seed(42)

# Define time points (election years) and political parties
years = ["2012", "2016", "2020", "2024"]
parties = ["Democratic", "Republican", "Independent", "Other"]

# Colors for each party - using seaborn's colorblind-safe palette
palette = sns.color_palette("colorblind", n_colors=8)
party_colors = {
    "Democratic": palette[0],  # Blue
    "Republican": palette[3],  # Red
    "Independent": palette[2],  # Green
    "Other": palette[7],  # Gray
}

# Voter counts (millions) at each time point
# Rows = parties, Columns = years
voter_counts = np.array(
    [
        [65.9, 65.8, 81.3, 72.0],  # Democratic
        [60.9, 63.0, 74.2, 77.0],  # Republican
        [8.5, 7.8, 5.2, 6.5],  # Independent
        [3.0, 4.5, 2.8, 3.5],  # Other
    ]
)

# Flow matrix between consecutive years (transitions between parties)
# This represents how voters moved between parties
flows = [
    # 2012 -> 2016
    {
        ("Democratic", "Democratic"): 58.0,
        ("Democratic", "Republican"): 4.5,
        ("Democratic", "Independent"): 2.5,
        ("Democratic", "Other"): 0.9,
        ("Republican", "Republican"): 55.0,
        ("Republican", "Democratic"): 3.0,
        ("Republican", "Independent"): 1.5,
        ("Republican", "Other"): 1.4,
        ("Independent", "Democratic"): 3.2,
        ("Independent", "Republican"): 2.8,
        ("Independent", "Independent"): 2.0,
        ("Independent", "Other"): 0.5,
        ("Other", "Democratic"): 1.6,
        ("Other", "Republican"): 0.7,
        ("Other", "Independent"): 0.3,
        ("Other", "Other"): 0.4,
    },
    # 2016 -> 2020
    {
        ("Democratic", "Democratic"): 60.0,
        ("Democratic", "Republican"): 2.5,
        ("Democratic", "Independent"): 2.0,
        ("Democratic", "Other"): 1.3,
        ("Republican", "Republican"): 58.0,
        ("Republican", "Democratic"): 3.5,
        ("Republican", "Independent"): 1.0,
        ("Republican", "Other"): 0.5,
        ("Independent", "Democratic"): 5.5,
        ("Independent", "Republican"): 1.5,
        ("Independent", "Independent"): 0.5,
        ("Independent", "Other"): 0.3,
        ("Other", "Democratic"): 2.0,
        ("Other", "Republican"): 1.5,
        ("Other", "Independent"): 0.5,
        ("Other", "Other"): 0.5,
    },
    # 2020 -> 2024
    {
        ("Democratic", "Democratic"): 65.0,
        ("Democratic", "Republican"): 10.0,
        ("Democratic", "Independent"): 4.5,
        ("Democratic", "Other"): 1.8,
        ("Republican", "Republican"): 62.0,
        ("Republican", "Democratic"): 5.5,
        ("Republican", "Independent"): 1.2,
        ("Republican", "Other"): 0.5,
        ("Independent", "Democratic"): 1.0,
        ("Independent", "Republican"): 3.0,
        ("Independent", "Independent"): 0.7,
        ("Independent", "Other"): 0.5,
        ("Other", "Democratic"): 0.5,
        ("Other", "Republican"): 2.0,
        ("Other", "Independent"): 0.1,
        ("Other", "Other"): 0.7,
    },
]


# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate positions for each time point
n_years = len(years)
x_positions = np.linspace(0, 10, n_years)
bar_width = 0.6
total_height = 100  # Normalize to percentage

# Track positions for each node (party at each time point)
node_positions = {}  # {(year_idx, party): (y_bottom, y_top)}

# Draw nodes (stacked bars) at each time point
for year_idx, year in enumerate(years):
    x = x_positions[year_idx]
    year_total = voter_counts[:, year_idx].sum()

    y_bottom = 0
    for party_idx, party in enumerate(parties):
        height = (voter_counts[party_idx, year_idx] / year_total) * total_height
        y_top = y_bottom + height

        # Store position for flow drawing
        node_positions[(year_idx, party)] = (y_bottom, y_top)

        # Draw the bar segment using seaborn's color palette styling
        rect = mpatches.Rectangle(
            (x - bar_width / 2, y_bottom),
            bar_width,
            height,
            facecolor=party_colors[party],
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)

        # Add party labels with voter counts on both first and last columns
        vote_millions = voter_counts[party_idx, year_idx]
        # Use compact format: "Party (XM)" on single line
        label_text = f"{party} ({vote_millions:.0f}M)"
        font_size = 13

        if year_idx == 0:
            ax.text(
                x - bar_width / 2 - 0.15,
                (y_bottom + y_top) / 2,
                label_text,
                ha="right",
                va="center",
                fontsize=font_size,
                fontweight="bold",
                color=party_colors[party],
            )
        elif year_idx == n_years - 1:
            ax.text(
                x + bar_width / 2 + 0.15,
                (y_bottom + y_top) / 2,
                label_text,
                ha="left",
                va="center",
                fontsize=font_size,
                fontweight="bold",
                color=party_colors[party],
            )

        y_bottom = y_top

    # Add year labels with total voters at top
    year_total_display = voter_counts[:, year_idx].sum()
    ax.text(
        x,
        total_height + 3,
        f"{year}\n({year_total_display:.1f}M total)",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
    )

# Draw flows between consecutive time points
for flow_idx, flow_dict in enumerate(flows):
    x0 = x_positions[flow_idx]
    x1 = x_positions[flow_idx + 1]

    # Calculate totals for normalization
    year0_total = voter_counts[:, flow_idx].sum()
    year1_total = voter_counts[:, flow_idx + 1].sum()

    # Track cumulative offsets for each source and target
    source_offsets = {party: node_positions[(flow_idx, party)][0] for party in parties}
    target_offsets = {party: node_positions[(flow_idx + 1, party)][0] for party in parties}

    # Draw each flow
    for (source_party, target_party), flow_value in flow_dict.items():
        if flow_value <= 0:
            continue

        # Calculate normalized heights
        source_height = (flow_value / year0_total) * total_height
        target_height = (flow_value / year1_total) * total_height

        # Get current positions
        y0_bot = source_offsets[source_party]
        y0_top = y0_bot + source_height
        y1_bot = target_offsets[target_party]
        y1_top = y1_bot + target_height

        # Draw the curved band with source color using Bezier curves
        band_x0 = x0 + bar_width / 2
        band_x1 = x1 - bar_width / 2
        cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
        cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

        verts = [
            (band_x0, y0_bot),
            (cx0, y0_bot),
            (cx1, y1_bot),
            (band_x1, y1_bot),
            (band_x1, y1_top),
            (cx1, y1_top),
            (cx0, y0_top),
            (band_x0, y0_top),
            (band_x0, y0_bot),
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
        # Increase alpha for smaller flows to improve visibility
        min_height = min(source_height, target_height)
        alpha = 0.55 if min_height < 3 else 0.40
        patch = mpatches.PathPatch(
            path, facecolor=party_colors[source_party], edgecolor=party_colors[source_party], linewidth=0.5, alpha=alpha
        )
        ax.add_patch(patch)

        # Update offsets
        source_offsets[source_party] = y0_top
        target_offsets[target_party] = y1_top

# Styling
ax.set_xlim(-2.8, 13.3)
ax.set_ylim(-8, 120)
ax.set_aspect("auto")

# Remove axes
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.set_facecolor("white")
fig.patch.set_facecolor("white")

# Title (strictly following spec-id · library · pyplots.ai format)
ax.set_title("alluvial-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=25)

# Add subtitle with data context and scale information
ax.text(
    5,
    -5,
    "US Voter Migration 2012-2024 | Values in millions | Flow width proportional to transitions",
    ha="center",
    va="top",
    fontsize=14,
    color="#666666",
    style="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
