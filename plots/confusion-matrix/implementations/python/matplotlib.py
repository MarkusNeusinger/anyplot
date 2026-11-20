"""anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential colormap runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns: set these to your table's column names
TRUE_LABEL = "True Label"  # role: true_labels
PREDICTED_LABEL = "Predicted Label"  # role: predicted_labels
CLASS_NAME = "Class Name"  # role: class_names

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.3, random_state=42)
clf = RandomForestClassifier(random_state=42).fit(X_train, y_train)
df = pd.DataFrame({TRUE_LABEL: y_test, PREDICTED_LABEL: clf.predict(X_test), CLASS_NAME: iris.target_names[y_test]})

# Plot: reads only df and the constants above
codes = sorted(set(df[TRUE_LABEL]) | set(df[PREDICTED_LABEL]))
names = dict(zip(df[TRUE_LABEL], df[CLASS_NAME], strict=True))
classes = [str(names.get(code, code)) for code in codes]
n_classes = len(classes)
matrix = pd.crosstab(df[TRUE_LABEL], df[PREDICTED_LABEL]).reindex(index=codes, columns=codes, fill_value=0)
counts = matrix.to_numpy()
row_share = counts / np.maximum(counts.sum(axis=1, keepdims=True), 1) * 100

title = "Iris Classifier · confusion-matrix · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.18)

im = ax.imshow(counts, cmap=imprint_seq, vmin=0, aspect="equal")

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cbar.ax.tick_params(labelsize=10, colors=INK_SOFT)
cbar.set_label("Count (% = share of true class)", fontsize=10, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_xticks(np.arange(n_classes), classes)
ax.set_yticks(np.arange(n_classes), classes)
ax.tick_params(axis="both", labelsize=12, colors=INK_SOFT, length=0)
plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

# Cell annotations: ink chosen from the luminance of the cell's own color
for i in range(n_classes):
    for j in range(n_classes):
        r, g, b, _ = imprint_seq(im.norm(counts[i, j]))
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        ax.text(
            j,
            i,
            f"{counts[i, j]}\n({row_share[i, j]:.0f}%)",
            ha="center",
            va="center",
            color="#1A1A17" if luminance > 0.3 else "#FFFDF6",
            fontsize=12,
            fontweight="bold",
        )

# Cell borders, drawn on the page background so cells read as separate tiles
ax.set_xticks(np.arange(n_classes + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n_classes + 1) - 0.5, minor=True)
ax.grid(which="minor", color=PAGE_BG, linewidth=2.5)
ax.tick_params(which="minor", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_xlabel(PREDICTED_LABEL, fontsize=13, color=INK, labelpad=8)
ax.set_ylabel(TRUE_LABEL, fontsize=13, color=INK, labelpad=8)
fig.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.96)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
