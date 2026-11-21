""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, to_rgb


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential Imprint colormap for single-polarity count data
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

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

# Columns: set these to your table's labels
TRUE_LABEL = "True Label"  # role: true_labels
PREDICTED_LABEL = "Predicted Label"  # role: predicted_labels

# Data: replace this block with your own labeled square matrix (rows = true class, columns = predicted class),
# for example df = pd.crosstab(y_true, y_pred)
# Plant disease classifier on leaf photos: five classes, strong diagonal, systematic rust/blight confusion
class_names = ["Healthy", "Leaf Rust", "Blight", "Mildew", "Mosaic Virus"]
df = pd.DataFrame(
    [
        [184, 4, 3, 6, 2],  # Healthy: rarely flagged as diseased
        [7, 131, 21, 5, 3],  # Leaf Rust: often mistaken for Blight
        [5, 24, 118, 4, 6],  # Blight: mirror confusion with Rust
        [9, 6, 3, 142, 2],  # Mildew: occasionally read as Healthy
        [3, 2, 7, 3, 87],  # Mosaic Virus: rare class, fewest samples
    ],
    index=pd.Index(class_names, name=TRUE_LABEL),
    columns=pd.Index(class_names, name=PREDICTED_LABEL),
)

# Plot
title = "Plant Disease Classifier · confusion-matrix · python · seaborn · anyplot.ai"
title_fontsize = round(12 * min(1.0, 67 / len(title)))

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(
    df.astype(float),
    annot=True,
    fmt=".0f",
    cmap=imprint_seq,
    square=True,
    linewidths=1.5,
    linecolor=PAGE_BG,
    cbar_kws={"shrink": 0.78, "pad": 0.03},
    annot_kws={"size": 11, "weight": "bold"},
    ax=ax,
)


# Annotation color per cell: whichever of light/dark ink contrasts better with the cell color
def _luminance(color):
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


values = df.astype(float).to_numpy()
norm_values = (values - np.nanmin(values)) / (np.nanmax(values) - np.nanmin(values))
for text, value in zip(ax.texts, norm_values.ravel(), strict=True):
    lum = _luminance(imprint_seq(value))
    contrast_light = 1.05 / (lum + 0.05)
    contrast_dark = (lum + 0.05) / 0.06
    text.set_color("#FFFFFF" if contrast_light >= contrast_dark else "#1A1A17")

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=9, colors=INK_SOFT)
cbar.ax.set_ylabel("Count", fontsize=10, labelpad=8, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_xlabel(df.columns.name, fontsize=11, labelpad=8, color=INK)
ax.set_ylabel(df.index.name, fontsize=11, labelpad=8, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", pad=14, color=INK)
ax.tick_params(axis="both", labelsize=9, colors=INK_SOFT)
plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
plt.setp(ax.get_yticklabels(), rotation=0)

fig.subplots_adjust(left=0.22, right=0.93, top=0.92, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
