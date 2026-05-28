""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
BRAND = "#009E73"
SECONDARY = "#C475FD"

# Generate synthetic classification data with imbalanced classes
np.random.seed(42)
n_samples = 500

# Simulate imbalanced dataset: 20% positive, 80% negative
positive_ratio = 0.2
n_positive = int(n_samples * positive_ratio)
n_negative = n_samples - n_positive

# True labels
y_true = np.concatenate([np.ones(n_positive), np.zeros(n_negative)])

# Simulate classifier scores - good classifier gives higher scores to positives
positive_scores = np.random.beta(5, 2, n_positive)  # Skewed higher
negative_scores = np.random.beta(2, 5, n_negative)  # Skewed lower
y_scores = np.concatenate([positive_scores, negative_scores])

# Calculate precision-recall curve
# Sort by scores descending
desc_score_indices = np.argsort(y_scores)[::-1]
y_scores_sorted = y_scores[desc_score_indices]
y_true_sorted = y_true[desc_score_indices]

# Get unique thresholds
distinct_value_indices = np.where(np.diff(y_scores_sorted))[0]
threshold_idxs = np.concatenate([[0], distinct_value_indices + 1])

# Calculate TP, FP cumulative sums
tps = np.cumsum(y_true_sorted)
fps = np.cumsum(1 - y_true_sorted)

# Calculate precision and recall at each threshold
precision_vals = tps / (tps + fps)
recall_vals = tps / tps[-1]

# Use thresholds at distinct values (add starting point: recall=0, precision=1)
precision = np.concatenate([[1], precision_vals[threshold_idxs]])
recall = np.concatenate([[0], recall_vals[threshold_idxs]])

# Calculate Average Precision (area under curve)
recall_diff = np.diff(recall)
average_precision = np.sum(precision[1:] * recall_diff)

# Create step-wise data for proper step visualization
recall_step = []
precision_step = []
for i in range(len(recall) - 1):
    recall_step.extend([recall[i], recall[i + 1]])
    precision_step.extend([precision[i], precision[i]])
recall_step.append(recall[-1])
precision_step.append(precision[-1])

df_curve = pd.DataFrame(
    {"recall": recall_step, "precision": precision_step, "model": f"Classifier (AP = {average_precision:.3f})"}
)

# Create iso-F1 curves data
f1_scores = [0.2, 0.4, 0.6, 0.8]
f1_data = []
for f1_score in f1_scores:
    x = np.linspace(f1_score / 2 + 0.01, 1, 100)
    y = f1_score * x / (2 * x - f1_score)
    mask = (y >= 0) & (y <= 1)
    for xi, yi in zip(x[mask], y[mask], strict=False):
        f1_data.append({"recall": xi, "precision": yi, "f1": f"F1={f1_score:.1f}"})

df_f1 = pd.DataFrame(f1_data)

# Labels for iso-F1 curves (at the end of each curve)
f1_labels = []
for f1_score in f1_scores:
    x = np.linspace(f1_score / 2 + 0.01, 1, 100)
    y = f1_score * x / (2 * x - f1_score)
    mask = (y >= 0) & (y <= 1)
    if np.any(mask):
        f1_labels.append({"recall": x[mask][-1] + 0.01, "precision": y[mask][-1], "label": f"F1={f1_score:.1f}"})

df_f1_labels = pd.DataFrame(f1_labels)

# Build the plot
plot = (
    ggplot()
    # Iso-F1 curves (background)
    + geom_line(
        data=df_f1,
        mapping=aes(x="recall", y="precision", group="f1"),
        color=INK_SOFT,
        alpha=0.3,
        size=1,
        linetype="dotted",
    )
    # F1 labels
    + geom_text(
        data=df_f1_labels, mapping=aes(x="recall", y="precision", label="label"), color=INK_MUTED, size=10, alpha=0.6
    )
    # Main precision-recall curve
    + geom_area(data=df_curve, mapping=aes(x="recall", y="precision"), fill=BRAND, alpha=0.2)
    + geom_line(data=df_curve, mapping=aes(x="recall", y="precision", color="model"), size=1.5)
    # Baseline: random classifier
    + geom_hline(yintercept=positive_ratio, color=SECONDARY, size=1.2, linetype="dashed")
    + geom_text(
        data=pd.DataFrame(
            {"x": [0.85], "y": [positive_ratio + 0.03], "label": [f"Random Baseline ({positive_ratio:.0%})"]}
        ),
        mapping=aes(x="x", y="y", label="label"),
        color=INK_SOFT,
        size=12,
    )
    # Labels and title
    + labs(x="Recall (Sensitivity)", y="Precision (PPV)", title="precision-recall · letsplot · anyplot.ai", color="")
    + scale_x_continuous(limits=[0, 1.0])
    + scale_y_continuous(limits=[0, 1.05])
    + scale_color_manual(values=[BRAND])
    # Size for 4800x2700 at scale=3
    + ggsize(1600, 900)
    # Theme
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="top",
    )
)

# Save as PNG (scale 3x = 4800 x 2700 px) and HTML
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
