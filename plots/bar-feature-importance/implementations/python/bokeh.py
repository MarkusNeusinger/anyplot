""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet, LinearColorMapper
from bokeh.palettes import Blues9
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Feature importances from a classification model
features = [
    "Income",
    "Credit Score",
    "Age",
    "Employment Years",
    "Debt Ratio",
    "Num Accounts",
    "Loan Amount",
    "Education Level",
    "Num Inquiries",
    "Home Ownership",
    "Payment History",
    "Account Balance",
]
importances = [0.185, 0.162, 0.124, 0.098, 0.089, 0.076, 0.068, 0.058, 0.052, 0.041, 0.032, 0.015]

# Sort by importance (highest at top when plotted)
sorted_pairs = sorted(zip(features, importances, strict=True), key=lambda x: x[1])
features_sorted = [p[0] for p in sorted_pairs]
importances_sorted = [p[1] for p in sorted_pairs]

# Create data source
source = ColumnDataSource(
    data={
        "features": features_sorted,
        "importances": importances_sorted,
        "labels": [f"{imp:.3f}" for imp in importances_sorted],
        "label_x": [imp + 0.008 for imp in importances_sorted],  # offset for label placement
    }
)

# Color mapper for gradient effect (light to dark based on importance)
color_mapper = LinearColorMapper(palette=list(reversed(Blues9)), low=min(importances), high=max(importances))

# Create figure with categorical y-axis
p = figure(
    width=4800,
    height=2700,
    y_range=features_sorted,
    x_range=(0, max(importances) * 1.15),
    title="bar-feature-importance · bokeh · pyplots.ai",
    x_axis_label="Importance Score",
    toolbar_location=None,
)

# Draw horizontal bars with color gradient
p.hbar(
    y="features",
    right="importances",
    height=0.7,
    source=source,
    fill_color={"field": "importances", "transform": color_mapper},
    line_color="#306998",
    line_width=2,
)

# Add value labels at end of bars
labels = LabelSet(
    x="label_x",
    y="features",
    text="labels",
    source=source,
    text_font_size="18pt",
    text_color="#306998",
    text_baseline="middle",
)
p.add_layout(labels)

# Styling for large canvas
p.title.text_font_size = "32pt"
p.title.text_color = "#306998"
p.xaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling (subtle)
p.xgrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = None

# Axis styling
p.xaxis.axis_line_color = "#666666"
p.yaxis.axis_line_color = "#666666"
p.xaxis.major_tick_line_color = "#666666"
p.yaxis.major_tick_line_color = "#666666"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="bar-feature-importance · bokeh · pyplots.ai")
