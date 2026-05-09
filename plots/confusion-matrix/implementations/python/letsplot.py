"""anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-12-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Multi-class classification results for image classifier
np.random.seed(42)

class_names = ["Cat", "Dog", "Bird", "Fish"]
n_classes = len(class_names)

# Create a realistic confusion matrix with strong diagonal
# and some realistic misclassification patterns
confusion_data = np.array(
    [
        [45, 8, 3, 2],  # Cat: sometimes confused with Dog
        [6, 52, 4, 1],  # Dog: sometimes confused with Cat
        [2, 3, 38, 5],  # Bird: sometimes confused with Fish
        [1, 2, 7, 41],  # Fish: sometimes confused with Bird
    ]
)

# Build long-form data for geom_tile
rows = []
for i, true_label in enumerate(class_names):
    for j, pred_label in enumerate(class_names):
        count = confusion_data[i, j]
        rows.append(
            {"True Label": true_label, "Predicted Label": pred_label, "Count": count, "true_idx": i, "pred_idx": j}
        )

df = pd.DataFrame(rows)

# Calculate percentages for annotation (row normalization = recall)
total_per_row = confusion_data.sum(axis=1, keepdims=True)
percentages = (confusion_data / total_per_row * 100).astype(int)
df["Percentage"] = [percentages[r["true_idx"], r["pred_idx"]] for _, r in df.iterrows()]
df["Label"] = df.apply(lambda r: f"{r['Count']}\n({r['Percentage']}%)", axis=1)

# Set category order for proper matrix layout
df["True Label"] = pd.Categorical(df["True Label"], categories=class_names[::-1], ordered=True)
df["Predicted Label"] = pd.Categorical(df["Predicted Label"], categories=class_names, ordered=True)

# Determine text color based on count (theme-adaptive)
max_count = df["Count"].max()
if THEME == "light":
    df["text_color"] = df["Count"].apply(lambda c: "#1A1A17" if c > max_count * 0.4 else "#4A4A44")
else:
    df["text_color"] = df["Count"].apply(lambda c: "#F0EFE8" if c > max_count * 0.4 else "#B8B7B0")

# Color gradient for sequential data (Blues)
if THEME == "light":
    low_color = "#E7F0F9"
    high_color = "#08519C"
else:
    low_color = "#1F3D5C"
    high_color = "#74B3E5"

# Create confusion matrix heatmap
plot = (
    ggplot(df, aes(x="Predicted Label", y="True Label", fill="Count"))
    + geom_tile(color=INK_SOFT, size=1.5, tooltips="none")
    + geom_text(aes(label="Label", color="text_color"), size=14, fontface="bold")
    + scale_fill_gradient(low=low_color, high=high_color, name="Count")
    + labs(x="Predicted Label", y="True Label", title="confusion-matrix · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=28, face="bold", color=INK),
        axis_title=element_text(size=22, color=INK),
        axis_text=element_text(size=18, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        panel_grid=element_blank(),
    )
    + ggsize(1200, 1200)
    + coord_fixed()
)

# Save as PNG (scale 3x for 3600x3600 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
