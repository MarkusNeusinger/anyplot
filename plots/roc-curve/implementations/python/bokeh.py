""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Simulated ROC curves for three classifiers with different performance levels
np.random.seed(42)

# Generate ROC curve points using sklearn-like simulation
# Using the parametric approach: FPR = t, TPR = t^(1/k) where k controls curve shape
n_points = 200
t = np.linspace(0, 1, n_points)

# Model 1: Strong classifier (AUC ~0.95) - curve bows far towards top-left
k1 = 0.15
fpr_1 = t
tpr_1 = np.power(t, k1)
auc_1 = np.trapezoid(tpr_1, fpr_1)

# Model 2: Medium classifier (AUC ~0.82) - moderate curve
k2 = 0.35
fpr_2 = t
tpr_2 = np.power(t, k2)
auc_2 = np.trapezoid(tpr_2, fpr_2)

# Model 3: Weak classifier (AUC ~0.68) - closer to diagonal
k3 = 0.6
fpr_3 = t
tpr_3 = np.power(t, k3)
auc_3 = np.trapezoid(tpr_3, fpr_3)

# Random classifier reference line
fpr_random = np.array([0, 1])
tpr_random = np.array([0, 1])

# Create ColumnDataSources
source_1 = ColumnDataSource(data={"fpr": fpr_1, "tpr": tpr_1})
source_2 = ColumnDataSource(data={"fpr": fpr_2, "tpr": tpr_2})
source_3 = ColumnDataSource(data={"fpr": fpr_3, "tpr": tpr_3})
source_random = ColumnDataSource(data={"fpr": fpr_random, "tpr": tpr_random})

# Create figure - Square format preferred for equal aspect ratio
p = figure(
    width=3600,
    height=3600,
    title="roc-curve · bokeh · pyplots.ai",
    x_axis_label="False Positive Rate",
    y_axis_label="True Positive Rate",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
    tools="",
    toolbar_location=None,
)

# Plot random classifier reference line (diagonal)
random_line = p.line(
    x="fpr", y="tpr", source=source_random, line_width=3, line_dash="dashed", line_color="#888888", alpha=0.8
)

# Plot ROC curves with distinct colors
# Using Python Blue (#306998) for best model, then complementary colors
line_1 = p.line(x="fpr", y="tpr", source=source_1, line_width=5, line_color="#306998", alpha=0.9)
line_2 = p.line(x="fpr", y="tpr", source=source_2, line_width=5, line_color="#FFD43B", alpha=0.9)
line_3 = p.line(x="fpr", y="tpr", source=source_3, line_width=5, line_color="#E74C3C", alpha=0.9)

# Create legend with AUC scores
legend = Legend(
    items=[
        (f"Random Forest (AUC = {auc_1:.2f})", [line_1]),
        (f"Logistic Regression (AUC = {auc_2:.2f})", [line_2]),
        (f"Decision Tree (AUC = {auc_3:.2f})", [line_3]),
        ("Random Classifier", [random_line]),
    ],
    location="bottom_right",
)

p.add_layout(legend)
legend.label_text_font_size = "20pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.8
legend.border_line_alpha = 0

# Style the plot
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background and border
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = "#CCCCCC"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="ROC Curve with AUC")
