""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LabelSet, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform


# Data - Multi-class classification results for a sentiment analysis model
np.random.seed(42)

class_names = ["Negative", "Neutral", "Positive", "Very Positive"]

# Simulated confusion matrix with realistic patterns:
# - Good diagonal (correct predictions)
# - Adjacent classes more likely to be confused
# - Some class imbalance
confusion = np.array(
    [
        [142, 23, 8, 2],  # Negative: mostly correct, some confused with Neutral
        [18, 98, 31, 5],  # Neutral: often confused with adjacent classes
        [5, 28, 156, 24],  # Positive: good accuracy, some confusion with Neutral/Very Positive
        [1, 4, 19, 86],  # Very Positive: smaller class, good precision
    ]
)

# Prepare data for Bokeh heatmap using rect glyphs
x_coords = []
y_coords = []
values = []
text_labels = []

for i, true_class in enumerate(class_names):
    for j, pred_class in enumerate(class_names):
        x_coords.append(pred_class)
        y_coords.append(true_class)
        val = confusion[i, j]
        values.append(val)
        text_labels.append(str(val))

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "value": values, "text": text_labels})

# Color mapping - Blues sequential palette for counts
colors = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]
mapper = LinearColorMapper(palette=colors, low=0, high=max(values))

# Create figure - Square format works better for confusion matrices
p = figure(
    width=3600,
    height=3600,
    title="confusion-matrix · bokeh · pyplots.ai",
    x_range=class_names,
    y_range=list(reversed(class_names)),  # Reverse to have first class at top
    x_axis_label="Predicted Label",
    y_axis_label="True Label",
    tools="",
    toolbar_location=None,
)

# Draw heatmap cells using rect
p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    line_color="#FFFFFF",
    line_width=3,
)

# Add text annotations for cell values
# Calculate contrasting colors for text (white on dark, black on light)
text_colors = []
for val in values:
    # Use white text on darker cells (higher values)
    if val > max(values) * 0.5:
        text_colors.append("#FFFFFF")
    else:
        text_colors.append("#08306b")

source.data["text_color"] = text_colors

labels = LabelSet(
    x="x",
    y="y",
    text="text",
    text_color="text_color",
    text_font_size="32pt",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
    source=source,
)
p.add_layout(labels)

# Style the figure for large canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.major_label_orientation = 0.4  # Slight angle for readability

# Remove grid for cleaner heatmap look
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Add colorbar
color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    title="Count",
    title_text_font_size="22pt",
    major_label_text_font_size="18pt",
    label_standoff=12,
    bar_line_color="#08306b",
    bar_line_width=2,
    width=30,
    padding=40,
)
p.add_layout(color_bar, "right")

# Adjust overall padding
p.min_border_left = 150
p.min_border_right = 150
p.min_border_top = 100
p.min_border_bottom = 150

# Save outputs
export_png(p, filename="plot.png")

# Also save interactive HTML
output_file("plot.html")
save(p)
