""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import plotly.graph_objects as go


# Data - synthetic sedimentary section based on Western Interior Seaway formations
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

# Refined earth-tone palette with Python Blue accent for limestone
lithology_styles = {
    "Sandstone": {"color": "#E8D5A3", "pattern_shape": ".", "pattern_size": 8},
    "Shale": {"color": "#9E9A91", "pattern_shape": "-", "pattern_size": 6},
    "Limestone": {"color": "#7BA7C9", "pattern_shape": "+", "pattern_size": 8},
    "Siltstone": {"color": "#C9B897", "pattern_shape": "/", "pattern_size": 6},
    "Conglomerate": {"color": "#B8763C", "pattern_shape": "x", "pattern_size": 10},
}

# Age boundary colors for subtle background shading
age_colors = {
    "Late Cretaceous": "rgba(48, 105, 152, 0.04)",
    "Maastrichtian": "rgba(48, 105, 152, 0.08)",
    "Paleocene": "rgba(48, 105, 152, 0.12)",
    "Eocene": "rgba(48, 105, 152, 0.16)",
}

# Plot
fig = go.Figure()

# Group consecutive layers by age for boundary markers and left-side labels
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

# Add subtle age-period background shading using shapes
for group in age_groups:
    fig.add_shape(
        type="rect",
        x0=0.3,
        x1=1.95,
        y0=group["top"],
        y1=group["bottom"],
        fillcolor=age_colors.get(group["age"], "rgba(0,0,0,0.02)"),
        line={"width": 0},
        layer="below",
    )

# Add age boundary lines (heavier horizontal lines at period transitions)
for i in range(1, len(age_groups)):
    boundary_depth = age_groups[i]["top"]
    fig.add_shape(
        type="line",
        x0=0.3,
        x1=1.95,
        y0=boundary_depth,
        y1=boundary_depth,
        line={"color": "#306998", "width": 2.5, "dash": "dot"},
        layer="above",
    )

# Add layer bars
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
                    "fgcolor": "rgba(0,0,0,0.45)",
                },
                "line": {"color": "#2C2C2C", "width": 1.5},
            },
            width=0.65,
            showlegend=False,
            hovertemplate=(
                f"<b>{layer['formation']}</b><br>"
                f"Lithology: {layer['lithology']}<br>"
                f"Depth: {layer['top']}–{layer['bottom']} m<br>"
                f"Thickness: {thickness} m<br>"
                f"Age: {layer['age']}"
                "<extra></extra>"
            ),
        )
    )

    # Formation name annotation (right side) - increased font size
    fig.add_annotation(
        x=1.38,
        y=mid_depth,
        text=f"<b>{layer['formation']}</b><br><i>{layer['lithology']}</i>",
        showarrow=False,
        font={"size": 15, "color": "#1A1A1A"},
        xanchor="left",
        yanchor="middle",
    )

# Age labels on the left side
for group in age_groups:
    mid = (group["top"] + group["bottom"]) / 2
    fig.add_annotation(
        x=0.55,
        y=mid,
        text=f"<b>{group['age']}</b>",
        showarrow=False,
        font={"size": 14, "color": "#306998"},
        xanchor="right",
        yanchor="middle",
    )

# Legend for lithology types with pattern swatches
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
                    "fgcolor": "rgba(0,0,0,0.45)",
                },
                "line": {"color": "#2C2C2C", "width": 1},
            },
            name=lithology,
            showlegend=True,
        )
    )

# Style
fig.update_layout(
    title={
        "text": "column-stratigraphic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1A1A1A"},
        "x": 0.5,
        "xanchor": "center",
    },
    yaxis={
        "title": {"text": "Depth (m)", "font": {"size": 22, "color": "#2C2C2C"}},
        "tickfont": {"size": 16},
        "autorange": "reversed",
        "dtick": 20,
        "gridcolor": "rgba(0,0,0,0.07)",
        "gridwidth": 1,
        "zeroline": False,
        "side": "left",
    },
    xaxis={"showticklabels": False, "showgrid": False, "zeroline": False, "range": [0.3, 1.95], "fixedrange": True},
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    barmode="overlay",
    bargap=0,
    legend={
        "title": {"text": "<b>Lithology</b>", "font": {"size": 18}},
        "font": {"size": 15},
        "x": 0.88,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.95)",
        "bordercolor": "rgba(48,105,152,0.3)",
        "borderwidth": 1,
    },
    margin={"l": 130, "r": 140, "t": 80, "b": 40},
    height=900,
    width=1600,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
