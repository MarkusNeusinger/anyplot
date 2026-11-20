"""anyplot.ai
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

# Imprint palette: position 1 for the model curve, position 2 for the baseline
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
Y_TRUE = "True label"  # role: y_true
Y_SCORES = ["Predicted score"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 500
# Imbalanced classification: about 20% positive class
labels = rng.choice([0, 1], size=n_samples, p=[0.8, 0.2])
# Positive class scores higher on average
scores = np.where(labels == 1, rng.beta(5, 2, size=n_samples), rng.beta(2, 5, size=n_samples))
df = pd.DataFrame({Y_TRUE: labels, Y_SCORES[0]: scores})

# Plot: reads only df and the constants above
RECALL = "Recall (Sensitivity)"
PRECISION = "Precision (Positive Predictive Value)"

ranked = df.sort_values(Y_SCORES[0], ascending=False)
true_positives = ranked[Y_TRUE].cumsum().to_numpy()
n_predicted = np.arange(1, len(ranked) + 1)
curve = pd.DataFrame(
    {
        RECALL: np.concatenate([[0.0], true_positives / df[Y_TRUE].sum()]),
        PRECISION: np.concatenate([[1.0], true_positives / n_predicted]),
    }
)

# Average precision: precision weighted by each recall increment
ap_score = float(np.sum(np.diff(curve[RECALL]) * curve[PRECISION].to_numpy()[1:]))

# Baseline: a random classifier sits at the positive class ratio
baseline = float(df[Y_TRUE].mean())

plot = (
    ggplot(curve, aes(x=RECALL, y=PRECISION))
    + geom_step(color=IMPRINT_PALETTE[0], size=1.2, direction="vh")
    + geom_hline(yintercept=baseline, linetype="dashed", color=IMPRINT_PALETTE[1], size=0.9)
    + annotate(
        "text",
        x=0.95,
        y=baseline + 0.05,
        label=f"Random classifier (baseline = {baseline:.2f})",
        ha="right",
        size=8,
        color=INK,
    )
    + annotate(
        "rect", xmin=0.08, xmax=0.53, ymin=0.45, ymax=0.63, fill=ELEVATED_BG, alpha=0.95, color=INK_SOFT, size=0.3
    )
    + annotate(
        "text", x=0.305, y=0.54, label=f"Average Precision (AP) = {ap_score:.3f}", size=9, color=INK, fontweight="bold"
    )
    + labs(title="precision-recall · python · plotnine · anyplot.ai")
    + scale_x_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=(0, 1), breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        text=element_text(size=7),
        plot_title=element_text(size=12, color=INK, ha="center"),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
