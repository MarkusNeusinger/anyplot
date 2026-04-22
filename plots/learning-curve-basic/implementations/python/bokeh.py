""" pyplots.ai
learning-curve-basic: Model Learning Curve
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure


# Data - Simulate learning curve for a classification model
np.random.seed(42)

# Training set sizes (10 points from 10% to 100% of data)
train_sizes = np.array([50, 100, 200, 300, 400, 500, 600, 700, 800, 900])

# Simulate 5-fold cross-validation scores
n_folds = 5
n_sizes = len(train_sizes)

# Training scores: start high and stay high (slight decrease as model generalizes)
train_scores_mean = 0.99 - 0.02 * np.log(train_sizes / train_sizes[0]) / np.log(train_sizes[-1] / train_sizes[0])
train_scores_std = 0.01 + 0.01 * (1 - train_sizes / train_sizes[-1])

# Validation scores: start low, improve with more data (typical learning curve shape)
validation_scores_mean = 0.65 + 0.25 * (1 - np.exp(-train_sizes / 300))
validation_scores_std = 0.08 * np.exp(-train_sizes / 400) + 0.01

# Create bands for confidence intervals (±1 std)
train_upper = train_scores_mean + train_scores_std
train_lower = train_scores_mean - train_scores_std
val_upper = validation_scores_mean + validation_scores_std
val_lower = validation_scores_mean - validation_scores_std

# Create ColumnDataSource for training data
train_source = ColumnDataSource(
    data={"x": train_sizes, "y": train_scores_mean, "upper": train_upper, "lower": train_lower}
)

# Create ColumnDataSource for validation data
val_source = ColumnDataSource(
    data={"x": train_sizes, "y": validation_scores_mean, "upper": val_upper, "lower": val_lower}
)

# Create figure (4800 x 2700 px for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="learning-curve-basic · bokeh · pyplots.ai",
    x_axis_label="Training Set Size (samples)",
    y_axis_label="Accuracy Score",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Add confidence bands for training scores (Python Blue)
train_band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=train_source,
    fill_color="#306998",
    fill_alpha=0.2,
    line_color="#306998",
    line_alpha=0.3,
)
p.add_layout(train_band)

# Add confidence bands for validation scores (Python Yellow/Orange)
val_band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=val_source,
    fill_color="#FFD43B",
    fill_alpha=0.3,
    line_color="#FFD43B",
    line_alpha=0.4,
)
p.add_layout(val_band)

# Plot training score line
train_line = p.line(x="x", y="y", source=train_source, line_color="#306998", line_width=4, line_alpha=0.9)

# Plot training score markers
train_scatter = p.scatter(x="x", y="y", source=train_source, color="#306998", size=22, alpha=0.9)

# Plot validation score line
val_line = p.line(x="x", y="y", source=val_source, line_color="#E6A800", line_width=4, line_alpha=0.9)

# Plot validation score markers
val_scatter = p.scatter(x="x", y="y", source=val_source, color="#E6A800", size=22, alpha=0.9)

# Add hover tool for interactivity (Bokeh distinctive feature)
hover_train = HoverTool(
    renderers=[train_scatter],
    tooltips=[
        ("Type", "Training Score"),
        ("Samples", "@x{0}"),
        ("Accuracy", "@y{0.000}"),
        ("Std Range", "@lower{0.000} - @upper{0.000}"),
    ],
    mode="mouse",
)
p.add_tools(hover_train)

hover_val = HoverTool(
    renderers=[val_scatter],
    tooltips=[
        ("Type", "Validation Score"),
        ("Samples", "@x{0}"),
        ("Accuracy", "@y{0.000}"),
        ("Std Range", "@lower{0.000} - @upper{0.000}"),
    ],
    mode="mouse",
)
p.add_tools(hover_val)

# Create legend - positioned inside plot area, top-left for better visibility
legend = Legend(
    items=[
        LegendItem(label="Training Score", renderers=[train_line, train_scatter]),
        LegendItem(label="Validation Score", renderers=[val_line, val_scatter]),
    ],
    location="top_left",
)

p.add_layout(legend, "center")

# Styling - increased sizes for better readability on 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Legend styling - larger and more prominent
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_alpha = 0.9
p.legend.background_fill_color = "#ffffff"
p.legend.border_line_color = "#888888"
p.legend.border_line_width = 2
p.legend.padding = 25
p.legend.spacing = 20
p.legend.glyph_width = 50
p.legend.glyph_height = 40

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Axis range to show all data with padding
p.y_range.start = 0.55
p.y_range.end = 1.02

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(p)
