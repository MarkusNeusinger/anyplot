"""anyplot.ai
silhouette-basic: Silhouette Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SEPAL_LENGTH = "Sepal length (cm)"  # role: samples
SEPAL_WIDTH = "Sepal width (cm)"  # role: extra
PETAL_LENGTH = "Petal length (cm)"  # role: extra
PETAL_WIDTH = "Petal width (cm)"  # role: extra
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("clustered_samples.csv")
iris = load_iris()
FEATURES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
df = pd.DataFrame(iris.data, columns=FEATURES)
df[CLUSTER] = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(df[FEATURES])
df[SILHOUETTE] = silhouette_samples(df[FEATURES], df[CLUSTER])

# Plot: reads only df and the constants above
GAP = 0.06 * len(df) / df[CLUSTER].nunique()  # blank rows between cluster blocks
silhouette_avg = df[SILHOUETTE].mean()
x_left = min(-0.2, df[SILHOUETTE].min() - 0.05)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

y_lower = GAP
for i, (cluster, rows) in enumerate(df.groupby(CLUSTER, sort=True)):
    values = np.sort(rows[SILHOUETTE].to_numpy())
    y_upper = y_lower + len(values)
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]

    # One horizontal bar per sample, sorted within the cluster
    ax.fill_betweenx(np.arange(y_lower, y_upper), 0, values, facecolor=color, edgecolor=color, alpha=0.8)

    # Annotate the cluster with its average silhouette score (x in axes fraction, y in data)
    ax.text(
        0.14,
        (y_lower + y_upper) / 2,
        f"Cluster {cluster}\n(avg: {values.mean():.2f})",
        transform=ax.get_yaxis_transform(),
        fontsize=8,
        va="center",
        ha="right",
        color=INK,
    )
    y_lower = y_upper + GAP

ax.axvline(silhouette_avg, color=INK_SOFT, linestyle="--", linewidth=1.8, label=f"Average score: {silhouette_avg:.2f}")

# Style
ax.set_title("silhouette-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(SILHOUETTE, fontsize=10, color=INK)
ax.set_ylabel("Samples, grouped by cluster", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.set_xlim(x_left, 1.0)
ax.set_ylim(0, y_lower)
ax.set_yticks([])

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

leg = ax.legend(fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

ax.grid(True, alpha=0.15, linestyle="-", axis="x", color=INK_SOFT, linewidth=0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
