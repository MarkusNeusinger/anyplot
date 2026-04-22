""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB


# Data - Generate imbalanced classification dataset
np.random.seed(42)
X, y_true = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_classes=2,
    weights=[0.7, 0.3],  # Imbalanced dataset
    random_state=42,
)

# Split into train and test for realistic evaluation
X_train, X_test, y_train, y_test = train_test_split(X, y_true, test_size=0.5, random_state=42, stratify=y_true)

# Train two classifiers for comparison
lr_model = LogisticRegression(random_state=42, max_iter=1000)
nb_model = GaussianNB()

lr_model.fit(X_train, y_train)
nb_model.fit(X_train, y_train)

# Get prediction probabilities on test set
lr_scores = lr_model.predict_proba(X_test)[:, 1]
nb_scores = nb_model.predict_proba(X_test)[:, 1]

# Calculate precision-recall curves
lr_precision, lr_recall, _ = precision_recall_curve(y_test, lr_scores)
nb_precision, nb_recall, _ = precision_recall_curve(y_test, nb_scores)

# Calculate Average Precision scores
lr_ap = average_precision_score(y_test, lr_scores)
nb_ap = average_precision_score(y_test, nb_scores)

# Baseline (random classifier) - positive class ratio
baseline = np.mean(y_test)

# Create figure (16:9 aspect ratio at 4800x2700)
p = figure(
    width=4800,
    height=2700,
    title="precision-recall · bokeh · pyplots.ai",
    x_axis_label="Recall",
    y_axis_label="Precision",
    x_range=(-0.02, 1.05),
    y_range=(0, 1.08),
)

# Create data sources for stepped lines
lr_source = ColumnDataSource(data={"recall": lr_recall, "precision": lr_precision})
nb_source = ColumnDataSource(data={"recall": nb_recall, "precision": nb_precision})

# Plot Precision-Recall curves with step style
lr_line = p.step(x="recall", y="precision", source=lr_source, line_width=5, color="#306998", alpha=0.9, mode="after")

nb_line = p.step(x="recall", y="precision", source=nb_source, line_width=5, color="#FFD43B", alpha=0.9, mode="after")

# Baseline reference line (random classifier)
baseline_source = ColumnDataSource(data={"x": [0, 1], "y": [baseline, baseline]})
baseline_line = p.line(
    x="x", y="y", source=baseline_source, line_width=4, line_dash="dashed", color="#666666", alpha=0.8
)

# Create legend with AP scores
legend = Legend(
    items=[
        (f"Logistic Regression (AP = {lr_ap:.3f})", [lr_line]),
        (f"Naive Bayes (AP = {nb_ap:.3f})", [nb_line]),
        (f"Random Classifier (baseline = {baseline:.2f})", [baseline_line]),
    ],
    location="top_right",
    label_text_font_size="28pt",
    glyph_width=50,
    glyph_height=30,
    spacing=20,
    padding=25,
    background_fill_alpha=0.9,
    background_fill_color="white",
    border_line_color="#cccccc",
    border_line_width=2,
)

p.add_layout(legend)

# Style the plot - scaled for 4800x2700
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_width = 2
p.yaxis.minor_tick_line_width = 2

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Outline
p.outline_line_width = 2
p.outline_line_color = "#cccccc"

# Min border for padding
p.min_border_left = 100
p.min_border_right = 100
p.min_border_top = 80
p.min_border_bottom = 100

# Save as PNG
export_png(p, filename="plot.png")
