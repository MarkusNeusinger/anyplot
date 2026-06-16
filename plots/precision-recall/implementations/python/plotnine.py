""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_step,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 for baseline

# Data - Simulated binary classification results
np.random.seed(42)
n_samples = 500

# Create realistic classification scenario (imbalanced - ~20% positive class)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])

# Generate scores: positive class gets higher scores on average
y_scores = np.where(
    y_true == 1,
    np.clip(np.random.beta(5, 2, size=n_samples), 0, 1),
    np.clip(np.random.beta(2, 5, size=n_samples), 0, 1),
)

# Calculate precision-recall curve
sorted_indices = np.argsort(y_scores)[::-1]
y_true_sorted = y_true[sorted_indices]
tp_cumsum = np.cumsum(y_true_sorted)
total_positives = y_true.sum()
n_predictions = np.arange(1, len(y_true_sorted) + 1)

precision = tp_cumsum / n_predictions
recall = tp_cumsum / total_positives

# Add start point (recall=0, precision=1)
precision = np.concatenate([[1], precision])
recall = np.concatenate([[0], recall])

# Calculate average precision (area under PR curve)
recall_diff = np.diff(recall)
ap_score = np.sum(recall_diff * precision[1:])

# Baseline (positive class ratio)
baseline = y_true.mean()

# Create DataFrame for plotting
df = pd.DataFrame({"Recall": recall, "Precision": precision})

# Plot
plot = (
    ggplot(df, aes(x="Recall", y="Precision"))
    + geom_step(color=BRAND, size=2, direction="vh")
    + geom_hline(yintercept=baseline, linetype="dashed", color=ACCENT, size=1.5)
    + annotate(
        "text",
        x=0.95,
        y=baseline + 0.05,
        label=f"Random Classifier (baseline = {baseline:.2f})",
        ha="right",
        size=14,
        color=ACCENT,
    )
    + annotate(
        "rect", xmin=0.55, xmax=0.95, ymin=0.75, ymax=0.95, fill=ELEVATED_BG, alpha=0.95, color=INK_SOFT, size=0.3
    )
    + annotate(
        "text", x=0.75, y=0.85, label=f"Average Precision (AP) = {ap_score:.3f}", size=16, color=INK, fontweight="bold"
    )
    + labs(
        x="Recall (Sensitivity)",
        y="Precision (Positive Predictive Value)",
        title="precision-recall · plotnine · anyplot.ai",
    )
    + scale_x_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        text=element_text(size=14),
        plot_title=element_text(size=24, color=INK, ha="center"),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
