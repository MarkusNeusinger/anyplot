""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Energy flow from sources to end-use sectors (in TWh)
sources = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
targets = ["Residential", "Commercial", "Industrial", "Transportation"]

# Node labels (sources first, then targets)
labels = sources + targets

# Define flows: (source_index, target_index, value)
# Indices: Coal=0, Gas=1, Nuclear=2, Renewables=3
# Residential=4, Commercial=5, Industrial=6, Transportation=7
flows = [
    # Coal flows
    (0, 4, 5),  # Coal -> Residential
    (0, 5, 8),  # Coal -> Commercial
    (0, 6, 25),  # Coal -> Industrial
    # Natural Gas flows
    (1, 4, 22),  # Gas -> Residential
    (1, 5, 18),  # Gas -> Commercial
    (1, 6, 15),  # Gas -> Industrial
    (1, 7, 3),  # Gas -> Transportation
    # Nuclear flows
    (2, 4, 12),  # Nuclear -> Residential
    (2, 5, 10),  # Nuclear -> Commercial
    (2, 6, 8),  # Nuclear -> Industrial
    # Renewables flows
    (3, 4, 8),  # Renewables -> Residential
    (3, 5, 6),  # Renewables -> Commercial
    (3, 6, 5),  # Renewables -> Industrial
    (3, 7, 4),  # Renewables -> Transportation
]

source_indices = [f[0] for f in flows]
target_indices = [f[1] for f in flows]
values = [f[2] for f in flows]

# Colors for source nodes (Python Blue variations and Yellow)
node_colors = [
    "#306998",  # Coal - Python Blue
    "#4A90C2",  # Natural Gas - Light Blue
    "#FFD43B",  # Nuclear - Python Yellow
    "#7AB648",  # Renewables - Green
    "#8FA8BD",  # Residential
    "#A3B8CC",  # Commercial
    "#B8C9DB",  # Industrial
    "#CCD9E8",  # Transportation
]

# Link colors with transparency (based on source)
link_colors = [
    "rgba(48, 105, 152, 0.5)"
    if s == 0
    else "rgba(74, 144, 194, 0.5)"
    if s == 1
    else "rgba(255, 212, 59, 0.5)"
    if s == 2
    else "rgba(122, 182, 72, 0.5)"
    for s in source_indices
]

# Create Sankey diagram
fig = go.Figure(
    data=[
        go.Sankey(
            node=dict(pad=25, thickness=35, line=dict(color="white", width=2), label=labels, color=node_colors),
            link=dict(source=source_indices, target=target_indices, value=values, color=link_colors),
        )
    ]
)

# Update layout for 4800x2700 px output
fig.update_layout(
    title=dict(
        text="Energy Distribution · sankey-basic · plotly · pyplots.ai", font=dict(size=36), x=0.5, xanchor="center"
    ),
    font=dict(size=22),
    template="plotly_white",
    margin=dict(l=80, r=80, t=120, b=60),
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
