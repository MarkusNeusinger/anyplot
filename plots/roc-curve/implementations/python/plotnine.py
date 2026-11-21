"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-09
"""

import os
import sys

import numpy as np
import pandas as pd


# Prevent import of local file by removing current dir from path
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
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

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FPR = "False Positive Rate"  # role: fpr
TPR = "True Positive Rate"  # role: tpr
AUC = "AUC"  # role: auc
MODEL = "Model"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("roc.csv")
np.random.seed(42)
thresholds = np.linspace(0, 1, 200)
exponents = {"Random Forest": (2.5, 0.4), "Logistic Regression": (1.8, 0.7)}
frames = []
for name, (fpr_exp, tpr_exp) in exponents.items():
    fpr = np.concatenate([[0], np.power(thresholds[1:-1], fpr_exp), [1]])
    tpr = np.concatenate([[0], np.power(thresholds[1:-1], tpr_exp), [1]])
    frames.append(pd.DataFrame({FPR: fpr, TPR: tpr, AUC: np.trapezoid(tpr, fpr), MODEL: name}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
labels = df[MODEL].astype(str) + " (AUC = " + df[AUC].round(2).astype(str) + ")"
df["Legend"] = pd.Categorical(labels, categories=labels.dropna().unique().tolist())

# Theme-adaptive style
anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    legend_position=(0.97, 0.05),
    legend_key_width=24,
)

plot = (
    ggplot(df, aes(x=FPR, y=TPR, color="Legend"))
    + geom_abline(intercept=0, slope=1, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.6)
    + geom_line(size=1.2, alpha=0.95)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=df["Legend"].cat.categories.tolist())
    + scale_x_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + coord_fixed(ratio=1)
    + labs(title="roc-curve · python · plotnine · anyplot.ai", color=MODEL)
    + theme_minimal()
    + anyplot_theme
    + annotate(
        "text",
        x=0.3,
        y=0.36,
        label="Diagonal = Random Classifier",
        size=7,
        color=INK_SOFT,
        fontstyle="italic",
        angle=45,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6)
