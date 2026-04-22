""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import plotly.graph_objects as go


# Data: Voter migration between political parties across 4 election cycles
# Categories: Conservative, Liberal, Progressive, Independent
# Shows realistic voter movement patterns

# Define time points (election years)
time_points = ["2012", "2016", "2020", "2024"]

# Node labels for each time point (same categories at each stage)
categories = ["Conservative", "Liberal", "Progressive", "Independent"]
node_labels = categories * 4  # Repeat for each time point

# Define node positions
# X positions: 4 time points evenly spaced
x_positions = []
for t in range(4):
    x_positions.extend([0.01 + (t / 3) * 0.98] * 4)

# Y positions: 4 categories evenly spaced vertically (consistent order)
# Conservative at top, Liberal, Progressive, Independent at bottom
y_positions = [0.15, 0.42, 0.68, 0.92] * 4

# Colors for each category (consistent across time points)
category_colors = {
    "Conservative": "#306998",  # Python Blue
    "Liberal": "#FFD43B",  # Python Yellow
    "Progressive": "#2CA02C",  # Green
    "Independent": "#9467BD",  # Purple
}

node_colors = [category_colors[cat] for cat in node_labels]

# Define flows between time points
# Format: (source_time, source_cat, target_time, target_cat, value)
flows_data = [
    # 2012 -> 2016 transitions
    (0, 0, 1, 0, 280),  # Conservative stays Conservative
    (0, 0, 1, 3, 20),  # Conservative to Independent
    (0, 1, 1, 1, 250),  # Liberal stays Liberal
    (0, 1, 1, 2, 30),  # Liberal to Progressive
    (0, 1, 1, 3, 15),  # Liberal to Independent
    (0, 2, 1, 2, 120),  # Progressive stays Progressive
    (0, 2, 1, 1, 25),  # Progressive to Liberal
    (0, 3, 1, 3, 80),  # Independent stays Independent
    (0, 3, 1, 0, 30),  # Independent to Conservative
    (0, 3, 1, 1, 20),  # Independent to Liberal
    # 2016 -> 2020 transitions
    (1, 0, 2, 0, 260),  # Conservative stays Conservative
    (1, 0, 2, 3, 50),  # Conservative to Independent
    (1, 1, 2, 1, 240),  # Liberal stays Liberal
    (1, 1, 2, 2, 45),  # Liberal to Progressive
    (1, 2, 2, 2, 140),  # Progressive stays Progressive
    (1, 2, 2, 1, 35),  # Progressive to Liberal
    (1, 3, 2, 3, 90),  # Independent stays Independent
    (1, 3, 2, 0, 25),  # Independent to Conservative
    (1, 3, 2, 2, 15),  # Independent to Progressive
    # 2020 -> 2024 transitions
    (2, 0, 3, 0, 250),  # Conservative stays Conservative
    (2, 0, 3, 3, 35),  # Conservative to Independent
    (2, 1, 3, 1, 255),  # Liberal stays Liberal
    (2, 1, 3, 2, 40),  # Liberal to Progressive
    (2, 2, 3, 2, 160),  # Progressive stays Progressive
    (2, 2, 3, 1, 40),  # Progressive to Liberal
    (2, 3, 3, 3, 100),  # Independent stays Independent
    (2, 3, 3, 0, 20),  # Independent to Conservative
    (2, 3, 3, 1, 10),  # Independent to Liberal
]

# Convert to source/target indices and values
sources = []
targets = []
values = []
link_colors = []
link_customdata = []

for src_time, src_cat, tgt_time, tgt_cat, value in flows_data:
    src_idx = src_time * 4 + src_cat
    tgt_idx = tgt_time * 4 + tgt_cat
    sources.append(src_idx)
    targets.append(tgt_idx)
    values.append(value)
    # Custom data for hover template
    link_customdata.append(
        [categories[src_cat], time_points[src_time], categories[tgt_cat], time_points[tgt_time], value]
    )
    # Use source category color with transparency for links
    base_color = category_colors[categories[src_cat]]
    # Convert hex to rgba with transparency
    r = int(base_color[1:3], 16)
    g = int(base_color[3:5], 16)
    b = int(base_color[5:7], 16)
    link_colors.append(f"rgba({r},{g},{b},0.4)")

# Create the Sankey diagram (alluvial style)
fig = go.Figure(
    data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=30,
                thickness=35,
                line=dict(color="white", width=2),
                label=node_labels,
                color=node_colors,
                x=x_positions,
                y=y_positions,
                hovertemplate="<b>%{label}</b><br>Voters: %{value:,}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                customdata=link_customdata,
                hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                + "→ <b>%{customdata[2]}</b> (%{customdata[3]})<br>"
                + "Voters: <b>%{value:,}</b><extra></extra>",
            ),
        )
    ]
)

# Add time point labels as annotations
for i, year in enumerate(time_points):
    fig.add_annotation(
        x=i / 3, y=1.08, text=f"<b>{year}</b>", showarrow=False, font=dict(size=26, color="#333333"), xanchor="center"
    )

# Add legend using invisible scatter traces
for cat, color in category_colors.items():
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=18, color=color, symbol="square"),
            name=cat,
            showlegend=True,
        )
    )

# Update layout
fig.update_layout(
    title=dict(
        text="Voter Migration · alluvial-basic · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
        y=0.98,
    ),
    font=dict(size=18, color="#333333"),
    template="plotly_white",
    margin=dict(l=40, r=40, t=120, b=80),
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend=dict(
        orientation="h", yanchor="bottom", y=-0.06, xanchor="center", x=0.5, font=dict(size=18), itemsizing="constant"
    ),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
