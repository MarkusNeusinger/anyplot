""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggsave
from sklearn.metrics import auc, roc_curve


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#1A1A17" if THEME == "light" else "#F0EFE8"
NEUTRAL = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FPR = "False positive rate"  # role: fpr
TPR = "True positive rate"  # role: tpr
AUC = "AUC"  # role: auc
MODEL = "Classifier"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("roc_points.csv")
# with one row per ROC point, the classifier name and its AUC.
rng = np.random.default_rng(42)
n_per_class = 400
outcome = np.repeat([0, 1], n_per_class)
curves = []
for name, (a_neg, b_neg, a_pos, b_pos) in {
    "Gradient boosting": (2, 6, 5, 2.5),
    "Logistic model": (2, 3.5, 3.5, 2.5),
}.items():
    scores = np.concatenate([rng.beta(a_neg, b_neg, n_per_class), rng.beta(a_pos, b_pos, n_per_class)])
    fpr, tpr, _ = roc_curve(outcome, scores)
    curves.append(pd.DataFrame({FPR: fpr, TPR: tpr, MODEL: name, AUC: auc(fpr, tpr)}))
curves.append(pd.DataFrame({FPR: [0.0, 1.0], TPR: [0.0, 1.0], MODEL: "Random guess", AUC: 0.5}))
df = pd.concat(curves, ignore_index=True)

# Plot
df["label"] = [f"{name} (AUC = {score:.2f})" for name, score in zip(df[MODEL], df[AUC])]
series = list(df["label"].unique())
colors = IMPRINT_PALETTE[: len(series) - 1] + [NEUTRAL]
linetypes = ["solid"] * (len(series) - 1) + ["dashed"]

plot = (
    ggplot(df, aes(x=FPR, y=TPR, color="label", linetype="label"))
    + geom_path(size=1.6)
    + scale_color_manual(values=colors, breaks=series)
    + scale_linetype_manual(values=linetypes, breaks=series)
    + scale_x_continuous(limits=[0, 1], expand=[0, 0.01])
    + scale_y_continuous(limits=[0, 1], expand=[0, 0.01])
    + coord_fixed(ratio=1)
    + labs(
        title="Credit Default Risk · roc-curve · python · letsplot · anyplot.ai",
        color="Classifier",
        linetype="Classifier",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.2),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=14, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_position=[0.97, 0.04],
        legend_justification=[1, 0],
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
