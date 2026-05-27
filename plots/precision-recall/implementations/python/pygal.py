""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233")

# Data - Generate balanced binary classification dataset
np.random.seed(42)
X, y = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_classes=2,
    weights=[0.5, 0.5],  # Balanced: 50% class 0, 50% class 1
    flip_y=0.05,
    random_state=42,
)

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Train two classifiers for comparison
# Support Vector Machine
svm_model = SVC(kernel="rbf", probability=True, random_state=42, gamma="scale")
svm_model.fit(X_train, y_train)
svm_scores = svm_model.predict_proba(X_test)[:, 1]
svm_precision, svm_recall, _ = precision_recall_curve(y_test, svm_scores)
svm_ap = average_precision_score(y_test, svm_scores)

# Gradient Boosting
gb_model = GradientBoostingClassifier(n_estimators=50, max_depth=5, random_state=42)
gb_model.fit(X_train, y_train)
gb_scores = gb_model.predict_proba(X_test)[:, 1]
gb_precision, gb_recall, _ = precision_recall_curve(y_test, gb_scores)
gb_ap = average_precision_score(y_test, gb_scores)

# Baseline (random classifier) - horizontal line at positive class ratio
baseline = np.mean(y_test)

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create XY chart for precision-recall curve
chart = pygal.XY(
    width=4800,
    height=2700,
    title="precision-recall · pygal · anyplot.ai",
    x_title="Recall",
    y_title="Precision",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    range=(0, 1),
    xrange=(0, 1),
    show_minor_x_labels=False,
    show_minor_y_labels=False,
)

# Downsample curves for cleaner visualization
n_points = 100
svm_indices = np.linspace(0, len(svm_recall) - 1, n_points, dtype=int)
svm_recall_ds = svm_recall[svm_indices]
svm_precision_ds = svm_precision[svm_indices]

gb_indices = np.linspace(0, len(gb_recall) - 1, n_points, dtype=int)
gb_recall_ds = gb_recall[gb_indices]
gb_precision_ds = gb_precision[gb_indices]

# Create stepped data points for threshold-based visualization
svm_stepped_points = []
for i in range(len(svm_recall_ds)):
    if i > 0:
        svm_stepped_points.append((svm_recall_ds[i], svm_precision_ds[i - 1]))
    svm_stepped_points.append((svm_recall_ds[i], svm_precision_ds[i]))

gb_stepped_points = []
for i in range(len(gb_recall_ds)):
    if i > 0:
        gb_stepped_points.append((gb_recall_ds[i], gb_precision_ds[i - 1]))
    gb_stepped_points.append((gb_recall_ds[i], gb_precision_ds[i]))

# Add curves
chart.add(f"SVM (AP={svm_ap:.3f})", svm_stepped_points)
chart.add(f"Gradient Boosting (AP={gb_ap:.3f})", gb_stepped_points)

# Add baseline
baseline_points = [(0, baseline), (1, baseline)]
chart.add(f"Random Baseline ({baseline:.2f})", baseline_points, stroke_dasharray="10,5")

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
