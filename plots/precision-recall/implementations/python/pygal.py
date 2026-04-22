""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: pygal 3.1.0 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split


# Data - Generate imbalanced binary classification dataset
np.random.seed(42)
X, y = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_classes=2,
    weights=[0.7, 0.3],  # Imbalanced: 70% class 0, 30% class 1
    flip_y=0.05,  # Add noise for more realistic results
    random_state=42,
)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Train two classifiers for comparison
# Logistic Regression
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train, y_train)
lr_scores = lr_model.predict_proba(X_test)[:, 1]
lr_precision, lr_recall, _ = precision_recall_curve(y_test, lr_scores)
lr_ap = average_precision_score(y_test, lr_scores)

# Random Forest (slightly less regularized for more interesting curve)
rf_model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
rf_model.fit(X_train, y_train)
rf_scores = rf_model.predict_proba(X_test)[:, 1]
rf_precision, rf_recall, _ = precision_recall_curve(y_test, rf_scores)
rf_ap = average_precision_score(y_test, rf_scores)

# Baseline (random classifier) - horizontal line at positive class ratio
baseline = np.mean(y_test)

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#E74C3C"),  # Python Blue, Python Yellow, Red for baseline
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=32,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
    font_family="sans-serif",
)

# Create XY chart for precision-recall curve
chart = pygal.XY(
    width=4800,
    height=2700,
    title="precision-recall · pygal · pyplots.ai",
    x_title="Recall",
    y_title="Precision",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 5},
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=30,
    truncate_legend=-1,
    range=(0, 1),  # Y-axis range
    xrange=(0, 1),  # X-axis range
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    x_labels_major_every=2,
    y_labels_major_every=2,
)

# Downsample curves for cleaner visualization (inline, no helper function)
n_points = 100
lr_indices = np.linspace(0, len(lr_recall) - 1, n_points, dtype=int)
lr_recall_ds = lr_recall[lr_indices]
lr_precision_ds = lr_precision[lr_indices]

rf_indices = np.linspace(0, len(rf_recall) - 1, n_points, dtype=int)
rf_recall_ds = rf_recall[rf_indices]
rf_precision_ds = rf_precision[rf_indices]

# Create stepped data points for threshold-based visualization
# For each point, add horizontal segment first, then drop vertically
lr_stepped_points = []
for i in range(len(lr_recall_ds)):
    if i > 0:
        # Horizontal step: keep previous precision, move to current recall
        lr_stepped_points.append((lr_recall_ds[i], lr_precision_ds[i - 1]))
    # Vertical step: drop to current precision at current recall
    lr_stepped_points.append((lr_recall_ds[i], lr_precision_ds[i]))

rf_stepped_points = []
for i in range(len(rf_recall_ds)):
    if i > 0:
        # Horizontal step: keep previous precision, move to current recall
        rf_stepped_points.append((rf_recall_ds[i], rf_precision_ds[i - 1]))
    # Vertical step: drop to current precision at current recall
    rf_stepped_points.append((rf_recall_ds[i], rf_precision_ds[i]))

# Add Logistic Regression curve
chart.add(f"Logistic Regression (AP={lr_ap:.3f})", lr_stepped_points)

# Add Random Forest curve
chart.add(f"Random Forest (AP={rf_ap:.3f})", rf_stepped_points)

# Add baseline (random classifier) - horizontal line
baseline_points = [(0, baseline), (1, baseline)]
chart.add(f"Random Baseline ({baseline:.2f})", baseline_points, stroke_dasharray="10,5")

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
