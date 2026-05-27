""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - realistic multi-class classification results
np.random.seed(42)

# Class names for a sentiment analysis classifier
class_names = ["Negative", "Neutral", "Positive"]
n_classes = len(class_names)

# Create a realistic confusion matrix with:
# - Good diagonal (correct predictions)
# - Some confusion between adjacent sentiment classes
confusion_data = np.array(
    [
        [85, 12, 3],  # Negative: mostly correct, some confused with Neutral
        [8, 72, 20],  # Neutral: harder to classify, confused with both
        [4, 15, 81],  # Positive: mostly correct, some confused with Neutral
    ]
)

# Convert to long format for plotnine
rows = []
for i, true_class in enumerate(class_names):
    for j, pred_class in enumerate(class_names):
        rows.append({"True Label": true_class, "Predicted Label": pred_class, "Count": confusion_data[i, j]})

df = pd.DataFrame(rows)

# Set categorical order (reverse for y-axis to have first class at top)
df["True Label"] = pd.Categorical(df["True Label"], categories=class_names[::-1], ordered=True)
df["Predicted Label"] = pd.Categorical(df["Predicted Label"], categories=class_names, ordered=True)

# Add text color based on count (theme-adaptive: light text on dark cells, dark text on light cells)
threshold = (confusion_data.max() + confusion_data.min()) / 2
light_text = "#F0EFE8" if THEME == "light" else "#FAF8F1"
dark_text = "#1A1A17" if THEME == "light" else "#E8E8E0"
df["text_color"] = df["Count"].apply(lambda x: light_text if x >= threshold else dark_text)

# Create the confusion matrix heatmap
plot = (
    ggplot(df, aes(x="Predicted Label", y="True Label", fill="Count"))
    + geom_tile(color=INK_SOFT, size=2)
    + geom_text(aes(label="Count", color="text_color"), size=20, fontweight="bold", show_legend=False)
    + scale_fill_gradient(
        low="#e8f4f8" if THEME == "light" else "#2a3f4f",
        high="#08519c" if THEME == "light" else "#2ABCCD",
        name="Sample Count",
    )
    + scale_color_identity()
    + labs(title="confusion-matrix · plotnine · anyplot.ai", x="Predicted Label", y="True Label")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=22, weight="bold", color=INK),
        axis_text=element_text(size=18, color=INK_SOFT),
        plot_title=element_text(size=24, weight="bold", ha="center", color=INK),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=PAGE_BG if THEME == "light" else "#242420", color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save the plot
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
