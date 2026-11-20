""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-20
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
F1_LEVELS = [0.2, 0.4, 0.6, 0.8]  # iso-F1 reference contours

# Columns: set these to your table's column names
Y_TRUE = "y_true"  # role: y_true
Y_SCORES = ["y_score"]  # role: y_scores
RECALL = "Recall (Sensitivity)"  # role: extra
PRECISION = "Precision (PPV)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
np.random.seed(42)
n_positive = 100  # imbalanced: 20% positive
n_negative = 400
df = pd.DataFrame(
    {
        Y_TRUE: np.concatenate([np.ones(n_positive), np.zeros(n_negative)]),
        Y_SCORES[0]: np.concatenate([np.random.beta(5, 2, n_positive), np.random.beta(2, 5, n_negative)]),
    }
)

# Plot: reads only df and the constants above
positive_ratio = df[Y_TRUE].mean()

# Precision and recall at every distinct score threshold
order = np.argsort(df[Y_SCORES[0]].to_numpy())[::-1]
scores_sorted = df[Y_SCORES[0]].to_numpy()[order]
true_sorted = df[Y_TRUE].to_numpy()[order]
threshold_idxs = np.concatenate([[0], np.where(np.diff(scores_sorted))[0] + 1])
tps = np.cumsum(true_sorted)
fps = np.cumsum(1 - true_sorted)
precision = np.concatenate([[1], (tps / (tps + fps))[threshold_idxs]])
recall = np.concatenate([[0], (tps / tps[-1])[threshold_idxs]])

# Average Precision: step-wise area under the curve
average_precision = np.sum(precision[1:] * np.diff(recall))

# Stepped line: hold each precision until the next recall value
df_curve = pd.DataFrame(
    {
        RECALL: np.repeat(recall, 2)[1:],
        PRECISION: np.repeat(precision, 2)[:-1],
        "model": f"Classifier (AP = {average_precision:.3f})",
    }
)

# Iso-F1 contours and their end labels
f1_rows = []
f1_labels = []
for f1 in F1_LEVELS:
    x = np.linspace(f1 / 2 + 0.01, 1, 100)
    y = f1 * x / (2 * x - f1)
    keep = (y >= 0) & (y <= 1)
    f1_rows.append(pd.DataFrame({RECALL: x[keep], PRECISION: y[keep], "f1": f"F1={f1:.1f}"}))
    if keep.any():
        f1_labels.append({RECALL: x[keep][-1] - 0.035, PRECISION: y[keep][-1] + 0.025, "label": f"F1={f1:.1f}"})
df_f1 = pd.concat(f1_rows)
df_f1_labels = pd.DataFrame(f1_labels)

df_baseline = pd.DataFrame(
    {
        RECALL: [df_curve[RECALL].max() * 0.2],
        PRECISION: [positive_ratio + 0.03],
        "label": [f"Random Baseline ({positive_ratio:.0%})"],
    }
)

plot = (
    ggplot()
    # Iso-F1 curves (background)
    + geom_line(
        data=df_f1,
        mapping=aes(x=RECALL, y=PRECISION, group="f1"),
        color=INK_SOFT,
        alpha=0.3,
        size=0.6,
        linetype="dotted",
    )
    + geom_text(data=df_f1_labels, mapping=aes(x=RECALL, y=PRECISION, label="label"), color=INK_MUTED, size=4)
    # Main precision-recall curve
    + geom_area(data=df_curve, mapping=aes(x=RECALL, y=PRECISION), fill=IMPRINT_PALETTE[0], alpha=0.2)
    + geom_line(data=df_curve, mapping=aes(x=RECALL, y=PRECISION, color="model"), size=1.0)
    # Baseline: random classifier
    + geom_hline(yintercept=positive_ratio, color=IMPRINT_PALETTE[1], size=0.8, linetype="dashed")
    + geom_text(data=df_baseline, mapping=aes(x=RECALL, y=PRECISION, label="label"), color=INK_SOFT, size=5)
    + labs(title="precision-recall · python · letsplot · anyplot.ai", color="")
    + scale_x_continuous(limits=[0, 1.0])
    + scale_y_continuous(limits=[0, 1.05])
    + scale_color_manual(values=IMPRINT_PALETTE)
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="top",
    )
)

# Save PNG (scale 4 = 3200 x 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
