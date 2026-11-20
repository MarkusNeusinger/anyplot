"""anyplot.ai
silhouette-basic: Silhouette Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from sklearn.cluster import KMeans
from sklearn.datasets import load_wine
from sklearn.metrics import silhouette_samples
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FLAVANOIDS = "flavanoids"  # role: samples
COLOR = "color_intensity"  # role: extra
PROLINE = "proline"  # role: extra
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("silhouettes.csv")
# Wine chemistry (178 samples, 3 measurements), standardized and clustered with K-means (k = 4)
df = load_wine(as_frame=True).frame[[FLAVANOIDS, COLOR, PROLINE]]
features = StandardScaler().fit_transform(df)
labels = KMeans(n_clusters=4, random_state=7, n_init=10).fit_predict(features)
df[CLUSTER] = [f"Cluster {label + 1}" for label in labels]
df[SILHOUETTE] = silhouette_samples(features, labels)

# Plot: reads only df and the constants above
GAP = 6  # empty rows between cluster blocks
df = df.sort_values([CLUSTER, SILHOUETTE], kind="stable").reset_index(drop=True)
cluster_names = df[CLUSTER].unique().tolist()
block_index = df[CLUSTER].map({name: i for i, name in enumerate(cluster_names)})
df["row"] = np.arange(len(df)) + block_index * GAP

avg_score = df[SILHOUETTE].mean()
x_min = min(0.0, df[SILHOUETTE].min())
x_max = df[SILHOUETTE].max()
label_x = x_max + 0.04

summary = df.groupby(CLUSTER, sort=False).agg(row=("row", "mean"), avg=(SILHOUETTE, "mean"), n=(SILHOUETTE, "size"))
summary = summary.reset_index()
summary["label"] = [
    f"{c}\navg {a:.2f} (n={n})" for c, a, n in zip(summary[CLUSTER], summary["avg"], summary["n"], strict=True)
]
summary["x"] = label_x

avg_label = pd.DataFrame({"x": [avg_score + 0.01], "y": [df["row"].max()], "label": [f"Overall avg {avg_score:.2f}"]})

plot = (
    ggplot()
    + geom_segment(aes(x=0, xend=SILHOUETTE, y="row", yend="row", color=CLUSTER), data=df, size=0.9)
    + geom_vline(xintercept=avg_score, color=INK, linetype="dashed", size=0.6)
    + geom_text(aes(x="x", y="row", label="label"), data=summary, size=8, ha="left", color=INK, lineheight=1.0)
    + geom_text(aes(x="x", y="y", label="label"), data=avg_label, size=7, ha="left", va="bottom", color=INK_SOFT)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=cluster_names)
    + scale_x_continuous(limits=(x_min - 0.05, x_max + 0.4), breaks=np.round(np.arange(-0.2, x_max + 0.1, 0.1), 1))
    + labs(x=SILHOUETTE, y="Samples (sorted within cluster)", title="silhouette-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.12),
        panel_border=element_blank(),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
