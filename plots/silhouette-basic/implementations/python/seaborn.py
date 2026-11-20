"""anyplot.ai
silhouette-basic: Silhouette Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Set seaborn theme
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
SPENDING = "Annual spending (USD)"  # role: samples
FREQUENCY = "Purchases per year"  # role: extra
RECENCY = "Days since last purchase"  # role: extra
CLUSTER = "Cluster"  # role: cluster_labels
FEATURES = [SPENDING, FREQUENCY, RECENCY]

# Data: replace this block with your own table, for example df = pd.read_csv("customers.csv")
np.random.seed(42)
spending = np.concatenate(
    [
        np.random.normal(1500, 300, 60),  # High spenders
        np.random.normal(800, 200, 90),  # Medium spenders
        np.random.normal(200, 100, 50),  # Low spenders
    ]
)
frequency = np.concatenate([np.random.normal(24, 5, 60), np.random.normal(12, 4, 90), np.random.normal(3, 2, 50)])
recency = np.concatenate([np.random.normal(5, 10, 60), np.random.normal(20, 15, 90), np.random.normal(60, 30, 50)])
features = np.column_stack([spending, frequency, recency])
labels = KMeans(n_clusters=3, random_state=123, n_init=10).fit_predict(features)
df = pd.DataFrame(features, columns=FEATURES)
df[CLUSTER] = labels

# Plot: reads only df and the constants above
complete = df.dropna(subset=[*FEATURES, CLUSTER])  # rows with a missing value cannot be scored
X = complete[FEATURES].to_numpy()
silhouette_vals = silhouette_samples(X, complete[CLUSTER])
avg_score = silhouette_score(X, complete[CLUSTER])
clusters = sorted(complete[CLUSTER].unique())
gap = 0.05 * len(complete)  # blank rows between cluster blocks
left = min(0.0, np.nanmin(silhouette_vals)) - 0.15

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

y_lower = gap
for i, cluster in enumerate(clusters):
    vals = np.sort(silhouette_vals[(complete[CLUSTER] == cluster).to_numpy()])
    y_positions = np.arange(y_lower, y_lower + len(vals))

    ax.barh(
        y_positions,
        vals,
        height=1.0,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        edgecolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        alpha=0.85,
        label=f"Cluster {cluster}",
    )
    ax.text(
        left + 0.02,
        y_positions.mean(),
        f"C{cluster}\n{np.nanmean(vals):.2f}",
        fontsize=8,
        fontweight="medium",
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        va="center",
        ha="left",
    )
    y_lower = y_positions[-1] + 1 + gap

# Average silhouette line
ax.axvline(avg_score, color=INK_SOFT, linestyle="--", linewidth=1.5, label=f"Average: {avg_score:.3f}")

# Style
ax.set_xlim(left, 1.0)
ax.set_ylim(0, y_lower)
ax.set_xlabel("Silhouette Coefficient", fontsize=10, color=INK)
ax.set_ylabel("Samples (grouped by cluster)", fontsize=10, color=INK)
ax.set_title("silhouette-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.set_yticks([])
sns.despine(ax=ax, left=True)
ax.grid(axis="x", alpha=0.15, linewidth=0.5, color=INK)

legend = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=len(clusters) + 1, fontsize=8, frameon=True)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

fig.subplots_adjust(left=0.07, right=0.97, top=0.92, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
