""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - Generate realistic K-means inertia values
np.random.seed(42)

# Simulate inertia values that decrease with more clusters
# Typical elbow curve pattern with clear elbow around k=4
k_values = np.arange(1, 11)
base_inertia = 5000

# Create realistic decreasing inertia with elbow around k=4
inertia = []
for k in k_values:
    if k == 1:
        val = base_inertia
    elif k <= 4:
        # Sharp decrease before elbow
        val = base_inertia * (0.35 ** (k - 1)) + np.random.uniform(50, 100)
    else:
        # Gradual decrease after elbow (diminishing returns)
        val = inertia[-1] * 0.85 + np.random.uniform(20, 50)
    inertia.append(val)

inertia = np.array(inertia)

# Optimal k (elbow point)
optimal_k = 4

# Create ColumnDataSource
source = ColumnDataSource(data={"k": k_values, "inertia": inertia})

# Create figure (4800 x 2700 px for landscape format)
p = figure(
    width=4800,
    height=2700,
    title="elbow-curve · bokeh · pyplots.ai",
    x_axis_label="Number of Clusters (k)",
    y_axis_label="Inertia (Within-Cluster Sum of Squares)",
    tools="",
    toolbar_location=None,
)

# Plot line connecting points
p.line(x="k", y="inertia", source=source, line_width=4, line_color="#306998", line_alpha=0.8)

# Plot markers at each k value
p.scatter(
    x="k", y="inertia", source=source, size=20, fill_color="#306998", line_color="#1a3a5c", line_width=3, fill_alpha=0.9
)

# Highlight the optimal k (elbow point)
optimal_inertia = inertia[optimal_k - 1]
p.scatter(
    x=[optimal_k],
    y=[optimal_inertia],
    size=30,
    fill_color="#FFD43B",
    line_color="#b8960a",
    line_width=4,
    legend_label=f"Optimal k = {optimal_k}",
)

# Add vertical line at elbow point
vline = Span(
    location=optimal_k, dimension="height", line_color="#FFD43B", line_width=3, line_dash="dashed", line_alpha=0.7
)
p.add_layout(vline)

# Add annotation label for elbow point
elbow_label = Label(
    x=optimal_k + 0.3,
    y=optimal_inertia + 150,
    text="Elbow Point",
    text_font_size="24pt",
    text_color="#333333",
    text_font_style="bold",
)
p.add_layout(elbow_label)

# Style title
p.title.text_font_size = "32pt"
p.title.text_color = "#333333"
p.title.align = "center"

# Style axes labels
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"

# Style tick labels
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Style axis lines
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#888888"
p.yaxis.axis_line_color = "#888888"

# Style ticks
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.minor_tick_line_width = 1
p.yaxis.minor_tick_line_width = 1

# Set x-axis to show integer values only
p.xaxis.ticker = list(k_values)

# Add subtle grid
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Style legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_width = 2
p.legend.border_line_color = "#cccccc"
p.legend.padding = 15
p.legend.margin = 20

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = "#cccccc"
p.outline_line_width = 2

# Save as PNG
export_png(p, filename="plot.png")
