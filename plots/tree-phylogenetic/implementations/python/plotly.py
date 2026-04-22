""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import plotly.graph_objects as go


# Primate phylogenetic tree based on mitochondrial DNA divergence
# Newick format: ((((Human:0.1,Chimpanzee:0.1):0.05,Gorilla:0.15):0.1,Orangutan:0.25):0.15,Gibbon:0.4);

# Species and their evolutionary distances from root
species = ["Human", "Chimpanzee", "Gorilla", "Orangutan", "Gibbon"]

# Cumulative distances from root (calculated from tree topology)
# Root -> African_ape (0.15) -> HCG_ancestor (0.1) -> HC_ancestor (0.05) -> Human/Chimp (0.1)
distances_from_root = {
    "Human": 0.15 + 0.1 + 0.05 + 0.1,  # 0.4
    "Chimpanzee": 0.15 + 0.1 + 0.05 + 0.1,  # 0.4
    "Gorilla": 0.15 + 0.1 + 0.15,  # 0.4
    "Orangutan": 0.15 + 0.25,  # 0.4
    "Gibbon": 0.4,  # 0.4
}

# Internal node positions (x = distance from root)
internal_x = {"Root": 0.0, "African_ape": 0.15, "HCG_ancestor": 0.25, "HC_ancestor": 0.30}

# Y positions for species (leaf nodes)
species_y = {"Human": 5, "Chimpanzee": 4, "Gorilla": 3, "Orangutan": 2, "Gibbon": 1}

# Y positions for internal nodes (average of children)
internal_y = {
    "HC_ancestor": (species_y["Human"] + species_y["Chimpanzee"]) / 2,
    "HCG_ancestor": (species_y["Human"] + species_y["Chimpanzee"] + species_y["Gorilla"]) / 3,
    "African_ape": (species_y["Human"] + species_y["Chimpanzee"] + species_y["Gorilla"] + species_y["Orangutan"]) / 4,
    "Root": 3,
}

# Build edges for rectangular phylogram
edge_x = []
edge_y = []

# Tree structure connections (child, parent)
connections = [
    ("Human", "HC_ancestor"),
    ("Chimpanzee", "HC_ancestor"),
    ("HC_ancestor", "HCG_ancestor"),
    ("Gorilla", "HCG_ancestor"),
    ("HCG_ancestor", "African_ape"),
    ("Orangutan", "African_ape"),
    ("African_ape", "Root"),
    ("Gibbon", "Root"),
]

# Create edge traces for rectangular phylogram
for child, parent in connections:
    # Get child position
    child_x = distances_from_root[child] if child in species else internal_x[child]
    child_y = species_y[child] if child in species else internal_y[child]

    # Get parent position
    parent_x = internal_x[parent]
    parent_y = internal_y[parent]

    # Horizontal line from child to parent x position
    edge_x.extend([child_x, parent_x, None])
    edge_y.extend([child_y, child_y, None])

    # Vertical line at parent x position
    edge_x.extend([parent_x, parent_x, None])
    edge_y.extend([child_y, parent_y, None])

# Create figure
fig = go.Figure()

# Add branch lines (edges)
fig.add_trace(
    go.Scatter(
        x=edge_x, y=edge_y, mode="lines", line={"color": "#306998", "width": 3}, hoverinfo="skip", showlegend=False
    )
)

# Add leaf nodes (species)
leaf_x = [distances_from_root[s] for s in species]
leaf_y = [species_y[s] for s in species]

fig.add_trace(
    go.Scatter(
        x=leaf_x,
        y=leaf_y,
        mode="markers+text",
        marker={"size": 18, "color": "#FFD43B", "line": {"width": 2, "color": "#306998"}},
        text=species,
        textposition="middle right",
        textfont={"size": 20, "color": "#333333"},
        hovertemplate="%{text}<br>Distance: %{x:.2f}<extra></extra>",
        showlegend=False,
    )
)

# Add internal nodes
internal_nodes_x = list(internal_x.values())
internal_nodes_y = [internal_y.get(n, 3) for n in internal_x.keys()]
internal_labels = list(internal_x.keys())

fig.add_trace(
    go.Scatter(
        x=internal_nodes_x,
        y=internal_nodes_y,
        mode="markers",
        marker={"size": 12, "color": "#306998", "symbol": "circle"},
        hovertemplate="%{text}<br>Distance: %{x:.2f}<extra></extra>",
        text=internal_labels,
        showlegend=False,
    )
)

# Add scale bar
scale_bar_y = 0.3
scale_bar_length = 0.1
fig.add_trace(
    go.Scatter(
        x=[0, scale_bar_length],
        y=[scale_bar_y, scale_bar_y],
        mode="lines",
        line={"color": "#333333", "width": 3},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Scale bar label
fig.add_annotation(
    x=scale_bar_length / 2,
    y=scale_bar_y - 0.15,
    text="0.1 substitutions/site",
    showarrow=False,
    font={"size": 16, "color": "#333333"},
)

# Update layout
fig.update_layout(
    title={
        "text": "Primate Evolution · tree-phylogenetic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Evolutionary Distance (substitutions per site)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.05, 0.55],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 6],
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 150, "t": 100, "b": 100},
    showlegend=False,
)

# Add clade annotations
fig.add_annotation(
    x=0.32,
    y=4.5,
    text="Hominini",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#888888",
    ax=40,
    ay=0,
    font={"size": 16, "color": "#555555", "style": "italic"},
)

fig.add_annotation(
    x=0.27,
    y=3.8,
    text="Homininae<br>(African Apes)",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#888888",
    ax=50,
    ay=-20,
    font={"size": 16, "color": "#555555", "style": "italic"},
)

fig.add_annotation(
    x=0.17,
    y=2.8,
    text="Hominidae<br>(Great Apes)",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#888888",
    ax=50,
    ay=-30,
    font={"size": 16, "color": "#555555", "style": "italic"},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
