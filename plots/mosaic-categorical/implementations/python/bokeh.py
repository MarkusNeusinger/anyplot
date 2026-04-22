""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Data - Titanic survival data (class vs survival)
data = {
    "Class": ["First", "First", "Second", "Second", "Third", "Third"],
    "Survival": ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
    "Count": [203, 122, 118, 167, 178, 528],
}
df = pd.DataFrame(data)

# Calculate proportions for mosaic plot
total = df["Count"].sum()
class_totals = df.groupby("Class")["Count"].sum()
class_order = ["First", "Second", "Third"]
survival_order = ["Survived", "Did Not Survive"]

# Build rectangles for mosaic plot - use more horizontal space (92% of canvas)
rectangles = []
gap = 0.015
plot_width = 0.92  # Expanded from 0.72 to use more horizontal space
x_start = 0.04  # Start position with small left margin

for class_name in class_order:
    class_data = df[df["Class"] == class_name]
    class_total = class_totals[class_name]
    class_width = (class_total / total) * plot_width - gap

    y_start = 0.12
    for survival in survival_order:
        cell_data = class_data[class_data["Survival"] == survival]
        if len(cell_data) > 0:
            count = cell_data["Count"].values[0]
            cell_height = (count / class_total) * 0.75 - gap / 2
            pct = count / class_total * 100

            rectangles.append(
                {
                    "left": x_start,
                    "right": x_start + class_width,
                    "bottom": y_start,
                    "top": y_start + cell_height,
                    "class": class_name,
                    "survival": survival,
                    "count": count,
                    "pct": f"{pct:.1f}%",
                }
            )
            y_start += (count / class_total) * 0.75

    x_start += (class_total / total) * plot_width

# Assign colors based on survival
colors = []
for rect in rectangles:
    if rect["survival"] == "Survived":
        colors.append("#306998")  # Python Blue
    else:
        colors.append("#FFD43B")  # Python Yellow

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "left": [r["left"] for r in rectangles],
        "right": [r["right"] for r in rectangles],
        "bottom": [r["bottom"] for r in rectangles],
        "top": [r["top"] for r in rectangles],
        "color": colors,
        "class": [r["class"] for r in rectangles],
        "survival": [r["survival"] for r in rectangles],
        "count": [r["count"] for r in rectangles],
        "pct": [r["pct"] for r in rectangles],
    }
)

# Create figure with proper middle dot character
p = figure(
    width=4800,
    height=2700,
    title="mosaic-categorical \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(0, 1),
    y_range=(0, 1),
    tools="",
    toolbar_location=None,
)

# Draw rectangles using quad with name for hover
quads = p.quad(
    left="left",
    right="right",
    bottom="bottom",
    top="top",
    source=source,
    color="color",
    line_color="white",
    line_width=4,
    alpha=0.9,
    name="mosaic",
)

# Add HoverTool for interactivity (key Bokeh feature)
hover = HoverTool(
    renderers=[quads],
    tooltips=[("Class", "@class"), ("Status", "@survival"), ("Count", "@count"), ("Proportion", "@pct")],
)
p.add_tools(hover)

# Add count labels in center of each rectangle
for rect in rectangles:
    cx = (rect["left"] + rect["right"]) / 2
    cy = (rect["bottom"] + rect["top"]) / 2
    label = Label(
        x=cx,
        y=cy,
        text=str(rect["count"]),
        text_align="center",
        text_baseline="middle",
        text_font_size="36pt",
        text_font_style="bold",
        text_color="white" if rect["survival"] == "Survived" else "#333333",
    )
    p.add_layout(label)

# Add class labels at bottom
x_pos = 0.04
for class_name in class_order:
    class_total = class_totals[class_name]
    class_width = (class_total / total) * plot_width - gap
    label = Label(
        x=x_pos + class_width / 2,
        y=0.06,
        text=class_name,
        text_align="center",
        text_baseline="middle",
        text_font_size="32pt",
        text_font_style="bold",
        text_color="#333333",
    )
    p.add_layout(label)
    x_pos += (class_total / total) * plot_width

# Add x-axis label centered under the mosaic
x_axis_label = Label(
    x=0.5,
    y=0.015,
    text="Passenger Class (width = proportion of passengers)",
    text_align="center",
    text_baseline="bottom",
    text_font_size="24pt",
    text_color="#555555",
)
p.add_layout(x_axis_label)

# Add legend inline at the top right of the mosaic (better integration)
legend_y = 0.92
legend_items = [
    {"color": "#306998", "text": "Survived", "x": 0.68},
    {"color": "#FFD43B", "text": "Did Not Survive", "x": 0.86},
]

for item in legend_items:
    # Legend color box
    p.quad(
        left=[item["x"] - 0.015],
        right=[item["x"] + 0.015],
        bottom=[legend_y - 0.018],
        top=[legend_y + 0.018],
        color=item["color"],
        line_color="white",
        line_width=2,
    )
    # Legend text
    label = Label(
        x=item["x"] + 0.025,
        y=legend_y,
        text=item["text"],
        text_align="left",
        text_baseline="middle",
        text_font_size="24pt",
        text_color="#333333",
    )
    p.add_layout(label)

# Add subtitle centered
subtitle = Label(
    x=0.5,
    y=0.97,
    text="Titanic Survival by Passenger Class",
    text_align="center",
    text_baseline="top",
    text_font_size="32pt",
    text_font_style="italic",
    text_color="#555555",
)
p.add_layout(subtitle)

# Style the figure
p.title.text_font_size = "40pt"
p.title.text_font_style = "bold"
p.title.align = "center"

# Hide axes
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
