""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import os

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression


# Data - Generate binary classification data
np.random.seed(42)
X, y = make_classification(
    n_samples=200, n_features=1, n_informative=1, n_redundant=0, n_clusters_per_class=1, flip_y=0.1, random_state=42
)
x = X.flatten()

# Scale x to meaningful range (e.g., test score 20-80)
x = (x - x.min()) / (x.max() - x.min()) * 60 + 20

# Fit logistic regression
model = LogisticRegression()
model.fit(x.reshape(-1, 1), y)

# Generate smooth curve for logistic regression
x_curve = np.linspace(x.min() - 2, x.max() + 2, 300)
prob_curve = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Compute confidence intervals (using asymptotic approximation)
p_val = prob_curve
se = np.sqrt(p_val * (1 - p_val) / len(x))  # Simplified SE approximation
z = 1.96  # 95% CI
ci_lower = np.clip(prob_curve - z * se * 3, 0, 1)  # Scaled for visibility
ci_upper = np.clip(prob_curve + z * se * 3, 0, 1)

# Jitter y values for visibility
jitter = np.random.uniform(-0.03, 0.03, len(y))
y_jittered = y + jitter

# Separate data by class
class_0_mask = y == 0
class_1_mask = y == 1

# Create data sources
source_class0 = ColumnDataSource(data={"x": x[class_0_mask], "y": y_jittered[class_0_mask]})

source_class1 = ColumnDataSource(data={"x": x[class_1_mask], "y": y_jittered[class_1_mask]})

source_curve = ColumnDataSource(data={"x": x_curve, "prob": prob_curve, "ci_lower": ci_lower, "ci_upper": ci_upper})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="logistic-regression · bokeh · pyplots.ai",
    x_axis_label="Test Score",
    y_axis_label="Probability of Passing",
    x_range=(x.min() - 5, x.max() + 5),
    y_range=(-0.08, 1.08),
)

# Confidence interval band
p.varea(
    x="x",
    y1="ci_lower",
    y2="ci_upper",
    source=source_curve,
    fill_color="#306998",
    fill_alpha=0.2,
    legend_label="95% CI",
)

# Logistic curve
p.line(x="x", y="prob", source=source_curve, line_color="#306998", line_width=5, legend_label="Logistic Curve")

# Data points - Class 0 (failed)
p.scatter(
    x="x",
    y="y",
    source=source_class0,
    size=20,
    fill_color="#306998",
    fill_alpha=0.6,
    line_color="white",
    line_width=2,
    legend_label="Class 0 (Failed)",
)

# Data points - Class 1 (passed)
p.scatter(
    x="x",
    y="y",
    source=source_class1,
    size=20,
    fill_color="#FFD43B",
    fill_alpha=0.7,
    line_color="#333333",
    line_width=2,
    legend_label="Class 1 (Passed)",
)

# Decision threshold line at p=0.5
threshold = Span(location=0.5, dimension="width", line_color="#E63946", line_width=4, line_dash="dashed")
p.add_layout(threshold)

# Add threshold label
threshold_label = Label(
    x=x.max() - 5,
    y=0.53,
    text="Decision Threshold (p=0.5)",
    text_font_size="20pt",
    text_color="#E63946",
    text_align="right",
)
p.add_layout(threshold_label)

# Model accuracy annotation
accuracy = model.score(x.reshape(-1, 1), y)
accuracy_label = Label(
    x=x.min() + 2, y=0.92, text=f"Model Accuracy: {accuracy:.1%}", text_font_size="22pt", text_color="#333333"
)
p.add_layout(accuracy_label)

# Styling - Large text for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Legend styling
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "20pt"
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.background_fill_alpha = 0.85
p.legend.border_line_color = "#CCCCCC"
p.legend.padding = 15

# Background
p.background_fill_color = "#FAFAFA"

# Save to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "plot.png")
export_png(p, filename=output_path)
