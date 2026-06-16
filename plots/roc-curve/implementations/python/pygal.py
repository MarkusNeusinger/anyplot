""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Simulate ROC curves for three classifiers with different AUC scores
np.random.seed(42)

# Generate predictions for an excellent model (AUC ~0.95)
y_true = np.array([0] * 100 + [1] * 100)
y_scores_excellent = np.concatenate(
    [
        np.random.beta(1.5, 6, 100),  # Negatives - lower scores
        np.random.beta(6, 1.5, 100),  # Positives - higher scores
    ]
)

# Generate predictions for a moderate model (AUC ~0.70)
y_scores_moderate = np.concatenate(
    [
        np.random.beta(2.5, 2.5, 100),  # Negatives
        np.random.beta(2.8, 2.2, 100),  # Positives
    ]
)

# Generate predictions for a poor model (AUC ~0.60)
y_scores_poor = np.concatenate(
    [
        np.random.beta(2.5, 2.0, 100),  # Negatives
        np.random.beta(2.2, 2.5, 100),  # Positives
    ]
)

# Compute ROC points for excellent model
thresholds = np.linspace(1, 0, 100)
tpr_excellent = []
fpr_excellent = []
for thresh in thresholds:
    y_pred = (y_scores_excellent >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr_excellent.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr_excellent.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr_excellent = np.array(fpr_excellent)
tpr_excellent = np.array(tpr_excellent)

# Compute ROC points for moderate model
tpr_moderate = []
fpr_moderate = []
for thresh in thresholds:
    y_pred = (y_scores_moderate >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr_moderate.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr_moderate.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr_moderate = np.array(fpr_moderate)
tpr_moderate = np.array(tpr_moderate)

# Compute ROC points for poor model
tpr_poor = []
fpr_poor = []
for thresh in thresholds:
    y_pred = (y_scores_poor >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr_poor.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr_poor.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr_poor = np.array(fpr_poor)
tpr_poor = np.array(tpr_poor)

# Compute AUC using trapezoidal rule
sorted_idx_excellent = np.argsort(fpr_excellent)
auc_excellent = np.trapezoid(tpr_excellent[sorted_idx_excellent], fpr_excellent[sorted_idx_excellent])

sorted_idx_moderate = np.argsort(fpr_moderate)
auc_moderate = np.trapezoid(tpr_moderate[sorted_idx_moderate], fpr_moderate[sorted_idx_moderate])

sorted_idx_poor = np.argsort(fpr_poor)
auc_poor = np.trapezoid(tpr_poor[sorted_idx_poor], fpr_poor[sorted_idx_poor])

# Create custom style for anyplot.ai (scaled for 4800x2700 canvas)
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

# Create XY chart for ROC curve
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="roc-curve · pygal · anyplot.ai",
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

# Prepare data points for pygal XY chart
points_excellent = list(zip(fpr_excellent.tolist(), tpr_excellent.tolist(), strict=True))
chart.add(f"Excellent (AUC = {auc_excellent:.2f})", points_excellent)

points_moderate = list(zip(fpr_moderate.tolist(), tpr_moderate.tolist(), strict=True))
chart.add(f"Moderate (AUC = {auc_moderate:.2f})", points_moderate)

points_poor = list(zip(fpr_poor.tolist(), tpr_poor.tolist(), strict=True))
chart.add(f"Poor (AUC = {auc_poor:.2f})", points_poor)

# Random classifier reference line (diagonal)
diagonal = [(0, 0), (1, 1)]
chart.add("Random (AUC = 0.50)", diagonal, stroke_dasharray="10,5")

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
