""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-09
"""

import os

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

np.random.seed(42)

# Data: Voter migration between political parties across 4 election cycles
years = ["2012", "2016", "2020", "2024"]
parties = ["Democratic", "Republican", "Independent", "Other"]

# Map parties to Okabe-Ito colors
party_colors = {
    "Democratic": IMPRINT[0],  # #009E73 (brand green)
    "Republican": IMPRINT[1],  # #C475FD (vermillion)
    "Independent": IMPRINT[2],  # #4467A3 (blue)
    "Other": IMPRINT[3],  # #BD8233 (reddish purple)
}

# Voter counts (millions) at each time point
voter_counts = np.array(
    [
        [65.9, 65.8, 81.3, 72.0],  # Democratic
        [60.9, 63.0, 74.2, 77.0],  # Republican
        [8.5, 7.8, 5.2, 6.5],  # Independent
        [3.0, 4.5, 2.8, 3.5],  # Other
    ]
)

# Flow matrix between consecutive years (transitions between parties)
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

# Custom style for text elements
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
)

# Create minimal chart just for title rendering
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="alluvial-basic·pygal·anyplot.ai",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    dots_size=0,
    stroke=False,
    range=(0, 100),
    xrange=(0, 100),
)

# Add empty data to avoid "No data" message
chart.add("", [(50, 50)])

# Render base SVG
base_svg = chart.render().decode("utf-8")

# SVG coordinate mapping
margin_left = 600
margin_right = 600
margin_top = 400
margin_bottom = 350
chart_width = 4800 - margin_left - margin_right
chart_height = 2700 - margin_top - margin_bottom

# Calculate positions for each time point
n_years = len(years)
x_positions = [margin_left + i * chart_width / (n_years - 1) for i in range(n_years)]
bar_width = 150
total_height = chart_height

# Track node positions
node_positions = {}

# Build SVG elements for nodes and flows
alluvial_svg = '<g id="alluvial-diagram">'

# Calculate node positions and draw bars
for year_idx, year in enumerate(years):
    x = x_positions[year_idx]
    year_total = voter_counts[:, year_idx].sum()

    y_top = margin_top
    for party_idx, party in enumerate(parties):
        height = (voter_counts[party_idx, year_idx] / year_total) * total_height
        y_bottom = y_top + height

        # Store position for flow drawing
        node_positions[(year_idx, party)] = (y_top, y_bottom)

        # Draw rectangle for this party at this year
        alluvial_svg += f'''
    <rect x="{x - bar_width / 2:.0f}" y="{y_top:.0f}" width="{bar_width:.0f}" height="{height:.0f}"
          fill="{party_colors[party]}" stroke="{PAGE_BG}" stroke-width="3"/>'''

        y_top = y_bottom

    # Add year label at bottom
    alluvial_svg += f'''
    <text x="{x:.0f}" y="{margin_top + total_height + 80:.0f}" text-anchor="middle"
          font-size="52" font-weight="bold" font-family="sans-serif"
          fill="{INK}">{year}</text>'''

# Add party labels on left side
for party in parties:
    y_top, y_bottom = node_positions[(0, party)]
    y_center = (y_top + y_bottom) / 2
    alluvial_svg += f'''
    <text x="{x_positions[0] - bar_width / 2 - 30:.0f}" y="{y_center:.0f}" text-anchor="end"
          font-size="44" font-weight="bold" font-family="sans-serif"
          fill="{party_colors[party]}" dominant-baseline="middle">{party}</text>'''

# Add party labels on right side
for party in parties:
    y_top, y_bottom = node_positions[(n_years - 1, party)]
    y_center = (y_top + y_bottom) / 2
    alluvial_svg += f'''
    <text x="{x_positions[-1] + bar_width / 2 + 30:.0f}" y="{y_center:.0f}" text-anchor="start"
          font-size="44" font-weight="bold" font-family="sans-serif"
          fill="{party_colors[party]}" dominant-baseline="middle">{party}</text>'''

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
        y0_top = source_offsets[source_party]
        y0_bottom = y0_top + source_height
        y1_top = target_offsets[target_party]
        y1_bottom = y1_top + target_height

        # Bezier curve control points
        band_x0 = x0 + bar_width / 2
        band_x1 = x1 - bar_width / 2
        cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
        cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

        # Create path for the curved band
        path_d = (
            f"M {band_x0:.0f},{y0_top:.0f} "
            f"C {cx0:.0f},{y0_top:.0f} {cx1:.0f},{y1_top:.0f} {band_x1:.0f},{y1_top:.0f} "
            f"L {band_x1:.0f},{y1_bottom:.0f} "
            f"C {cx1:.0f},{y1_bottom:.0f} {cx0:.0f},{y0_bottom:.0f} {band_x0:.0f},{y0_bottom:.0f} "
            f"Z"
        )

        alluvial_svg += f'''
    <path d="{path_d}" fill="{party_colors[source_party]}" fill-opacity="0.35" stroke="none"/>'''

        # Update offsets
        source_offsets[source_party] = y0_bottom
        target_offsets[target_party] = y1_bottom

# Add subtitle explaining the visualization
subtitle_y = margin_top + total_height + 150
alluvial_svg += f'''
    <text x="2400" y="{subtitle_y:.0f}" text-anchor="middle"
          font-size="42" font-style="italic" font-family="sans-serif"
          fill="{INK_SOFT}">Voter Migration Between Political Parties (Millions of Voters)</text>'''

alluvial_svg += "\n</g>"

# Insert alluvial elements before closing </svg> tag
svg_with_alluvial = base_svg.replace("</svg>", f"{alluvial_svg}\n</svg>")

# Save outputs
cairosvg.svg2png(bytestring=svg_with_alluvial.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(
        """<!DOCTYPE html>
<html>
<head>
    <title>alluvial-basic·pygal·anyplot.ai</title>
    <style>
        body { margin: 0; padding: 20px; background: """
        + ("#f5f5f5" if THEME == "light" else "#2a2a2a")
        + """; font-family: sans-serif; }
        .container { max-width: 100%; margin: 0 auto; }
        object { width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot-"""
        + THEME
        + """.svg">
            Alluvial diagram not supported
        </object>
    </div>
</body>
</html>"""
    )
