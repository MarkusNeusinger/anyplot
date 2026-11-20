"""anyplot.ai
silhouette-basic: Silhouette Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 6  # empty rows between two cluster blocks

# Columns: set these to your table's column names
FEATURE = "Petal length (cm)"  # role: samples
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("silhouettes.csv")
X = load_iris().data
labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X)
df = pd.DataFrame(
    {FEATURE: X[:, 2], CLUSTER: [f"Cluster {k}" for k in labels], SILHOUETTE: silhouette_samples(X, labels)}
)

# Plot: reads only df and the constants above
df = df.sort_values([CLUSTER, SILHOUETTE]).reset_index(drop=True)
block = pd.factorize(df[CLUSTER], sort=True)[0]
df["row"] = np.arange(len(df)) + block * GAP

overall = df[SILHOUETTE].mean()
floor = min(0.0, df[SILHOUETTE].min())
label_x = floor - 0.03

summary = df.groupby(CLUSTER, sort=False).agg(row=("row", "mean"), avg=(SILHOUETTE, "mean")).reset_index()
summary["x"] = label_x
summary["label"] = [f"{name}\n(avg: {avg:.2f})" for name, avg in zip(summary[CLUSTER], summary["avg"])]

avg_label = pd.DataFrame({"x": [overall + 0.03], "row": [df["row"].max()], "label": [f"Avg: {overall:.2f}"]})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_line(color=INK, size=0.3),
    panel_grid_minor_x=element_line(color=INK, size=0.2),
    panel_grid_major_y=element_blank(),
    panel_grid_minor_y=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text_x=element_text(size=10, color=INK_SOFT),
    axis_text_y=element_blank(),
    axis_ticks_y=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=16, color=INK),
    legend_position="right",
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
)

plot = (
    ggplot(df, aes(x=SILHOUETTE, y="row", color=CLUSTER))
    + geom_segment(aes(xend=SILHOUETTE, yend="row"), x=0, size=0.8)
    + geom_vline(xintercept=overall, color=INK_SOFT, linetype="dashed", size=0.8)
    + geom_text(aes(x="x", y="row", label="label"), data=summary, size=4, hjust=1, color=INK_SOFT)
    + geom_text(aes(x="x", y="row", label="label"), data=avg_label, size=4, hjust=0, color=INK_SOFT)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(limits=[floor - 0.4, df[SILHOUETTE].max() + 0.05])
    + labs(x=SILHOUETTE, y="Sample (sorted within cluster)", title="silhouette-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
