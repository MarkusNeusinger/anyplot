""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Hierarchical data: Company budget allocation (in thousands)
# Structure: Company -> Departments -> Teams -> Projects

# Build hierarchy using labels and parents approach (like treemap-basic)
labels = ["Company"]
parents = [""]
values = [9600]  # Total budget

# Department data
departments = [("Engineering", 4500), ("Marketing", 2100), ("Sales", 1800), ("Operations", 1200)]

for dept_name, dept_budget in departments:
    labels.append(dept_name)
    parents.append("Company")
    values.append(dept_budget)

# Teams within departments
teams_data = [
    # Engineering teams
    ("Backend", "Engineering", 1800),
    ("Frontend", "Engineering", 1200),
    ("Data Science", "Engineering", 900),
    ("DevOps", "Engineering", 600),
    # Marketing teams
    ("Digital", "Marketing", 900),
    ("Brand", "Marketing", 600),
    ("Content", "Marketing", 600),
    # Sales teams
    ("Enterprise", "Sales", 1000),
    ("SMB", "Sales", 500),
    ("Partners", "Sales", 300),
    # Operations teams
    ("IT", "Operations", 500),
    ("HR", "Operations", 400),
    ("Finance", "Operations", 300),
]

for team_name, parent_dept, team_budget in teams_data:
    labels.append(team_name)
    parents.append(parent_dept)
    values.append(team_budget)

# Color mapping - consistent across both views
color_map = {
    "Company": "#FFFFFF",
    "Engineering": "#306998",
    "Marketing": "#FFD43B",
    "Sales": "#2CA02C",
    "Operations": "#9467BD",
}

# Assign colors based on department hierarchy
colors = []
for i, label in enumerate(labels):
    if label in color_map:
        colors.append(color_map[label])
    else:
        # Team/project - use parent department color
        parent = parents[i]
        colors.append(color_map.get(parent, "#306998"))

# Create side-by-side figure showing both views
fig = make_subplots(rows=1, cols=2, specs=[[{"type": "treemap"}, {"type": "sunburst"}]], horizontal_spacing=0.03)

# Treemap trace
fig.add_trace(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": "white"}},
        textfont={"size": 20},
        textinfo="label+value",
        texttemplate="%{label}<br>$%{value}K",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
    ),
    row=1,
    col=1,
)

# Sunburst trace
fig.add_trace(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": "white"}},
        textfont={"size": 16},
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        insidetextorientation="radial",
    ),
    row=1,
    col=2,
)

# Update layout
fig.update_layout(
    title={
        "text": "Company Budget · hierarchy-toggle-view · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    margin={"t": 100, "l": 20, "r": 20, "b": 80},
    annotations=[
        {
            "text": "Treemap View",
            "x": 0.22,
            "y": 1.02,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 24, "color": "#333"},
        },
        {
            "text": "Sunburst View",
            "x": 0.78,
            "y": 1.02,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 24, "color": "#333"},
        },
        {
            "text": "Two perspectives: rectangles for size comparison, radial for hierarchy depth",
            "x": 0.5,
            "y": -0.03,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 18, "color": "#666"},
        },
    ],
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Interactive HTML with toggle buttons
fig_interactive = go.Figure()

fig_interactive.add_trace(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": "white"}},
        textfont={"size": 22},
        textinfo="label+value",
        texttemplate="%{label}<br>$%{value}K",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        visible=True,
    )
)

fig_interactive.add_trace(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"width": 2, "color": "white"}},
        textfont={"size": 18},
        textinfo="label",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}K<br>Percent: %{percentParent:.1%}<extra></extra>",
        visible=False,
        insidetextorientation="radial",
    )
)

fig_interactive.update_layout(
    title={
        "text": "Company Budget · hierarchy-toggle-view · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    margin={"t": 120, "l": 30, "r": 30, "b": 50},
    updatemenus=[
        {
            "type": "buttons",
            "direction": "right",
            "x": 0.5,
            "xanchor": "center",
            "y": 1.08,
            "buttons": [
                {"label": "  Treemap  ", "method": "update", "args": [{"visible": [True, False]}]},
                {"label": "  Sunburst  ", "method": "update", "args": [{"visible": [False, True]}]},
            ],
            "font": {"size": 18},
            "bgcolor": "white",
            "bordercolor": "#306998",
            "borderwidth": 2,
        }
    ],
)

fig_interactive.write_html("plot.html", include_plotlyjs="cdn")
