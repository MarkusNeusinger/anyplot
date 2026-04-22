""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Arrow, ColumnDataSource, Label, Legend, LegendItem, VeeHead
from bokeh.plotting import figure
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - Iris dataset
iris = load_iris()
X = iris.data
y = iris.target
feature_names = ["sepal length", "sepal width", "petal length", "petal width"]
target_names = iris.target_names

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T
explained_var = pca.explained_variance_ratio_ * 100

# Scale loadings for visibility (scale to fit within score range)
score_max = np.abs(scores).max()
loading_scale = score_max * 0.9 / np.abs(loadings).max()
loadings_scaled = loadings * loading_scale

# Create figure with appropriate range
margin = 1.5
x_range = (scores[:, 0].min() - margin, scores[:, 0].max() + margin)
y_range = (scores[:, 1].min() - margin, scores[:, 1].max() + margin)

p = figure(
    width=4800,
    height=2700,
    title="biplot-pca · bokeh · pyplots.ai",
    x_axis_label=f"PC1 ({explained_var[0]:.1f}%)",
    y_axis_label=f"PC2 ({explained_var[1]:.1f}%)",
    x_range=x_range,
    y_range=y_range,
)

# Style title and axes - larger sizes for 4800x2700
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Colors for groups - using Python Blue first, then complementary colors
colors = ["#306998", "#FFD43B", "#4CAF50"]  # Python Blue, Python Yellow, Green

# Plot observation scores by group
legend_items = []
for i, name in enumerate(target_names):
    mask = y == i
    source = ColumnDataSource(data={"x": scores[mask, 0], "y": scores[mask, 1]})
    renderer = p.scatter(x="x", y="y", source=source, size=25, alpha=0.75, color=colors[i])
    legend_items.append(LegendItem(label=name, renderers=[renderer]))

# Add legend
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "24pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 12
legend.padding = 15
legend.background_fill_alpha = 0.85
p.add_layout(legend)

# Draw loading arrows with custom label positions to avoid overlap
arrow_color = "#C0392B"  # Red for contrast with data points

# Custom label offsets for each feature to avoid overlap
label_offsets = {
    "sepal length": (0.4, 0.5),
    "sepal width": (-0.3, 0.4),
    "petal length": (0.5, -0.4),
    "petal width": (0.3, 0.5),
}

for i, name in enumerate(feature_names):
    x_end = loadings_scaled[i, 0]
    y_end = loadings_scaled[i, 1]

    # Add arrow
    p.add_layout(
        Arrow(
            end=VeeHead(size=30, fill_color=arrow_color, line_color=arrow_color),
            x_start=0,
            y_start=0,
            x_end=x_end,
            y_end=y_end,
            line_width=4,
            line_color=arrow_color,
        )
    )

    # Add label with custom offset
    offset_x, offset_y = label_offsets[name]
    label = Label(
        x=x_end + offset_x,
        y=y_end + offset_y,
        text=name,
        text_font_size="20pt",
        text_color=arrow_color,
        text_font_style="bold",
        text_align="center",
    )
    p.add_layout(label)

# Add origin reference lines (dashed)
p.line(x=[x_range[0], x_range[1]], y=[0, 0], line_width=2, line_color="#888888", line_alpha=0.5, line_dash="dashed")
p.line(x=[0, 0], y=[y_range[0], y_range[1]], line_width=2, line_color="#888888", line_alpha=0.5, line_dash="dashed")

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#FAFAFA"

# Save
export_png(p, filename="plot.png")
