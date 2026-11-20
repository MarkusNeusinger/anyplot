"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the curve, position 2 for the highlighted optimum
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
K = "Number of Clusters (k)"  # role: k_values
INERTIA = "Inertia (Within-Cluster Sum of Squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("inertia.csv")
# Simulated K-means inertia on a customer segmentation dataset, elbow near k=4
df = pd.DataFrame({K: list(range(1, 11)), INERTIA: [12500, 6800, 3900, 2100, 1800, 1550, 1380, 1250, 1150, 1080]})

# Plot: reads only df and the constants above
# Elbow rule: the k where the drop before it is largest relative to the drop after it
drops = -np.diff(df[INERTIA].to_numpy(dtype=float, na_value=np.nan))
with np.errstate(divide="ignore", invalid="ignore"):
    ratios = drops[:-1] / drops[1:]
if np.isfinite(ratios).any():
    optimal = df.iloc[[int(np.nanargmax(np.where(np.isfinite(ratios), ratios, np.nan))) + 1]].copy()
else:
    optimal = df.iloc[0:0].copy()
optimal["label"] = [f"Elbow: k = {k:g}" for k in optimal[K].astype(float)]

plot = ggplot(df, aes(x=K, y=INERTIA))
if len(optimal):
    plot = (
        plot
        + geom_vline(
            data=optimal, mapping=aes(xintercept=K), linetype="dashed", color=IMPRINT_PALETTE[1], size=0.8, alpha=0.8
        )
        + geom_line(size=1.2, color=IMPRINT_PALETTE[0])
        + geom_point(size=4, color=IMPRINT_PALETTE[0], stroke=1, fill=PAGE_BG, shape=21)
        + geom_point(data=optimal, mapping=aes(x=K, y=INERTIA), size=9, color=IMPRINT_PALETTE[1], shape=18)
        + geom_text(
            data=optimal,
            mapping=aes(x=K, y=INERTIA, label="label"),
            color=INK,
            size=6,
            hjust=0,
            nudge_x=0.15,
            nudge_y=df[INERTIA].max() * 0.12,
            fontface="bold",
        )
    )
else:
    plot = (
        plot
        + geom_line(size=1.2, color=IMPRINT_PALETTE[0])
        + geom_point(size=4, color=IMPRINT_PALETTE[0], stroke=1, fill=PAGE_BG, shape=21)
    )
plot = (
    plot
    + labs(title="elbow-curve · python · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=df[K].tolist())
    + scale_y_continuous(limits=[0, df[INERTIA].max() * 1.05])
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.2),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
    )
    + ggsize(800, 450)
)

# Output
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
