""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-15
"""

import plotly.graph_objects as go


# Data - synthetic sedimentary section with 10 layers
layers = [
    {"top": 0, "bottom": 15, "lithology": "Sandstone", "formation": "Dakota Fm", "age": "Late Cretaceous"},
    {"top": 15, "bottom": 30, "lithology": "Shale", "formation": "Graneros Sh", "age": "Late Cretaceous"},
    {"top": 30, "bottom": 50, "lithology": "Limestone", "formation": "Greenhorn Ls", "age": "Late Cretaceous"},
    {"top": 50, "bottom": 62, "lithology": "Shale", "formation": "Carlile Sh", "age": "Late Cretaceous"},
    {"top": 62, "bottom": 78, "lithology": "Siltstone", "formation": "Niobrara Fm", "age": "Late Cretaceous"},
    {"top": 78, "bottom": 100, "lithology": "Limestone", "formation": "Fort Hays Ls", "age": "Late Cretaceous"},
    {"top": 100, "bottom": 125, "lithology": "Sandstone", "formation": "Fox Hills Ss", "age": "Maastrichtian"},
    {"top": 125, "bottom": 148, "lithology": "Conglomerate", "formation": "Lance Fm", "age": "Maastrichtian"},
    {"top": 148, "bottom": 170, "lithology": "Shale", "formation": "Fort Union Fm", "age": "Paleocene"},
    {"top": 170, "bottom": 195, "lithology": "Sandstone", "formation": "Wasatch Fm", "age": "Eocene"},
]

lithology_styles = {
    "Sandstone": {"color": "#F5DEB3", "pattern_shape": ".", "pattern_size": 8},
    "Shale": {"color": "#8B8682", "pattern_shape": "-", "pattern_size": 6},
    "Limestone": {"color": "#87CEEB", "pattern_shape": "+", "pattern_size": 8},
    "Siltstone": {"color": "#C4A882", "pattern_shape": "/", "pattern_size": 6},
    "Conglomerate": {"color": "#D2691E", "pattern_shape": "x", "pattern_size": 10},
}

# Plot
fig = go.Figure()

for layer in layers:
    style = lithology_styles[layer["lithology"]]
    thickness = layer["bottom"] - layer["top"]
    mid_depth = (layer["top"] + layer["bottom"]) / 2

    fig.add_trace(
        go.Bar(
            x=[1],
            y=[thickness],
            base=layer["top"],
            orientation="v",
            marker={
                "color": style["color"],
                "pattern": {
                    "shape": style["pattern_shape"],
                    "size": style["pattern_size"],
                    "solidity": 0.6,
                    "fgcolor": "rgba(0,0,0,0.5)",
                },
                "line": {"color": "black", "width": 1.5},
            },
            width=0.6,
            showlegend=False,
            hovertemplate=(
                f"<b>{layer['formation']}</b><br>"
                f"Lithology: {layer['lithology']}<br>"
                f"Depth: {layer['top']}–{layer['bottom']} m<br>"
                f"Age: {layer['age']}"
                "<extra></extra>"
            ),
        )
    )

    # Formation name annotation (right side)
    fig.add_annotation(
        x=1.42,
        y=mid_depth,
        text=f"<b>{layer['formation']}</b><br><i>{layer['lithology']}</i>",
        showarrow=False,
        font={"size": 13},
        xanchor="left",
        yanchor="middle",
    )

# Group consecutive layers by age for left-side labels
age_groups = []
current_age = layers[0]["age"]
current_top = layers[0]["top"]
prev_bottom = layers[0]["bottom"]
for layer in layers:
    if layer["age"] != current_age:
        age_groups.append({"age": current_age, "top": current_top, "bottom": prev_bottom})
        current_age = layer["age"]
        current_top = layer["top"]
    prev_bottom = layer["bottom"]
age_groups.append({"age": current_age, "top": current_top, "bottom": prev_bottom})

for group in age_groups:
    mid = (group["top"] + group["bottom"]) / 2
    fig.add_annotation(
        x=0.58,
        y=mid,
        text=f"<i>{group['age']}</i>",
        showarrow=False,
        font={"size": 12, "color": "#444444"},
        xanchor="right",
        yanchor="middle",
    )

# Legend for lithology types
for lithology, style in lithology_styles.items():
    fig.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            marker={
                "color": style["color"],
                "pattern": {
                    "shape": style["pattern_shape"],
                    "size": style["pattern_size"],
                    "solidity": 0.6,
                    "fgcolor": "rgba(0,0,0,0.5)",
                },
                "line": {"color": "black", "width": 1},
            },
            name=lithology,
            showlegend=True,
        )
    )

# Style
fig.update_layout(
    title={"text": "column-stratigraphic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    yaxis={
        "title": {"text": "Depth (m)", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "autorange": "reversed",
        "dtick": 20,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    xaxis={"showticklabels": False, "showgrid": False, "zeroline": False, "range": [0.2, 2.0], "fixedrange": True},
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    barmode="overlay",
    bargap=0,
    legend={
        "title": {"text": "Lithology", "font": {"size": 18}},
        "font": {"size": 14},
        "x": 0.92,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.2)",
        "borderwidth": 1,
    },
    margin={"l": 140, "r": 200, "t": 80, "b": 40},
    height=900,
    width=1600,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
