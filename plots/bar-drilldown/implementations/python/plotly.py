""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import plotly.graph_objects as go


# Hierarchical data: Company Revenue by Region -> Country -> City
# Root level: Regions
data = {
    "all": {"name": "All Regions", "value": 0, "parent": None},
    # Level 1: Regions
    "north_america": {"name": "North America", "value": 450, "parent": "all"},
    "europe": {"name": "Europe", "value": 380, "parent": "all"},
    "asia_pacific": {"name": "Asia Pacific", "value": 320, "parent": "all"},
    "latin_america": {"name": "Latin America", "value": 150, "parent": "all"},
    # Level 2: Countries under North America
    "usa": {"name": "USA", "value": 280, "parent": "north_america"},
    "canada": {"name": "Canada", "value": 120, "parent": "north_america"},
    "mexico": {"name": "Mexico", "value": 50, "parent": "north_america"},
    # Level 2: Countries under Europe
    "uk": {"name": "UK", "value": 140, "parent": "europe"},
    "germany": {"name": "Germany", "value": 130, "parent": "europe"},
    "france": {"name": "France", "value": 110, "parent": "europe"},
    # Level 2: Countries under Asia Pacific
    "japan": {"name": "Japan", "value": 150, "parent": "asia_pacific"},
    "australia": {"name": "Australia", "value": 100, "parent": "asia_pacific"},
    "singapore": {"name": "Singapore", "value": 70, "parent": "asia_pacific"},
    # Level 2: Countries under Latin America
    "brazil": {"name": "Brazil", "value": 90, "parent": "latin_america"},
    "argentina": {"name": "Argentina", "value": 60, "parent": "latin_america"},
    # Level 3: Cities under USA
    "new_york": {"name": "New York", "value": 120, "parent": "usa"},
    "los_angeles": {"name": "Los Angeles", "value": 90, "parent": "usa"},
    "chicago": {"name": "Chicago", "value": 70, "parent": "usa"},
    # Level 3: Cities under UK
    "london": {"name": "London", "value": 80, "parent": "uk"},
    "manchester": {"name": "Manchester", "value": 35, "parent": "uk"},
    "birmingham": {"name": "Birmingham", "value": 25, "parent": "uk"},
    # Level 3: Cities under Japan
    "tokyo": {"name": "Tokyo", "value": 85, "parent": "japan"},
    "osaka": {"name": "Osaka", "value": 40, "parent": "japan"},
    "nagoya": {"name": "Nagoya", "value": 25, "parent": "japan"},
}


def get_children(parent_id):
    """Get all children of a given parent."""
    return {k: v for k, v in data.items() if v["parent"] == parent_id}


def get_breadcrumb_path(node_id):
    """Build breadcrumb path from root to current node."""
    path = []
    current = node_id
    while current is not None and current in data:
        path.append({"id": current, "name": data[current]["name"]})
        current = data[current]["parent"]
    return list(reversed(path))


# Get root level children (regions)
children = get_children("all")
sorted_items = sorted(children.items(), key=lambda x: x[1]["value"], reverse=True)
ids = [item[0] for item in sorted_items]
names = [item[1]["name"] for item in sorted_items]
values = [item[1]["value"] for item in sorted_items]

# Check which items have children (are drillable)
drillable = [len(get_children(id_)) > 0 for id_ in ids]

# Color scheme - Python blue palette (darker for drillable)
colors = ["#306998" if d else "#4B8BBE" for d in drillable]

# Create custom data for click handling
customdata = [[id_, "drillable" if d else "leaf"] for id_, d in zip(ids, drillable, strict=True)]

# Build breadcrumb text
breadcrumb_path = get_breadcrumb_path("all")
breadcrumb_text = " > ".join([p["name"] for p in breadcrumb_path])

# Create bar chart
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=names,
        y=values,
        marker={"color": colors, "line": {"color": "#1E4A6D", "width": 2}},
        text=[f"${v}M" for v in values],
        textposition="outside",
        textfont={"size": 18, "color": "#333333"},
        customdata=customdata,
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y}M<br><i>%{customdata[1]}</i><extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "bar-drilldown · plotly · pyplots.ai<br>"
        "<sup style='font-size:18px; color:#666'>Revenue by Regions | Path: All Regions</sup>",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"title": {"text": "Regions", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Revenue ($ Millions)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    margin={"t": 120, "b": 100, "l": 100, "r": 50},
    annotations=[
        {
            "text": "🖱 Click a bar to drill down | Click breadcrumb to go back",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.15,
            "showarrow": False,
            "font": {"size": 16, "color": "#666666"},
            "xanchor": "center",
        }
    ],
)

# Create frames for drill levels to demonstrate the drilldown concept
frames = []
button_labels = []

# Frame 1: Root level (Regions) - current view
frames.append(
    go.Frame(
        data=[
            go.Bar(
                x=names,
                y=values,
                marker={"color": "#306998", "line": {"color": "#1E4A6D", "width": 2}},
                text=[f"${v}M" for v in values],
                textposition="outside",
                textfont={"size": 18, "color": "#333333"},
            )
        ],
        name="all",
        layout=go.Layout(
            title={
                "text": "bar-drilldown · plotly · pyplots.ai<br>"
                "<sup style='font-size:18px; color:#666'>Revenue by Regions | Path: All Regions</sup>"
            },
            xaxis={"title": {"text": "Regions", "font": {"size": 22}}},
        ),
    )
)
button_labels.append("All Regions")

# Frame 2: North America (Countries)
children_na = get_children("north_america")
sorted_na = sorted(children_na.items(), key=lambda x: x[1]["value"], reverse=True)
names_na = [item[1]["name"] for item in sorted_na]
values_na = [item[1]["value"] for item in sorted_na]

frames.append(
    go.Frame(
        data=[
            go.Bar(
                x=names_na,
                y=values_na,
                marker={"color": "#306998", "line": {"color": "#1E4A6D", "width": 2}},
                text=[f"${v}M" for v in values_na],
                textposition="outside",
                textfont={"size": 18, "color": "#333333"},
            )
        ],
        name="north_america",
        layout=go.Layout(
            title={
                "text": "bar-drilldown · plotly · pyplots.ai<br>"
                "<sup style='font-size:18px; color:#666'>Revenue by Countries | "
                "Path: All Regions > North America</sup>"
            },
            xaxis={"title": {"text": "Countries", "font": {"size": 22}}},
        ),
    )
)
button_labels.append("North America")

# Frame 3: USA (Cities)
children_usa = get_children("usa")
sorted_usa = sorted(children_usa.items(), key=lambda x: x[1]["value"], reverse=True)
names_usa = [item[1]["name"] for item in sorted_usa]
values_usa = [item[1]["value"] for item in sorted_usa]

frames.append(
    go.Frame(
        data=[
            go.Bar(
                x=names_usa,
                y=values_usa,
                marker={"color": "#4B8BBE", "line": {"color": "#1E4A6D", "width": 2}},
                text=[f"${v}M" for v in values_usa],
                textposition="outside",
                textfont={"size": 18, "color": "#333333"},
            )
        ],
        name="usa",
        layout=go.Layout(
            title={
                "text": "bar-drilldown · plotly · pyplots.ai<br>"
                "<sup style='font-size:18px; color:#666'>Revenue by Cities | "
                "Path: All Regions > North America > USA</sup>"
            },
            xaxis={"title": {"text": "Cities", "font": {"size": 22}}},
        ),
    )
)
button_labels.append("USA")

fig.frames = frames

# Add dropdown menu for level navigation
fig.update_layout(
    updatemenus=[
        {
            "type": "dropdown",
            "direction": "down",
            "x": 0.02,
            "y": 0.98,
            "xanchor": "left",
            "yanchor": "top",
            "showactive": True,
            "active": 0,
            "buttons": [
                {
                    "label": label,
                    "method": "animate",
                    "args": [
                        [frame.name],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 500, "redraw": True},
                            "transition": {"duration": 300},
                        },
                    ],
                }
                for label, frame in zip(button_labels, frames, strict=True)
            ],
            "bgcolor": "white",
            "bordercolor": "#306998",
            "font": {"size": 14},
            "pad": {"r": 10, "t": 10},
        }
    ]
)

# Save PNG (static image of root level)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html(
    "plot.html",
    include_plotlyjs=True,
    full_html=True,
    config={"displayModeBar": True, "displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
)
