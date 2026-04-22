""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, LinearColorMapper
from bokeh.plotting import figure
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier


# Data - Generate synthetic classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)

# Train a classifier
clf = KNeighborsClassifier(n_neighbors=15)
clf.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
h = 0.02  # Step size
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

# Get predictions for mesh grid
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Colors for classes
class_colors = ["#306998", "#FFD43B"]  # Python Blue and Yellow

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="contour-decision-boundary · bokeh · pyplots.ai",
    x_axis_label="Feature 1",
    y_axis_label="Feature 2",
    tools="",
    toolbar_location=None,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
)

# Use image to render decision boundary efficiently
color_mapper = LinearColorMapper(palette=["#C8D5E3", "#FFF5C8"], low=0, high=1)
p.image(
    image=[Z.astype(float)], x=x_min, y=y_min, dw=x_max - x_min, dh=y_max - y_min, color_mapper=color_mapper, alpha=0.5
)

# Separate data points by class
class_0_mask = y == 0
class_1_mask = y == 1

# Get predictions for training points to identify misclassified
y_pred = clf.predict(X)
correct_mask = y == y_pred

# Data sources for each class with hover info
source_class0 = ColumnDataSource(
    data={
        "x": X[class_0_mask, 0],
        "y": X[class_0_mask, 1],
        "class": ["Class 0"] * np.sum(class_0_mask),
        "status": ["Correct" if c else "Misclassified" for c in correct_mask[class_0_mask]],
    }
)

source_class1 = ColumnDataSource(
    data={
        "x": X[class_1_mask, 0],
        "y": X[class_1_mask, 1],
        "class": ["Class 1"] * np.sum(class_1_mask),
        "status": ["Correct" if c else "Misclassified" for c in correct_mask[class_1_mask]],
    }
)

# Plot training points
# Class 0 - circles
c0_scatter = p.scatter(
    x="x", y="y", source=source_class0, size=25, fill_color="#306998", line_color="white", line_width=3, alpha=0.9
)

# Class 1 - circles
c1_scatter = p.scatter(
    x="x", y="y", source=source_class1, size=25, fill_color="#FFD43B", line_color="white", line_width=3, alpha=0.9
)

# Mark misclassified points with X marker
misclassified_mask = ~correct_mask
misclassified_marker = None
if np.any(misclassified_mask):
    source_misclassified = ColumnDataSource(
        data={
            "x": X[misclassified_mask, 0],
            "y": X[misclassified_mask, 1],
            "true_class": [f"Class {c}" for c in y[misclassified_mask]],
            "pred_class": [f"Class {c}" for c in y_pred[misclassified_mask]],
        }
    )
    misclassified_marker = p.scatter(
        x="x", y="y", source=source_misclassified, marker="x", size=35, line_color="#CC3333", line_width=5, alpha=1.0
    )

# Add HoverTool for interactivity
hover = HoverTool(
    tooltips=[("Feature 1", "@x{0.2f}"), ("Feature 2", "@y{0.2f}"), ("Class", "@class"), ("Status", "@status")],
    renderers=[c0_scatter, c1_scatter],
)
p.add_tools(hover)

# Add separate HoverTool for misclassified points
if misclassified_marker is not None:
    hover_misclassified = HoverTool(
        tooltips=[
            ("Feature 1", "@x{0.2f}"),
            ("Feature 2", "@y{0.2f}"),
            ("True Class", "@true_class"),
            ("Predicted", "@pred_class"),
        ],
        renderers=[misclassified_marker],
    )
    p.add_tools(hover_misclassified)

# Create legend with misclassified entry
legend_items = [
    LegendItem(label="Class 0", renderers=[c0_scatter]),
    LegendItem(label="Class 1", renderers=[c1_scatter]),
]
if misclassified_marker is not None:
    legend_items.append(LegendItem(label="Misclassified", renderers=[misclassified_marker]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "28pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.background_fill_alpha = 0.8
legend.padding = 15
legend.spacing = 10
p.add_layout(legend, "right")

# Styling
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Save as PNG
export_png(p, filename="plot.png")

# Also save HTML for interactive version
output_file("plot.html")
save(p)
