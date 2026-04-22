""" pyplots.ai
count-basic: Basic Count Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure, output_file, save


# Data - Survey responses simulating a customer satisfaction survey
np.random.seed(42)
responses = np.random.choice(
    ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"],
    size=200,
    p=[0.25, 0.35, 0.20, 0.12, 0.08],
)

# Count occurrences
categories, counts = np.unique(responses, return_counts=True)
# Sort by count descending for better readability
sorted_indices = np.argsort(-counts)
categories = categories[sorted_indices]
counts = counts[sorted_indices]

# Create data source
source = ColumnDataSource(
    data={"category": categories.tolist(), "count": counts.tolist(), "label": [str(c) for c in counts]}
)

# Create figure with categorical x-axis
p = figure(
    x_range=categories.tolist(),
    width=4800,
    height=2700,
    title="count-basic · bokeh · pyplots.ai",
    x_axis_label="Response Category",
    y_axis_label="Number of Responses",
    toolbar_location=None,
)

# Plot bars with Python Blue color
p.vbar(
    x="category", top="count", source=source, width=0.7, color="#306998", alpha=0.85, line_color="#1e4c6b", line_width=2
)

# Add count labels above bars
labels = LabelSet(
    x="category",
    y="count",
    text="label",
    source=source,
    text_align="center",
    text_baseline="bottom",
    y_offset=10,
    text_font_size="22pt",
    text_color="#306998",
)
p.add_layout(labels)

# Style the plot
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = [6, 4]

# Axis styling
p.xaxis.major_label_orientation = 0.4
p.y_range.start = 0
p.y_range.end = max(counts) * 1.15  # Add space for labels

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="count-basic · bokeh · pyplots.ai")
save(p)
