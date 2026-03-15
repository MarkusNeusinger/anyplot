"""pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-15
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Range1d
from bokeh.plotting import figure, output_file, save


# Data: Synthetic sedimentary section with 10 layers
layers = [
    {"top": 0, "bottom": 15, "lithology": "Sandstone", "formation": "Dakota Fm", "age": "Late Cretaceous"},
    {"top": 15, "bottom": 35, "lithology": "Shale", "formation": "Mancos Fm", "age": "Late Cretaceous"},
    {"top": 35, "bottom": 50, "lithology": "Limestone", "formation": "Niobrara Fm", "age": "Late Cretaceous"},
    {"top": 50, "bottom": 65, "lithology": "Siltstone", "formation": "Pierre Fm", "age": "Late Cretaceous"},
    {"top": 65, "bottom": 90, "lithology": "Sandstone", "formation": "Fox Hills Fm", "age": "Late Cretaceous"},
    {"top": 90, "bottom": 110, "lithology": "Conglomerate", "formation": "Dawson Fm", "age": "Paleocene"},
    {"top": 110, "bottom": 135, "lithology": "Shale", "formation": "Green River Fm", "age": "Eocene"},
    {"top": 135, "bottom": 155, "lithology": "Limestone", "formation": "Leadville Fm", "age": "Eocene"},
    {"top": 155, "bottom": 175, "lithology": "Sandstone", "formation": "Wasatch Fm", "age": "Eocene"},
    {"top": 175, "bottom": 200, "lithology": "Siltstone", "formation": "Uinta Fm", "age": "Eocene"},
]

# Lithology style mapping: color, hatch_pattern
lithology_styles = {
    "Sandstone": {"color": "#F5DEB3", "hatch_pattern": ".", "hatch_color": "#8B7355"},
    "Shale": {"color": "#A9A9A9", "hatch_pattern": "-", "hatch_color": "#4A4A4A"},
    "Limestone": {"color": "#87CEEB", "hatch_pattern": "+", "hatch_color": "#2E5A88"},
    "Siltstone": {"color": "#C4B7A6", "hatch_pattern": "/", "hatch_color": "#6B5B4A"},
    "Conglomerate": {"color": "#D2691E", "hatch_pattern": "o", "hatch_color": "#5C2E00"},
}

# Build data arrays
tops = [layer["top"] for layer in layers]
bottoms = [layer["bottom"] for layer in layers]
lithologies = [layer["lithology"] for layer in layers]
formations = [layer["formation"] for layer in layers]
ages = [layer["age"] for layer in layers]
thicknesses = [layer["bottom"] - layer["top"] for layer in layers]

fill_colors = [lithology_styles[lith]["color"] for lith in lithologies]
hatch_patterns = [lithology_styles[lith]["hatch_pattern"] for lith in lithologies]
hatch_colors = [lithology_styles[lith]["hatch_color"] for lith in lithologies]

# Column x-position and width
col_left = 0.0
col_right = 1.0
col_center = 0.5
col_width = 1.0

# Plot
p = figure(
    width=4800,
    height=2700,
    title="column-stratigraphic · bokeh · pyplots.ai",
    y_axis_label="Depth (m)",
    toolbar_location=None,
    x_range=Range1d(-0.8, 2.5),
    y_range=Range1d(210, -10),
)

# Draw each layer as a rectangle with hatch pattern
legend_items_dict = {}
for layer in layers:
    source = ColumnDataSource(
        data={
            "x": [col_center],
            "y": [(layer["top"] + layer["bottom"]) / 2],
            "width": [col_width],
            "height": [layer["bottom"] - layer["top"]],
            "lithology": [layer["lithology"]],
            "formation": [layer["formation"]],
            "age": [layer["age"]],
            "top_depth": [layer["top"]],
            "bottom_depth": [layer["bottom"]],
            "thickness": [layer["bottom"] - layer["top"]],
        }
    )

    style = lithology_styles[layer["lithology"]]
    renderer = p.rect(
        x="x",
        y="y",
        width="width",
        height="height",
        source=source,
        fill_color=style["color"],
        line_color="#2C2C2C",
        line_width=2,
        hatch_pattern=style["hatch_pattern"],
        hatch_color=style["hatch_color"],
        hatch_alpha=0.7,
        hatch_scale=16,
        hatch_weight=2,
    )

    # Track renderers for legend (one entry per lithology)
    lith = layer["lithology"]
    if lith not in legend_items_dict:
        legend_items_dict[lith] = renderer

    # Hover tool per layer
    hover = HoverTool(
        renderers=[renderer],
        tooltips=[
            ("Lithology", "@lithology"),
            ("Formation", "@formation"),
            ("Age", "@age"),
            ("Top", "@top_depth{0.0} m"),
            ("Bottom", "@bottom_depth{0.0} m"),
            ("Thickness", "@thickness{0.0} m"),
        ],
    )
    p.add_tools(hover)

# Formation labels on the right side
for layer in layers:
    mid_y = (layer["top"] + layer["bottom"]) / 2
    label = Label(
        x=col_right + 0.08,
        y=mid_y,
        text=layer["formation"],
        text_font_size="18pt",
        text_align="left",
        text_baseline="middle",
        text_color="#2C2C2C",
    )
    p.add_layout(label)

# Age labels on the left side
age_groups = {}
for layer in layers:
    age = layer["age"]
    if age not in age_groups:
        age_groups[age] = {"top": layer["top"], "bottom": layer["bottom"]}
    else:
        age_groups[age]["bottom"] = max(age_groups[age]["bottom"], layer["bottom"])
        age_groups[age]["top"] = min(age_groups[age]["top"], layer["top"])

for age, bounds in age_groups.items():
    mid_y = (bounds["top"] + bounds["bottom"]) / 2
    label = Label(
        x=-0.08,
        y=mid_y,
        text=age,
        text_font_size="18pt",
        text_align="right",
        text_baseline="middle",
        text_color="#2C2C2C",
        text_font_style="italic",
    )
    p.add_layout(label)

    # Draw bracket line for age span
    p.line(x=[-0.05, -0.05], y=[bounds["top"], bounds["bottom"]], line_color="#2C2C2C", line_width=2)
    p.line(x=[-0.07, -0.05], y=[bounds["top"], bounds["top"]], line_color="#2C2C2C", line_width=2)
    p.line(x=[-0.07, -0.05], y=[bounds["bottom"], bounds["bottom"]], line_color="#2C2C2C", line_width=2)

# Legend
legend_items = [LegendItem(label=lith, renderers=[rend]) for lith, rend in legend_items_dict.items()]
legend = Legend(
    items=legend_items,
    location="bottom_right",
    label_text_font_size="20pt",
    spacing=12,
    padding=20,
    background_fill_alpha=0.85,
    glyph_height=30,
    glyph_width=30,
    title="Lithology",
    title_text_font_size="22pt",
    title_text_font_style="bold",
)
p.add_layout(legend)

# Style
p.title.text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "22pt"

p.xaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_dash = "dashed"

p.yaxis.minor_tick_line_color = None
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="column-stratigraphic · bokeh · pyplots.ai")
save(p)
