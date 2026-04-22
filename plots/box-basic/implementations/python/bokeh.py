""" pyplots.ai
box-basic: Basic Box Plot
Library: bokeh 3.8.2 | Python 3.14
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, LabelSet, Whisker
from bokeh.plotting import figure
from bokeh.transform import factor_cmap


# Data - Test scores across 4 classes with varying distributions
np.random.seed(42)
categories = ["Class A", "Class B", "Class C", "Class D"]

scores = {
    "Class A": np.random.normal(75, 10, 100),
    "Class B": np.concatenate([np.random.normal(85, 5, 90), np.array([65, 68, 70])]),
    "Class C": np.clip(np.random.normal(68, 14, 100), 30, None),
    "Class D": np.concatenate([np.random.normal(78, 8, 95), np.array([100, 102, 50, 52])]),
}

# Box plot statistics
colors = ["#306998", "#4B8BBE", "#E5A03A", "#7A9E3D"]

box_data = {"cat": [], "q1": [], "q2": [], "q3": [], "upper": [], "lower": [], "iqr": []}
outlier_x = []
outlier_y = []

for cat in categories:
    values = np.array(scores[cat])
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    lower_fence = q1 - 1.5 * iqr
    upper_whisker = values[values <= upper_fence].max()
    lower_whisker = values[values >= lower_fence].min()

    box_data["cat"].append(cat)
    box_data["q1"].append(round(q1, 1))
    box_data["q2"].append(round(q2, 1))
    box_data["q3"].append(round(q3, 1))
    box_data["upper"].append(round(upper_whisker, 1))
    box_data["lower"].append(round(lower_whisker, 1))
    box_data["iqr"].append(round(iqr, 1))

    outliers = values[(values < lower_fence) | (values > upper_fence)]
    for o in outliers:
        outlier_x.append(cat)
        outlier_y.append(round(o, 1))

source = ColumnDataSource(data=box_data)

# Figure (4800 x 2700 px)
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="box-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Class",
    y_axis_label="Test Score (points)",
    toolbar_location=None,
    tools="",
)

# Boxes (q1 to q3) with factor_cmap - wider boxes for better canvas utilization
cmap = factor_cmap("cat", palette=colors, factors=categories)
box_width = 0.7

p.vbar(
    x="cat",
    top="q3",
    bottom="q2",
    source=source,
    width=box_width,
    fill_color=cmap,
    line_color="#333333",
    line_width=2,
    fill_alpha=0.85,
)
p.vbar(
    x="cat",
    top="q2",
    bottom="q1",
    source=source,
    width=box_width,
    fill_color=cmap,
    line_color="#333333",
    line_width=2,
    fill_alpha=0.85,
)

# Median lines - thin rect for crisp appearance on categorical axis
median_source = ColumnDataSource(data={"x": box_data["cat"], "y": box_data["q2"]})
p.rect(x="x", y="y", width=box_width, height=0.08, source=median_source, fill_color="#1a1a1a", line_color="#1a1a1a")

# Whiskers
whisker = Whisker(
    base="cat", upper="upper", lower="lower", source=source, level="annotation", line_width=3, line_color="#333333"
)
whisker.upper_head.size = 40
whisker.lower_head.size = 40
whisker.upper_head.line_width = 3
whisker.lower_head.line_width = 3
p.add_layout(whisker)

# Outliers
if outlier_x:
    outlier_source = ColumnDataSource(data={"x": outlier_x, "y": outlier_y})
    p.scatter(
        x="x",
        y="y",
        source=outlier_source,
        size=18,
        fill_color="white",
        line_color="#333333",
        line_width=2.5,
        marker="circle",
        alpha=0.9,
    )

# Data storytelling - annotations highlighting key insights
class_b_iqr = box_data["iqr"][1]
class_c_iqr = box_data["iqr"][2]

annotation_source = ColumnDataSource(
    data={
        "x": ["Class B", "Class C"],
        "y": [box_data["upper"][1] + 6, box_data["upper"][2] + 6],
        "text": [f"Tightest spread (IQR = {class_b_iqr})", f"Widest spread (IQR = {class_c_iqr})"],
        "color": ["#3a6f94", "#c0820a"],
    }
)
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    text_color="color",
    source=annotation_source,
    text_font_size="20pt",
    text_font_style="bold",
    text_align="center",
)
p.add_layout(labels)

# Styling for 4800x2700 px
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Reduce x_range padding so boxes fill more of the canvas
p.x_range.range_padding = 0.12

# Grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2
p.ygrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_width = 1

# Spines - remove top and right
p.outline_line_color = None
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Background
p.background_fill_color = None
p.border_fill_color = None

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
