""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulate ROC curves for two classifiers
np.random.seed(42)

# Generate predictions for a good model (AUC ~0.92)
y_true = np.array([0] * 100 + [1] * 100)
y_scores_good = np.concatenate(
    [
        np.random.beta(2, 5, 100),  # Negatives - lower scores
        np.random.beta(5, 2, 100),  # Positives - higher scores
    ]
)

# Generate predictions for an average model (AUC ~0.78)
y_scores_avg = np.concatenate(
    [
        np.random.beta(2, 3, 100),  # Negatives
        np.random.beta(3, 2, 100),  # Positives
    ]
)

# Compute ROC points for good model
thresholds = np.linspace(1, 0, 100)
tpr_good = []
fpr_good = []
for thresh in thresholds:
    y_pred = (y_scores_good >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr_good.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr_good.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr_good = np.array(fpr_good)
tpr_good = np.array(tpr_good)

# Compute ROC points for average model
tpr_avg = []
fpr_avg = []
for thresh in thresholds:
    y_pred = (y_scores_avg >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr_avg.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr_avg.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr_avg = np.array(fpr_avg)
tpr_avg = np.array(tpr_avg)

# Compute AUC using trapezoidal rule
sorted_idx_good = np.argsort(fpr_good)
auc_good = np.trapezoid(tpr_good[sorted_idx_good], fpr_good[sorted_idx_good])

sorted_idx_avg = np.argsort(fpr_avg)
auc_avg = np.trapezoid(tpr_avg[sorted_idx_avg], fpr_avg[sorted_idx_avg])

# Create custom style for pyplots.ai (scaled for 4800x2700 canvas)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#888888"),  # Python Blue, Python Yellow, Gray
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=30,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart for ROC curve (XY allows arbitrary x,y points)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="roc-curve · pygal · pyplots.ai",
    x_title="False Positive Rate",
    y_title="True Positive Rate",
    show_dots=False,
    stroke_style={"width": 5},
    range=(0, 1),
    xrange=(0, 1),
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=False,
    legend_box_size=32,
    truncate_legend=-1,
    dots_size=0,
    fill=False,
    interpolate=None,
)

# Prepare data points for pygal XY chart (list of tuples)
# Good model ROC curve
points_good = list(zip(fpr_good.tolist(), tpr_good.tolist(), strict=True))
chart.add(f"Model A (AUC = {auc_good:.2f})", points_good)

# Average model ROC curve
points_avg = list(zip(fpr_avg.tolist(), tpr_avg.tolist(), strict=True))
chart.add(f"Model B (AUC = {auc_avg:.2f})", points_avg)

# Random classifier reference line (diagonal)
diagonal = [(0, 0), (1, 1)]
chart.add("Random (AUC = 0.50)", diagonal, stroke_dasharray="10,5")

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
